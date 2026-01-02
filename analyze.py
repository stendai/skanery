#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
COMPANY ANALYZER - Raport Analityczny z Wykresami
================================================================================

Generuje HTML raport analityczny na podstawie danych finansowych.

UŻYCIE:
    python analyze.py           # Pyta o ticker
    python analyze.py GEN       # Bezpośrednio dla tickera

STRUKTURA FOLDERÓW:
    raporty/{TICKER}/
    ├── bilans_YYYY_Q.txt       # Bilans (z BiznesRadar)
    ├── rzis_YYYY_Q.txt         # RZiS (z BiznesRadar)
    ├── przeplywy_YYYY_Q.txt    # Cash Flow (z BiznesRadar)
    ├── {ticker}_YYYY_Q.pdf     # Raport kwartalny (ESPI)
    ├── *.pdf / *.docx          # Dodatkowe dokumenty
    └── raport_analityczny.html # WYJŚCIE

================================================================================
"""

import os
import sys
import re
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import base64
from io import BytesIO

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# Opcjonalne importy
try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


# =============================================================================
# KONFIGURACJA
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAPORTY_DIR = os.path.join(BASE_DIR, "raporty")

# Kolory dla wykresów
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#28A745',
    'danger': '#DC3545',
    'warning': '#FFC107',
    'info': '#17A2B8',
    'light': '#F8F9FA',
    'dark': '#343A40',
    'revenue': '#2E86AB',
    'profit': '#28A745',
    'loss': '#DC3545',
    'cash': '#17A2B8',
    'assets': '#6C757D',
}

# Progi dla alertów
ALERT_THRESHOLDS = {
    'revenue_growth_high': 20,      # >20% YoY = zielony alert
    'revenue_growth_low': -10,      # <-10% YoY = czerwony alert
    'profit_margin_high': 15,       # >15% = dobra marża
    'profit_margin_low': 0,         # <0% = strata
    'cash_months': 6,               # <6 miesięcy cash runway = alert
    'debt_ratio_high': 0.5,         # >50% zadłużenia = alert
    'current_ratio_low': 1.0,       # <1.0 płynność = alert
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FinancialData:
    """Przechowuje sparsowane dane finansowe"""
    ticker: str
    quarters: List[str] = field(default_factory=list)
    
    # RZiS
    revenue: Dict[str, float] = field(default_factory=dict)
    costs: Dict[str, float] = field(default_factory=dict)
    gross_profit: Dict[str, float] = field(default_factory=dict)
    ebit: Dict[str, float] = field(default_factory=dict)
    net_profit: Dict[str, float] = field(default_factory=dict)
    
    # Bilans
    total_assets: Dict[str, float] = field(default_factory=dict)
    fixed_assets: Dict[str, float] = field(default_factory=dict)
    current_assets: Dict[str, float] = field(default_factory=dict)
    cash: Dict[str, float] = field(default_factory=dict)
    inventory: Dict[str, float] = field(default_factory=dict)
    receivables: Dict[str, float] = field(default_factory=dict)
    equity: Dict[str, float] = field(default_factory=dict)
    long_term_debt: Dict[str, float] = field(default_factory=dict)
    short_term_debt: Dict[str, float] = field(default_factory=dict)
    
    # Przepływy
    ocf: Dict[str, float] = field(default_factory=dict)  # Operating Cash Flow
    icf: Dict[str, float] = field(default_factory=dict)  # Investing Cash Flow
    fcf: Dict[str, float] = field(default_factory=dict)  # Financing Cash Flow
    capex: Dict[str, float] = field(default_factory=dict)
    depreciation: Dict[str, float] = field(default_factory=dict)
    
    # Metadane
    report_date: Optional[str] = None
    company_name: Optional[str] = None
    employees: Optional[float] = None
    management_comment: Optional[str] = None
    shareholders: List[Dict] = field(default_factory=list)


@dataclass
class ContextData:
    """Przechowuje kontekst z pliku _kontekst.txt"""
    employees: Optional[float] = None
    shareholders: List[Dict] = field(default_factory=list)
    management_comment: Optional[str] = None
    innovations: Optional[str] = None
    risks: Optional[str] = None
    raw_sections: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert/obserwacja z analizy"""
    type: str  # 'success', 'warning', 'danger', 'info'
    title: str
    message: str
    value: Optional[str] = None


@dataclass
class Attachment:
    """Dodatkowy plik załączony do raportu"""
    filename: str
    filepath: str
    filetype: str  # 'pdf', 'docx', 'other'
    description: Optional[str] = None


# =============================================================================
# PARSERY DANYCH
# =============================================================================

def parse_number(val: str) -> float:
    """Konwertuje string na float, obsługuje polskie formatowanie"""
    if pd.isna(val) or val == '' or val == '-':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # Usuń spacje, zamień przecinki
    cleaned = str(val).replace(' ', '').replace('\xa0', '').replace(',', '.')
    # Obsłuż ujemne z nawiasami
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]
    try:
        return float(cleaned)
    except:
        return 0.0


def parse_quarter(q_str: str) -> Tuple[int, int]:
    """Parsuje '2024/Q3 (wrz 24)' -> (2024, 3)"""
    match = re.search(r'(\d{4})/Q(\d)', q_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def quarter_to_date(year: int, quarter: int) -> datetime:
    """Konwertuje rok/kwartał na datę (koniec kwartału)"""
    month = quarter * 3
    return datetime(year, month, 28)


def parse_biznesradar_file(filepath: str) -> pd.DataFrame:
    """Parsuje plik TXT z BiznesRadar (tab-separated)"""
    if not os.path.exists(filepath):
        return pd.DataFrame()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normalizuj znaki końca linii
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = content.split('\n')
    
    # Znajdź nagłówek (linia z kwartałami)
    header_idx = None
    for i, line in enumerate(lines):
        if 'Q1' in line or 'Q2' in line or 'Q3' in line or 'Q4' in line:
            header_idx = i
            break
    
    if header_idx is None:
        return pd.DataFrame()
    
    # Parsuj nagłówki (kwartały) - obsłuż podwójne taby
    header_line = lines[header_idx]
    # Zamień podwójne taby na pojedyncze
    while '\t\t' in header_line:
        header_line = header_line.replace('\t\t', '\t')
    
    headers = header_line.strip().split('\t')
    headers = [h.strip() for h in headers if h.strip()]
    
    # Filtruj tylko kwartały
    quarters = [h for h in headers if 'Q1' in h or 'Q2' in h or 'Q3' in h or 'Q4' in h]
    
    # Parsuj dane
    data = {}
    for line in lines[header_idx + 1:]:
        if not line.strip():
            continue
        
        # Zamień podwójne taby
        while '\t\t' in line:
            line = line.replace('\t\t', '\t')
        
        parts = line.strip().split('\t')
        if len(parts) < 2:
            continue
        
        row_name = parts[0].strip()
        if not row_name or row_name == 'Data publikacji':
            continue
        
        values = []
        for p in parts[1:]:
            values.append(parse_number(p))
        
        # Dopasuj długość do liczby kwartałów
        while len(values) < len(quarters):
            values.append(0.0)
        
        data[row_name] = values[:len(quarters)]
    
    # Stwórz DataFrame z kwartałami jako kolumnami
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data, index=quarters)
    return df.T


def load_financial_data(ticker: str, folder_path: str) -> FinancialData:
    """Wczytuje wszystkie dane finansowe dla spółki"""
    data = FinancialData(ticker=ticker)
    
    # Znajdź pliki (z tickerem na początku nazwy)
    ticker_lower = ticker.lower()
    bilans_files = glob.glob(os.path.join(folder_path, f'{ticker_lower}_bilans*.txt'))
    rzis_files = glob.glob(os.path.join(folder_path, f'{ticker_lower}_rzis*.txt'))
    przeplywy_files = glob.glob(os.path.join(folder_path, f'{ticker_lower}_przeplywy*.txt'))
    
    # Parsuj RZiS
    if rzis_files:
        df_rzis = parse_biznesradar_file(rzis_files[0])
        if not df_rzis.empty:
            data.quarters = list(df_rzis.columns)
            
            row_mappings = {
                'Przychody ze sprzedaży': 'revenue',
                'Przychody ze sprzedaży produktów': 'revenue',
                'Techniczny koszt wytworzenia produkcji sprzedanej': 'costs',
                'Koszty działalności operacyjnej': 'costs',
                'Zysk ze sprzedaży': 'gross_profit',
                'Zysk operacyjny (EBIT)': 'ebit',
                'EBIT': 'ebit',
                'Zysk netto': 'net_profit',
                'Zysk netto akcjonariuszy jednostki dominującej': 'net_profit',
            }
            
            for row_name, attr_name in row_mappings.items():
                if row_name in df_rzis.index:
                    for q in data.quarters:
                        if q in df_rzis.columns:
                            getattr(data, attr_name)[q] = df_rzis.loc[row_name, q]
    
    # Parsuj Bilans
    if bilans_files:
        df_bilans = parse_biznesradar_file(bilans_files[0])
        if not df_bilans.empty:
            if not data.quarters:
                data.quarters = list(df_bilans.columns)
            
            row_mappings = {
                'Aktywa razem': 'total_assets',
                'Pasywa razem': 'total_assets',
                'Aktywa trwałe': 'fixed_assets',
                'Aktywa obrotowe': 'current_assets',
                'Środki pieniężne i inne aktywa pieniężne': 'cash',
                'Inwestycje krótkoterminowe': 'cash',
                'Zapasy': 'inventory',
                'Należności krótkoterminowe': 'receivables',
                'Kapitał własny akcjonariuszy jednostki dominującej': 'equity',
                'Kapitał własny': 'equity',
                'Zobowiązania długoterminowe': 'long_term_debt',
                'Zobowiązania krótkoterminowe': 'short_term_debt',
            }
            
            for row_name, attr_name in row_mappings.items():
                if row_name in df_bilans.index:
                    for q in df_bilans.columns:
                        if q not in getattr(data, attr_name):
                            getattr(data, attr_name)[q] = df_bilans.loc[row_name, q]
    
    # Parsuj Przepływy
    if przeplywy_files:
        df_cf = parse_biznesradar_file(przeplywy_files[0])
        if not df_cf.empty:
            row_mappings = {
                'Przepływy pieniężne z działalności operacyjnej': 'ocf',
                'Przepływy pieniężne z działalności inwestycyjnej': 'icf',
                'Przepływy pieniężne z działalności finansowej': 'fcf',
                'CAPEX (niematerialne i rzeczowe)': 'capex',
                'Amortyzacja': 'depreciation',
            }
            
            for row_name, attr_name in row_mappings.items():
                if row_name in df_cf.index:
                    for q in df_cf.columns:
                        getattr(data, attr_name)[q] = df_cf.loc[row_name, q]
    
    return data


def parse_quarterly_pdf(filepath: str) -> Dict[str, Any]:
    """Parsuje raport kwartalny PDF (podstawowe info)"""
    result = {
        'report_date': None,
        'employees': None,
        'management_comment': None,
        'shareholders': [],
    }
    
    if not HAS_PYPDF or not os.path.exists(filepath):
        return result
    
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages[:5]:  # Pierwsze 5 stron
                text += page.extract_text() or ''
        
        # Szukaj daty raportu
        date_match = re.search(r'Warszawa[,\s]+(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})', text)
        if date_match:
            result['report_date'] = date_match.group(1)
        
        # Szukaj zatrudnienia
        emp_match = re.search(r'zatrudni[^\d]*(\d+[,.]?\d*)', text, re.IGNORECASE)
        if emp_match:
            result['employees'] = parse_number(emp_match.group(1))
        
        # Szukaj komentarza zarządu (fragment)
        if 'Komentarz Zarządu' in text:
            start = text.find('Komentarz Zarządu')
            end = min(start + 1500, len(text))
            result['management_comment'] = text[start:end].strip()
        
    except Exception as e:
        print(f"  ⚠️ Błąd parsowania PDF: {e}")
    
    return result


def parse_context_file(filepath: str) -> Optional[ContextData]:
    """Parsuje plik _kontekst.txt z ręcznie przygotowanym kontekstem"""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  ⚠️ Błąd czytania kontekstu: {e}")
        return None
    
    context = ContextData()
    current_section = None
    section_content = []
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Pomiń komentarze
        if line.startswith('#'):
            continue
        
        # Wykryj sekcję [NAZWA]
        if line.startswith('[') and line.endswith(']'):
            # Zapisz poprzednią sekcję
            if current_section and section_content:
                context.raw_sections[current_section] = '\n'.join(section_content)
            
            current_section = line[1:-1].upper()
            section_content = []
            continue
        
        # Dodaj treść do bieżącej sekcji
        if current_section and line:
            section_content.append(line)
    
    # Zapisz ostatnią sekcję
    if current_section and section_content:
        context.raw_sections[current_section] = '\n'.join(section_content)
    
    # Parsuj znane sekcje
    
    # Zatrudnienie
    if 'ZATRUDNIENIE' in context.raw_sections:
        fte_match = re.search(r'FTE:\s*(\d+[,.]?\d*)', context.raw_sections['ZATRUDNIENIE'])
        if fte_match:
            context.employees = parse_number(fte_match.group(1))
    
    # Akcjonariat
    if 'AKCJONARIAT' in context.raw_sections:
        shareholders = []
        for line in context.raw_sections['AKCJONARIAT'].split('\n'):
            # Format: "Nazwa: XX.XX% kapitału / YY.YY% głosów"
            match = re.match(r'(.+?):\s*(\d+[,.]?\d*)%\s*kapitału\s*/\s*(\d+[,.]?\d*)%\s*głosów', line)
            if match:
                shareholders.append({
                    'name': match.group(1).strip(),
                    'capital': parse_number(match.group(2)),
                    'votes': parse_number(match.group(3))
                })
            else:
                # Prostszy format: "Nazwa: XX.XX%"
                match2 = re.match(r'(.+?):\s*(\d+[,.]?\d*)%', line)
                if match2:
                    shareholders.append({
                        'name': match2.group(1).strip(),
                        'capital': parse_number(match2.group(2)),
                        'votes': None
                    })
        context.shareholders = shareholders
    
    # Komentarz zarządu
    if 'KOMENTARZ ZARZĄDU' in context.raw_sections:
        context.management_comment = context.raw_sections['KOMENTARZ ZARZĄDU']
    elif 'KOMENTARZ' in context.raw_sections:
        context.management_comment = context.raw_sections['KOMENTARZ']
    
    # Innowacje / R&D
    if 'INNOWACJE / R&D' in context.raw_sections:
        context.innovations = context.raw_sections['INNOWACJE / R&D']
    elif 'INNOWACJE' in context.raw_sections:
        context.innovations = context.raw_sections['INNOWACJE']
    elif 'R&D' in context.raw_sections:
        context.innovations = context.raw_sections['R&D']
    
    # Ryzyka
    if 'RYZYKA / UWAGI' in context.raw_sections:
        context.risks = context.raw_sections['RYZYKA / UWAGI']
    elif 'RYZYKA' in context.raw_sections:
        context.risks = context.raw_sections['RYZYKA']
    elif 'UWAGI' in context.raw_sections:
        context.risks = context.raw_sections['UWAGI']
    
    return context


# =============================================================================
# ANALIZA I METRYKI
# =============================================================================

def calculate_metrics(data: FinancialData) -> Dict[str, Any]:
    """Oblicza kluczowe metryki finansowe"""
    metrics = {}
    
    if not data.quarters:
        return metrics
    
    # Ostatni kwartał
    latest = data.quarters[-1]
    prev_year = None
    
    # Znajdź kwartał rok temu
    year, q = parse_quarter(latest)
    for quarter in data.quarters:
        y, qq = parse_quarter(quarter)
        if y == year - 1 and qq == q:
            prev_year = quarter
            break
    
    # === Przychody ===
    if latest in data.revenue:
        metrics['revenue_latest'] = data.revenue[latest]
        
        if prev_year and prev_year in data.revenue and data.revenue[prev_year] > 0:
            metrics['revenue_yoy'] = ((data.revenue[latest] / data.revenue[prev_year]) - 1) * 100
        
        # TTM (trailing 12 months)
        ttm_quarters = data.quarters[-4:] if len(data.quarters) >= 4 else data.quarters
        metrics['revenue_ttm'] = sum(data.revenue.get(q, 0) for q in ttm_quarters)
    
    # === Zysk netto ===
    if latest in data.net_profit:
        metrics['net_profit_latest'] = data.net_profit[latest]
        
        if prev_year and prev_year in data.net_profit:
            if data.net_profit[prev_year] > 0:
                metrics['net_profit_yoy'] = ((data.net_profit[latest] / data.net_profit[prev_year]) - 1) * 100
            elif data.net_profit[prev_year] < 0 and data.net_profit[latest] > 0:
                metrics['net_profit_yoy'] = 999  # Turnaround
        
        # TTM
        ttm_quarters = data.quarters[-4:] if len(data.quarters) >= 4 else data.quarters
        metrics['net_profit_ttm'] = sum(data.net_profit.get(q, 0) for q in ttm_quarters)
    
    # === Marże ===
    if metrics.get('revenue_latest', 0) > 0:
        if latest in data.ebit:
            metrics['ebit_margin'] = (data.ebit[latest] / data.revenue[latest]) * 100
        if latest in data.net_profit:
            metrics['net_margin'] = (data.net_profit[latest] / data.revenue[latest]) * 100
    
    # === EBITDA ===
    if latest in data.ebit and latest in data.depreciation:
        metrics['ebitda_latest'] = data.ebit[latest] + data.depreciation[latest]
    
    # === Bilans ===
    if latest in data.cash:
        metrics['cash_latest'] = data.cash[latest]
        
        if prev_year and prev_year in data.cash and data.cash[prev_year] > 0:
            metrics['cash_yoy'] = ((data.cash[latest] / data.cash[prev_year]) - 1) * 100
    
    if latest in data.equity:
        metrics['equity_latest'] = data.equity[latest]
    
    if latest in data.total_assets:
        metrics['total_assets_latest'] = data.total_assets[latest]
    
    # === Wskaźniki ===
    # ROE
    if metrics.get('net_profit_ttm') and metrics.get('equity_latest', 0) > 0:
        metrics['roe'] = (metrics['net_profit_ttm'] / metrics['equity_latest']) * 100
    
    # ROA
    if metrics.get('net_profit_ttm') and metrics.get('total_assets_latest', 0) > 0:
        metrics['roa'] = (metrics['net_profit_ttm'] / metrics['total_assets_latest']) * 100
    
    # Debt ratio
    total_debt = data.long_term_debt.get(latest, 0) + data.short_term_debt.get(latest, 0)
    if metrics.get('total_assets_latest', 0) > 0:
        metrics['debt_ratio'] = total_debt / metrics['total_assets_latest']
    
    # Current ratio
    if data.short_term_debt.get(latest, 0) > 0:
        metrics['current_ratio'] = data.current_assets.get(latest, 0) / data.short_term_debt[latest]
    
    # Cash runway (miesiące)
    if metrics.get('cash_latest', 0) > 0 and latest in data.costs:
        monthly_burn = data.costs[latest] / 3  # Kwartał = 3 miesiące
        if monthly_burn > 0:
            metrics['cash_runway_months'] = metrics['cash_latest'] / monthly_burn
    
    # === Cash Flow ===
    if latest in data.ocf:
        metrics['ocf_latest'] = data.ocf[latest]
    
    # Free Cash Flow = OCF - CAPEX
    if latest in data.ocf and latest in data.capex:
        metrics['fcf_latest'] = data.ocf[latest] - data.capex[latest]
    
    return metrics


def generate_alerts(data: FinancialData, metrics: Dict[str, Any]) -> List[Alert]:
    """Generuje alerty na podstawie danych"""
    alerts = []
    
    # === Revenue Growth ===
    if 'revenue_yoy' in metrics:
        yoy = metrics['revenue_yoy']
        if yoy > ALERT_THRESHOLDS['revenue_growth_high']:
            alerts.append(Alert(
                type='success',
                title='📈 Silny wzrost przychodów',
                message=f'Przychody wzrosły o {yoy:.1f}% r/r - znacząco powyżej rynku',
                value=f'+{yoy:.1f}%'
            ))
        elif yoy < ALERT_THRESHOLDS['revenue_growth_low']:
            alerts.append(Alert(
                type='danger',
                title='📉 Spadek przychodów',
                message=f'Przychody spadły o {abs(yoy):.1f}% r/r - wymaga uwagi',
                value=f'{yoy:.1f}%'
            ))
    
    # === Profitability ===
    if 'net_margin' in metrics:
        margin = metrics['net_margin']
        if margin > ALERT_THRESHOLDS['profit_margin_high']:
            alerts.append(Alert(
                type='success',
                title='💰 Wysoka rentowność',
                message=f'Marża netto {margin:.1f}% - solidna profitabilność',
                value=f'{margin:.1f}%'
            ))
        elif margin < ALERT_THRESHOLDS['profit_margin_low']:
            alerts.append(Alert(
                type='danger',
                title='⚠️ Strata operacyjna',
                message=f'Marża netto ujemna ({margin:.1f}%) - spółka traci pieniądze',
                value=f'{margin:.1f}%'
            ))
    
    # === Turnaround ===
    if metrics.get('net_profit_yoy', 0) == 999:
        alerts.append(Alert(
            type='success',
            title='🔄 Turnaround',
            message='Spółka wyszła ze straty na zysk r/r - pozytywny sygnał',
            value='Zysk!'
        ))
    
    # === Cash Position ===
    if 'cash_yoy' in metrics:
        cash_yoy = metrics['cash_yoy']
        if cash_yoy > 50:
            alerts.append(Alert(
                type='success',
                title='💵 Silna pozycja gotówkowa',
                message=f'Gotówka wzrosła o {cash_yoy:.1f}% r/r',
                value=f'+{cash_yoy:.1f}%'
            ))
    
    if 'cash_runway_months' in metrics:
        runway = metrics['cash_runway_months']
        if runway < ALERT_THRESHOLDS['cash_months']:
            alerts.append(Alert(
                type='warning',
                title='⏰ Niski runway',
                message=f'Gotówka wystarczy na ~{runway:.0f} miesięcy przy obecnym burn rate',
                value=f'{runway:.0f} mies.'
            ))
    
    # === Debt ===
    if 'debt_ratio' in metrics:
        debt = metrics['debt_ratio']
        if debt > ALERT_THRESHOLDS['debt_ratio_high']:
            alerts.append(Alert(
                type='warning',
                title='📊 Wysokie zadłużenie',
                message=f'Wskaźnik zadłużenia {debt*100:.1f}% - powyżej 50%',
                value=f'{debt*100:.1f}%'
            ))
        elif debt < 0.1:
            alerts.append(Alert(
                type='success',
                title='✅ Niskie zadłużenie',
                message=f'Wskaźnik zadłużenia tylko {debt*100:.1f}% - bezpieczny bilans',
                value=f'{debt*100:.1f}%'
            ))
    
    # === Liquidity ===
    if 'current_ratio' in metrics:
        cr = metrics['current_ratio']
        if cr < ALERT_THRESHOLDS['current_ratio_low']:
            alerts.append(Alert(
                type='danger',
                title='💧 Niska płynność',
                message=f'Current ratio {cr:.2f} - poniżej 1.0, ryzyko płynności',
                value=f'{cr:.2f}'
            ))
        elif cr > 3:
            alerts.append(Alert(
                type='info',
                title='💧 Wysoka płynność',
                message=f'Current ratio {cr:.2f} - bardzo dobra płynność',
                value=f'{cr:.2f}'
            ))
    
    # === Cash Flow ===
    if 'fcf_latest' in metrics:
        fcf = metrics['fcf_latest']
        if fcf > 0:
            alerts.append(Alert(
                type='success',
                title='💸 Pozytywny Free Cash Flow',
                message=f'FCF = {fcf:,.0f} tys. PLN - spółka generuje gotówkę',
                value=f'{fcf:,.0f}'
            ))
    
    # === ROE ===
    if 'roe' in metrics:
        roe = metrics['roe']
        if roe > 20:
            alerts.append(Alert(
                type='success',
                title='📊 Wysokie ROE',
                message=f'ROE = {roe:.1f}% - efektywne wykorzystanie kapitału',
                value=f'{roe:.1f}%'
            ))
    
    return alerts


# =============================================================================
# WYKRESY
# =============================================================================

def fig_to_base64(fig) -> str:
    """Konwertuje matplotlib figure do base64 string"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str


def create_revenue_chart(data: FinancialData) -> str:
    """Tworzy wykres przychodów i zysku"""
    if not data.revenue:
        return ""
    
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    quarters = list(data.revenue.keys())[-12:]  # Ostatnie 12 kwartałów
    revenues = [data.revenue.get(q, 0) for q in quarters]
    profits = [data.net_profit.get(q, 0) for q in quarters]
    
    x = range(len(quarters))
    
    # Bars for revenue
    bars = ax1.bar(x, revenues, color=COLORS['revenue'], alpha=0.7, label='Przychody')
    ax1.set_ylabel('Przychody (tys. PLN)', color=COLORS['revenue'])
    ax1.tick_params(axis='y', labelcolor=COLORS['revenue'])
    
    # Line for profit
    ax2 = ax1.twinx()
    line = ax2.plot(x, profits, color=COLORS['profit'], linewidth=2, marker='o', 
                    markersize=6, label='Zysk netto')
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Zysk netto (tys. PLN)', color=COLORS['profit'])
    ax2.tick_params(axis='y', labelcolor=COLORS['profit'])
    
    # Koloruj zysk/stratę
    for i, p in enumerate(profits):
        color = COLORS['success'] if p >= 0 else COLORS['danger']
        ax2.plot(i, p, 'o', color=color, markersize=8, zorder=5)
    
    # Labels
    ax1.set_xticks(x)
    labels = [q.split('(')[0].strip() for q in quarters]
    ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    
    ax1.set_title(f'{data.ticker} - Przychody i Zysk Netto', fontsize=14, fontweight='bold')
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    return fig_to_base64(fig)


def create_cash_chart(data: FinancialData) -> str:
    """Tworzy wykres pozycji gotówkowej"""
    if not data.cash:
        return ""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    quarters = list(data.cash.keys())[-12:]
    cash = [data.cash.get(q, 0) for q in quarters]
    
    x = range(len(quarters))
    
    # Gradient fill
    ax.fill_between(x, cash, alpha=0.3, color=COLORS['cash'])
    ax.plot(x, cash, color=COLORS['cash'], linewidth=2, marker='o', markersize=6)
    
    # Annotate last value
    if cash:
        ax.annotate(f'{cash[-1]:,.0f}', xy=(len(cash)-1, cash[-1]), 
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, fontweight='bold', color=COLORS['cash'])
    
    ax.set_xticks(x)
    labels = [q.split('(')[0].strip() for q in quarters]
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    
    ax.set_ylabel('Gotówka (tys. PLN)')
    ax.set_title(f'{data.ticker} - Pozycja Gotówkowa', fontsize=14, fontweight='bold')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    plt.tight_layout()
    return fig_to_base64(fig)


def create_margins_chart(data: FinancialData) -> str:
    """Tworzy wykres marż"""
    if not data.revenue or not data.ebit:
        return ""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    quarters = list(data.revenue.keys())[-12:]
    
    ebit_margin = []
    net_margin = []
    
    for q in quarters:
        rev = data.revenue.get(q, 0)
        if rev > 0:
            ebit_margin.append((data.ebit.get(q, 0) / rev) * 100)
            net_margin.append((data.net_profit.get(q, 0) / rev) * 100)
        else:
            ebit_margin.append(0)
            net_margin.append(0)
    
    x = range(len(quarters))
    
    ax.plot(x, ebit_margin, color=COLORS['primary'], linewidth=2, marker='s', 
            markersize=6, label='Marża EBIT')
    ax.plot(x, net_margin, color=COLORS['secondary'], linewidth=2, marker='o', 
            markersize=6, label='Marża netto')
    
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.fill_between(x, 0, net_margin, alpha=0.2, color=COLORS['secondary'])
    
    ax.set_xticks(x)
    labels = [q.split('(')[0].strip() for q in quarters]
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    
    ax.set_ylabel('Marża (%)')
    ax.set_title(f'{data.ticker} - Marże', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.0f}%'))
    
    plt.tight_layout()
    return fig_to_base64(fig)


def create_cashflow_chart(data: FinancialData) -> str:
    """Tworzy wykres przepływów pieniężnych"""
    if not data.ocf:
        return ""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    quarters = list(data.ocf.keys())[-8:]  # Ostatnie 8 kwartałów
    
    ocf = [data.ocf.get(q, 0) for q in quarters]
    icf = [data.icf.get(q, 0) for q in quarters]
    fcf = [data.fcf.get(q, 0) for q in quarters]
    
    x = range(len(quarters))
    width = 0.25
    
    ax.bar([i - width for i in x], ocf, width, label='Operacyjne', color=COLORS['success'], alpha=0.8)
    ax.bar(x, icf, width, label='Inwestycyjne', color=COLORS['warning'], alpha=0.8)
    ax.bar([i + width for i in x], fcf, width, label='Finansowe', color=COLORS['info'], alpha=0.8)
    
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    ax.set_xticks(x)
    labels = [q.split('(')[0].strip() for q in quarters]
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    
    ax.set_ylabel('Przepływy (tys. PLN)')
    ax.set_title(f'{data.ticker} - Przepływy Pieniężne', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    
    plt.tight_layout()
    return fig_to_base64(fig)


def create_seasonality_chart(data: FinancialData) -> str:
    """Tworzy wykres sezonowości (Q1 vs Q2 vs Q3 vs Q4)"""
    if not data.revenue:
        return ""
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Grupuj po kwartałach
    q1, q2, q3, q4 = [], [], [], []
    
    for q, val in data.revenue.items():
        _, quarter = parse_quarter(q)
        if quarter == 1:
            q1.append(val)
        elif quarter == 2:
            q2.append(val)
        elif quarter == 3:
            q3.append(val)
        elif quarter == 4:
            q4.append(val)
    
    quarters_data = [q1, q2, q3, q4]
    quarters_labels = ['Q1', 'Q2', 'Q3', 'Q4']
    
    # Box plot
    bp = ax.boxplot(quarters_data, labels=quarters_labels, patch_artist=True)
    
    colors = [COLORS['info'], COLORS['warning'], COLORS['success'], COLORS['primary']]
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    # Średnie
    means = [sum(q)/len(q) if q else 0 for q in quarters_data]
    ax.scatter(range(1, 5), means, color='red', s=100, zorder=5, label='Średnia')
    
    ax.set_ylabel('Przychody (tys. PLN)')
    ax.set_title(f'{data.ticker} - Sezonowość Przychodów', fontsize=14, fontweight='bold')
    ax.legend()
    
    plt.tight_layout()
    return fig_to_base64(fig)


# =============================================================================
# GENEROWANIE HTML
# =============================================================================

def find_attachments(folder_path: str, ticker: str) -> List[Attachment]:
    """Znajduje dodatkowe pliki (PDF, DOCX) w folderze"""
    attachments = []
    
    # Pliki do pominięcia (dane źródłowe)
    skip_patterns = ['bilans', 'rzis', 'przeplywy', 'raport_analityczny']
    
    for ext in ['*.pdf', '*.PDF', '*.docx', '*.DOCX', '*.doc', '*.DOC']:
        for filepath in glob.glob(os.path.join(folder_path, ext)):
            filename = os.path.basename(filepath)
            filename_lower = filename.lower()
            
            # Pomiń pliki z danymi źródłowymi
            if any(skip in filename_lower for skip in skip_patterns):
                continue
            
            # Sprawdź czy to główny raport kwartalny (ticker_YYYY_Q.pdf)
            # np. gen_2025_3.pdf - to raport kwartalny, nie załącznik
            is_quarterly_report = False
            if filename_lower.startswith(ticker.lower()):
                # Sprawdź czy pasuje do wzorca raportu kwartalnego
                if re.match(rf'{ticker.lower()}_\d{{4}}_\d\.pdf', filename_lower):
                    is_quarterly_report = True
            
            filetype = 'pdf' if filepath.lower().endswith('.pdf') else 'docx'
            
            # Opis z nazwy pliku
            desc = filename.replace('_', ' ').replace('-', ' ')
            desc = re.sub(r'\.(pdf|docx|doc)$', '', desc, flags=re.IGNORECASE)
            
            # Jeśli to raport kwartalny, dodaj z odpowiednim opisem
            if is_quarterly_report:
                desc = f"📋 Raport Kwartalny - {desc}"
            
            attachments.append(Attachment(
                filename=filename,
                filepath=filepath,
                filetype=filetype,
                description=desc
            ))
    
    return attachments


def generate_html_report(data: FinancialData, metrics: Dict[str, Any], 
                         alerts: List[Alert], attachments: List[Attachment],
                         charts: Dict[str, str], context: Optional[ContextData] = None) -> str:
    """Generuje kompletny raport HTML"""
    
    # Timestamp
    generated = datetime.now().strftime('%Y-%m-%d %H:%M')
    latest_q = data.quarters[-1] if data.quarters else 'N/A'
    
    # === HTML START ===
    html = f'''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.ticker} - Raport Analityczny</title>
    <style>
        :root {{
            --primary: #2E86AB;
            --secondary: #A23B72;
            --success: #28A745;
            --danger: #DC3545;
            --warning: #FFC107;
            --info: #17A2B8;
            --light: #F8F9FA;
            --dark: #343A40;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 30px;
        }}
        
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        header .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}
        
        .meta {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
            font-size: 0.9rem;
            opacity: 0.85;
        }}
        
        main {{
            padding: 30px;
        }}
        
        section {{
            margin-bottom: 40px;
        }}
        
        h2 {{
            color: var(--primary);
            font-size: 1.5rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--light);
        }}
        
        h3 {{
            color: var(--dark);
            font-size: 1.2rem;
            margin: 20px 0 15px;
        }}
        
        /* KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: var(--light);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid var(--primary);
        }}
        
        .kpi-card.success {{ border-left-color: var(--success); }}
        .kpi-card.danger {{ border-left-color: var(--danger); }}
        .kpi-card.warning {{ border-left-color: var(--warning); }}
        
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--dark);
        }}
        
        .kpi-label {{
            font-size: 0.9rem;
            color: #666;
            margin-top: 5px;
        }}
        
        .kpi-change {{
            font-size: 0.85rem;
            margin-top: 5px;
        }}
        
        .kpi-change.positive {{ color: var(--success); }}
        .kpi-change.negative {{ color: var(--danger); }}
        
        /* Alerts */
        .alerts {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .alert {{
            padding: 15px 20px;
            border-radius: 8px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        
        .alert.success {{ background: #d4edda; border-left: 4px solid var(--success); }}
        .alert.warning {{ background: #fff3cd; border-left: 4px solid var(--warning); }}
        .alert.danger {{ background: #f8d7da; border-left: 4px solid var(--danger); }}
        .alert.info {{ background: #d1ecf1; border-left: 4px solid var(--info); }}
        
        .alert-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .alert-value {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-left: auto;
            white-space: nowrap;
        }}
        
        /* Charts */
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .chart-container img {{
            width: 100%;
            height: auto;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.9rem;
        }}
        
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #eee;
        }}
        
        th {{
            background: var(--light);
            font-weight: 600;
            color: var(--dark);
        }}
        
        td:first-child, th:first-child {{
            text-align: left;
        }}
        
        tr:hover {{
            background: #fafafa;
        }}
        
        .positive {{ color: var(--success); }}
        .negative {{ color: var(--danger); }}
        
        /* Context sections */
        #context {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        
        .context-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .context-item h3 {{
            margin: 0 0 10px 0;
            color: var(--primary);
            font-size: 1.1rem;
        }}
        
        .context-item p {{
            margin: 0;
            line-height: 1.6;
        }}
        
        .context-item.risks {{
            border-left: 4px solid var(--warning);
        }}
        
        .shareholders-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        .shareholders-table th,
        .shareholders-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .shareholders-table th {{
            background: var(--light);
            font-weight: 600;
        }}
        
        .shareholders-table tr:hover {{
            background: #f8f9fa;
        }}
        
        /* Attachments */
        .attachments-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .attachment {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 15px 20px;
            background: var(--light);
            border-radius: 8px;
            text-decoration: none;
            color: var(--dark);
            transition: all 0.2s;
        }}
        
        .attachment:hover {{
            background: var(--primary);
            color: white;
            transform: translateY(-2px);
        }}
        
        .attachment-icon {{
            font-size: 1.5rem;
        }}
        
        footer {{
            background: var(--dark);
            color: white;
            padding: 20px 30px;
            text-align: center;
            font-size: 0.85rem;
        }}
        
        @media (max-width: 768px) {{
            header h1 {{ font-size: 1.8rem; }}
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .meta {{ flex-direction: column; gap: 5px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 {data.ticker}</h1>
            <div class="subtitle">{data.company_name or 'Raport Analityczny'}</div>
            <div class="meta">
                <span>📅 Ostatni kwartał: {latest_q}</span>
                <span>🕐 Wygenerowano: {generated}</span>
                {f'<span>👥 Zatrudnienie: {data.employees:.0f} FTE</span>' if data.employees else ''}
            </div>
        </header>
        
        <main>
'''
    
    # === KPI CARDS ===
    html += '''
            <section id="kpi">
                <h2>📈 Kluczowe Wskaźniki</h2>
                <div class="kpi-grid">
'''
    
    # Revenue
    if 'revenue_latest' in metrics:
        yoy_class = 'positive' if metrics.get('revenue_yoy', 0) > 0 else 'negative'
        yoy_sign = '+' if metrics.get('revenue_yoy', 0) > 0 else ''
        card_class = 'success' if metrics.get('revenue_yoy', 0) > 20 else ''
        html += f'''
                    <div class="kpi-card {card_class}">
                        <div class="kpi-value">{metrics['revenue_latest']:,.0f}</div>
                        <div class="kpi-label">Przychody Q (tys. PLN)</div>
                        {'<div class="kpi-change ' + yoy_class + '">' + yoy_sign + f"{metrics['revenue_yoy']:.1f}% r/r</div>" if 'revenue_yoy' in metrics else ''}
                    </div>
'''
    
    # Net Profit
    if 'net_profit_latest' in metrics:
        card_class = 'success' if metrics['net_profit_latest'] > 0 else 'danger'
        html += f'''
                    <div class="kpi-card {card_class}">
                        <div class="kpi-value">{metrics['net_profit_latest']:,.0f}</div>
                        <div class="kpi-label">Zysk netto Q (tys. PLN)</div>
                    </div>
'''
    
    # Cash
    if 'cash_latest' in metrics:
        yoy_class = 'positive' if metrics.get('cash_yoy', 0) > 0 else 'negative'
        yoy_sign = '+' if metrics.get('cash_yoy', 0) > 0 else ''
        html += f'''
                    <div class="kpi-card">
                        <div class="kpi-value">{metrics['cash_latest']:,.0f}</div>
                        <div class="kpi-label">Gotówka (tys. PLN)</div>
                        {'<div class="kpi-change ' + yoy_class + '">' + yoy_sign + f"{metrics['cash_yoy']:.1f}% r/r</div>" if 'cash_yoy' in metrics else ''}
                    </div>
'''
    
    # Net Margin
    if 'net_margin' in metrics:
        card_class = 'success' if metrics['net_margin'] > 10 else ('danger' if metrics['net_margin'] < 0 else '')
        html += f'''
                    <div class="kpi-card {card_class}">
                        <div class="kpi-value">{metrics['net_margin']:.1f}%</div>
                        <div class="kpi-label">Marża netto</div>
                    </div>
'''
    
    # ROE
    if 'roe' in metrics:
        card_class = 'success' if metrics['roe'] > 15 else ''
        html += f'''
                    <div class="kpi-card {card_class}">
                        <div class="kpi-value">{metrics['roe']:.1f}%</div>
                        <div class="kpi-label">ROE (TTM)</div>
                    </div>
'''
    
    # Current Ratio
    if 'current_ratio' in metrics:
        card_class = 'danger' if metrics['current_ratio'] < 1 else ('success' if metrics['current_ratio'] > 2 else '')
        html += f'''
                    <div class="kpi-card {card_class}">
                        <div class="kpi-value">{metrics['current_ratio']:.2f}</div>
                        <div class="kpi-label">Current Ratio</div>
                    </div>
'''
    
    html += '''
                </div>
            </section>
'''
    
    # === ALERTS ===
    if alerts:
        html += '''
            <section id="alerts">
                <h2>🚨 Alerty i Obserwacje</h2>
                <div class="alerts">
'''
        for alert in alerts:
            html += f'''
                    <div class="alert {alert.type}">
                        <div>
                            <div class="alert-title">{alert.title}</div>
                            <div>{alert.message}</div>
                        </div>
                        {f'<div class="alert-value">{alert.value}</div>' if alert.value else ''}
                    </div>
'''
        html += '''
                </div>
            </section>
'''
    
    # === CHARTS ===
    html += '''
            <section id="charts">
                <h2>📊 Wykresy</h2>
'''
    
    if charts.get('revenue'):
        html += f'''
                <div class="chart-container">
                    <img src="data:image/png;base64,{charts['revenue']}" alt="Przychody i Zysk">
                </div>
'''
    
    if charts.get('margins'):
        html += f'''
                <div class="chart-container">
                    <img src="data:image/png;base64,{charts['margins']}" alt="Marże">
                </div>
'''
    
    if charts.get('cash'):
        html += f'''
                <div class="chart-container">
                    <img src="data:image/png;base64,{charts['cash']}" alt="Gotówka">
                </div>
'''
    
    if charts.get('cashflow'):
        html += f'''
                <div class="chart-container">
                    <img src="data:image/png;base64,{charts['cashflow']}" alt="Cash Flow">
                </div>
'''
    
    if charts.get('seasonality'):
        html += f'''
                <div class="chart-container">
                    <img src="data:image/png;base64,{charts['seasonality']}" alt="Sezonowość">
                </div>
'''
    
    html += '''
            </section>
'''
    
    # === DANE HISTORYCZNE ===
    html += '''
            <section id="historical">
                <h2>📋 Dane Historyczne</h2>
'''
    
    # Tabela przychodów i zysków
    if data.revenue:
        quarters = list(data.revenue.keys())[-8:]
        html += '''
                <h3>Rachunek Zysków i Strat (tys. PLN)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Pozycja</th>
'''
        for q in quarters:
            html += f'<th>{q.split("(")[0].strip()}</th>'
        
        html += '''
                        </tr>
                    </thead>
                    <tbody>
'''
        
        rows = [
            ('Przychody', data.revenue),
            ('EBIT', data.ebit),
            ('Zysk netto', data.net_profit),
        ]
        
        for row_name, row_data in rows:
            html += f'<tr><td>{row_name}</td>'
            for q in quarters:
                val = row_data.get(q, 0)
                cls = 'positive' if val > 0 else ('negative' if val < 0 else '')
                html += f'<td class="{cls}">{val:,.0f}</td>'
            html += '</tr>'
        
        html += '''
                    </tbody>
                </table>
'''
    
    # Tabela bilansu
    if data.cash:
        quarters = list(data.cash.keys())[-8:]
        html += '''
                <h3>Bilans - Wybrane Pozycje (tys. PLN)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Pozycja</th>
'''
        for q in quarters:
            html += f'<th>{q.split("(")[0].strip()}</th>'
        
        html += '''
                        </tr>
                    </thead>
                    <tbody>
'''
        
        rows = [
            ('Gotówka', data.cash),
            ('Aktywa obrotowe', data.current_assets),
            ('Aktywa razem', data.total_assets),
            ('Kapitał własny', data.equity),
            ('Zobow. krótkoterm.', data.short_term_debt),
        ]
        
        for row_name, row_data in rows:
            html += f'<tr><td>{row_name}</td>'
            for q in quarters:
                val = row_data.get(q, 0)
                html += f'<td>{val:,.0f}</td>'
            html += '</tr>'
        
        html += '''
                    </tbody>
                </table>
'''
    
    html += '''
            </section>
'''
    
    # === KONTEKST Z RAPORTU ===
    if context:
        has_context_content = (
            context.management_comment or 
            context.shareholders or 
            context.innovations or 
            context.risks or
            context.employees
        )
        
        if has_context_content:
            html += '''
            <section id="context">
                <h2>📋 Kontekst z Raportu Kwartalnego</h2>
'''
            
            # Zatrudnienie
            if context.employees:
                html += f'''
                <div class="context-item">
                    <h3>👥 Zatrudnienie</h3>
                    <p><strong>{context.employees:.1f} FTE</strong></p>
                </div>
'''
            
            # Komentarz zarządu
            if context.management_comment:
                comment_html = context.management_comment.replace('\n', '<br>')
                # Zamień punktory na listy
                comment_html = re.sub(r'^- ', '• ', comment_html, flags=re.MULTILINE)
                html += f'''
                <div class="context-item">
                    <h3>💬 Komentarz Zarządu</h3>
                    <p>{comment_html}</p>
                </div>
'''
            
            # Akcjonariat
            if context.shareholders:
                html += '''
                <div class="context-item">
                    <h3>📊 Struktura Akcjonariatu</h3>
                    <table class="shareholders-table">
                        <thead>
                            <tr>
                                <th>Akcjonariusz</th>
                                <th>Kapitał</th>
                                <th>Głosy</th>
                            </tr>
                        </thead>
                        <tbody>
'''
                for sh in context.shareholders:
                    votes = f"{sh['votes']:.2f}%" if sh.get('votes') else '-'
                    html += f'''
                            <tr>
                                <td>{sh['name']}</td>
                                <td>{sh['capital']:.2f}%</td>
                                <td>{votes}</td>
                            </tr>
'''
                html += '''
                        </tbody>
                    </table>
                </div>
'''
            
            # Innowacje / R&D
            if context.innovations:
                innovations_html = context.innovations.replace('\n', '<br>')
                innovations_html = re.sub(r'^- ', '• ', innovations_html, flags=re.MULTILINE)
                html += f'''
                <div class="context-item">
                    <h3>🔬 Innowacje / R&D</h3>
                    <p>{innovations_html}</p>
                </div>
'''
            
            # Ryzyka
            if context.risks:
                risks_html = context.risks.replace('\n', '<br>')
                risks_html = re.sub(r'^- ', '⚠️ ', risks_html, flags=re.MULTILINE)
                html += f'''
                <div class="context-item risks">
                    <h3>⚠️ Ryzyka i Uwagi</h3>
                    <p>{risks_html}</p>
                </div>
'''
            
            html += '''
            </section>
'''
    
    # === ZAŁĄCZNIKI ===
    if attachments:
        html += '''
            <section id="attachments">
                <h2>📎 Załączniki</h2>
                <div class="attachments-list">
'''
        for att in attachments:
            icon = '📄' if att.filetype == 'pdf' else '📝'
            # Link relatywny
            html += f'''
                    <a href="{att.filename}" class="attachment" target="_blank">
                        <span class="attachment-icon">{icon}</span>
                        <span>{att.description or att.filename}</span>
                    </a>
'''
        html += '''
                </div>
            </section>
'''
    
    # === FOOTER ===
    html += f'''
        </main>
        
        <footer>
            <p>Raport wygenerowany automatycznie przez Company Analyzer</p>
            <p>{generated} | Dane: BiznesRadar, ESPI</p>
        </footer>
    </div>
</body>
</html>
'''
    
    return html


# =============================================================================
# MAIN
# =============================================================================

def analyze_company(ticker: str) -> bool:
    """Główna funkcja analizy spółki"""
    ticker = ticker.upper()
    folder_path = os.path.join(RAPORTY_DIR, ticker.lower())
    
    print(f"\n{'='*60}")
    print(f"📊 ANALIZA: {ticker}")
    print(f"{'='*60}")
    
    # Sprawdź czy folder istnieje
    if not os.path.exists(folder_path):
        print(f"❌ Nie znaleziono folderu: {folder_path}")
        print(f"   Utwórz folder raporty/{ticker.lower()}/ i dodaj pliki.")
        return False
    
    print(f"📁 Folder: {folder_path}")
    
    # Wczytaj dane finansowe
    print("\n📥 Wczytuję dane finansowe...")
    data = load_financial_data(ticker, folder_path)
    
    if not data.quarters:
        print("❌ Nie znaleziono danych finansowych")
        print("   Upewnij się, że pliki bilans_*.txt, rzis_*.txt, przeplywy_*.txt są w folderze")
        return False
    
    print(f"   ✅ Znaleziono {len(data.quarters)} kwartałów")
    print(f"   📅 Zakres: {data.quarters[0]} - {data.quarters[-1]}")
    
    # Szukaj raportu PDF
    pdf_files = glob.glob(os.path.join(folder_path, f'{ticker.lower()}*.pdf'))
    pdf_files += glob.glob(os.path.join(folder_path, f'{ticker.upper()}*.pdf'))
    
    if pdf_files:
        print(f"\n📄 Parsowanie raportu: {os.path.basename(pdf_files[0])}")
        pdf_data = parse_quarterly_pdf(pdf_files[0])
        data.report_date = pdf_data.get('report_date')
        # Nie nadpisuj employees z PDF - kontekst jest lepszy
        if not data.employees:
            data.employees = pdf_data.get('employees')
        data.management_comment = pdf_data.get('management_comment')
    
    # Wczytaj kontekst z pliku _kontekst.txt
    context_file = os.path.join(folder_path, f'{ticker.lower()}_kontekst.txt')
    context = None
    
    if os.path.exists(context_file):
        print(f"\n📋 Wczytuję kontekst: {os.path.basename(context_file)}")
        context = parse_context_file(context_file)
        if context:
            if context.employees:
                data.employees = context.employees
                print(f"   ✅ Zatrudnienie: {context.employees} FTE")
            if context.shareholders:
                print(f"   ✅ Akcjonariat: {len(context.shareholders)} akcjonariuszy")
            if context.management_comment:
                print(f"   ✅ Komentarz zarządu: {len(context.management_comment)} znaków")
            if context.innovations:
                print(f"   ✅ Innowacje/R&D")
            if context.risks:
                print(f"   ✅ Ryzyka/Uwagi")
    else:
        print(f"\n📋 Brak pliku kontekstu ({ticker.lower()}_kontekst.txt)")
        print(f"   💡 Możesz go utworzyć ręcznie z informacjami z raportu kwartalnego")
    
    # Oblicz metryki
    print("\n📊 Obliczam metryki...")
    metrics = calculate_metrics(data)
    
    for key, val in metrics.items():
        if isinstance(val, float):
            print(f"   {key}: {val:,.2f}")
    
    # Generuj alerty
    print("\n🚨 Generuję alerty...")
    alerts = generate_alerts(data, metrics)
    for alert in alerts:
        icon = {'success': '✅', 'warning': '⚠️', 'danger': '❌', 'info': 'ℹ️'}.get(alert.type, '•')
        print(f"   {icon} {alert.title}")
    
    # Znajdź załączniki
    print("\n📎 Szukam załączników...")
    attachments = find_attachments(folder_path, ticker)
    for att in attachments:
        print(f"   📄 {att.filename}")
    
    # Generuj wykresy
    print("\n📈 Generuję wykresy...")
    charts = {}
    
    try:
        charts['revenue'] = create_revenue_chart(data)
        print("   ✅ Przychody i zysk")
    except Exception as e:
        print(f"   ⚠️ Błąd wykresu przychodów: {e}")
    
    try:
        charts['margins'] = create_margins_chart(data)
        print("   ✅ Marże")
    except Exception as e:
        print(f"   ⚠️ Błąd wykresu marż: {e}")
    
    try:
        charts['cash'] = create_cash_chart(data)
        print("   ✅ Gotówka")
    except Exception as e:
        print(f"   ⚠️ Błąd wykresu gotówki: {e}")
    
    try:
        charts['cashflow'] = create_cashflow_chart(data)
        print("   ✅ Cash Flow")
    except Exception as e:
        print(f"   ⚠️ Błąd wykresu cash flow: {e}")
    
    try:
        charts['seasonality'] = create_seasonality_chart(data)
        print("   ✅ Sezonowość")
    except Exception as e:
        print(f"   ⚠️ Błąd wykresu sezonowości: {e}")
    
    # Generuj HTML
    print("\n📝 Generuję raport HTML...")
    html = generate_html_report(data, metrics, alerts, attachments, charts, context)
    
    # Zapisz
    output_path = os.path.join(folder_path, f'{ticker.lower()}_raport_analityczny.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n{'='*60}")
    print(f"✅ RAPORT ZAPISANY")
    print(f"{'='*60}")
    print(f"📄 {output_path}")
    print(f"\nOtwórz w przeglądarce, aby zobaczyć raport.")
    
    return True


def list_available_companies() -> List[str]:
    """Listuje dostępne spółki (foldery w raporty/)"""
    if not os.path.exists(RAPORTY_DIR):
        return []
    
    companies = []
    for item in os.listdir(RAPORTY_DIR):
        folder = os.path.join(RAPORTY_DIR, item)
        if os.path.isdir(folder):
            companies.append(item.upper())
    
    return sorted(companies)


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           📊 COMPANY ANALYZER - Raport Analityczny           ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Sprawdź argumenty
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        # Pokaż dostępne spółki
        available = list_available_companies()
        
        if available:
            print(f"Dostępne spółki: {', '.join(available)}")
        else:
            print(f"ℹ️  Brak folderów w raporty/")
            print(f"   Utwórz folder np. raporty/gen/ i dodaj pliki z BiznesRadar")
        
        print()
        ticker = input("Podaj ticker spółki: ").strip().upper()
    
    if not ticker:
        print("❌ Nie podano tickera")
        return
    
    # Uruchom analizę
    success = analyze_company(ticker)
    
    if not success:
        print("\n❌ Analiza nie powiodła się")
        sys.exit(1)


if __name__ == "__main__":
    main()
