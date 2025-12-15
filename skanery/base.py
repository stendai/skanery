#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bazowy moduł dla wszystkich skanerów GPW.
Zawiera wspólne funkcje parsowania, walidacji i eksportu.
"""

import pandas as pd
import os
import re
import logging
import yaml
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)


def parse_percent(val) -> float:
    """Konwertuje wartość z % na float"""
    if pd.isna(val) or val == '' or val == '-':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = str(val).replace('%', '').replace(',', '.').replace(' ', '').replace('\xa0', '')
    cleaned = cleaned.lstrip('+')
    try:
        return float(cleaned)
    except:
        return 0.0


def parse_ticker(val) -> Optional[str]:
    """Wyciąga ticker z formatu 'GEN (GENOMED)' -> 'GEN'"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    match = re.match(r'^([A-Z0-9]+)', val)
    if match:
        return match.group(1)
    return val


def map_header(h: str) -> str:
    """Mapuje nagłówki z BiznesRadar na standardowe nazwy kolumn"""
    h_lower = h.lower()
    
    mappings = [
        ('profil', 'Ticker'),
        ('raport', 'Raport'),
    ]
    
    # Exact matches first
    if h_lower == 'roe':
        return 'ROE'
    if h_lower == 'roa':
        return 'ROA'
    if h_lower == 'rynek':
        return 'Rynek'
    
    # Pattern matches
    if 'roe' in h_lower and 'k/k' in h_lower:
        return 'ROE_QQ'
    if 'roe' in h_lower and 'r/r' in h_lower:
        return 'ROE_YY'
    if 'roa' in h_lower and 'k/k' in h_lower:
        return 'ROA_QQ'
    if 'roa' in h_lower and 'r/r' in h_lower:
        return 'ROA_YY'
    if 'mar' in h_lower and 'operacyj' in h_lower and 'k/k' in h_lower:
        return 'Margin_QQ'
    if 'mar' in h_lower and 'operacyj' in h_lower and 'r/r' in h_lower:
        return 'Margin_YY'
    if 'mar' in h_lower and 'operacyj' in h_lower:
        return 'OpMargin'
    if 'cena' in h_lower and 'operacyj' in h_lower:
        return 'P_EBIT'
    if 'cena' in h_lower and 'zysk' in h_lower and 'operacyj' not in h_lower and 'ksi' not in h_lower:
        return 'P_E'
    if 'cena' in h_lower and 'ksi' in h_lower:
        return 'P_BV'
    if 'zysk operacyjny' in h_lower and '3 lat' in h_lower:
        return 'EBIT_3Y'
    if 'przychody' in h_lower and 'dynamika' in h_lower and '3 lat' in h_lower:
        return 'Rev_3Y'
    if 'przychody' in h_lower and 'kwart' in h_lower:
        return 'Rev_QQ'
    if 'przychody' in h_lower and 'o4k' in h_lower:
        return 'Rev_O4K'
    if 'zad' in h_lower and 'og' in h_lower:
        return 'Debt_Ratio'
    if 'pokrycie' in h_lower and 'aktyw' in h_lower:
        return 'Asset_Coverage'
    if 'profil' in h_lower:
        return 'Ticker'
    
    # === NOWE MAPOWANIA DLA CASH QUALITY ===
    
    # Udział zysku netto w przepływach operacyjnych r/r -> Cash_Conv
    if 'udzia' in h_lower and 'zysk' in h_lower and 'przep' in h_lower:
        return 'Cash_Conv'
    
    # I stopień pokrycia -> Coverage_I
    if 'stopie' in h_lower and 'pokrycia' in h_lower:
        return 'Coverage_I'
    if h_lower == 'i stopień pokrycia':
        return 'Coverage_I'
    
    # Płynność bieżąca -> Current_Ratio
    if 'p' in h_lower and 'ynno' in h_lower and 'bie' in h_lower:
        return 'Current_Ratio'
    if 'płynność bieżąca' in h_lower:
        return 'Current_Ratio'
    
    return h


def load_data(filepath: str) -> Optional[pd.DataFrame]:
    """Wczytuje dane z pliku BiznesRadar (tab-separated)"""
    if not os.path.exists(filepath):
        logger.error(f"Plik '{filepath}' nie istnieje")
        return None
    
    logger.info(f"Wczytuję dane z '{filepath}'")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    data_lines = []
    header_line = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if 'Profil' in line and ('ROE' in line or 'Cena' in line):
            if header_line is None:
                header_line = line
            continue
        
        if 'w radarze' in line.lower() or 'ulubione' in line.lower() or 'znajdź' in line.lower():
            continue
        
        if re.match(r'^[A-Z0-9]+[\s\(]', line):
            first_word = line.split('\t')[0].split()[0].upper()
            if first_word in ['PROFIL', 'ROE', 'ROA', 'RAPORT', 'CENA', 'RYNEK']:
                continue
            data_lines.append(line)
    
    if not header_line:
        logger.error(f"Nie znaleziono nagłówka w pliku '{filepath}'")
        return None
    
    headers = header_line.split('\t')
    header_map = {h.strip(): map_header(h.strip()) for h in headers}
    
    rows = []
    for line in data_lines:
        parts = line.split('\t')
        if len(parts) < 8:
            continue
        
        row = {}
        for i, h in enumerate(headers):
            if i < len(parts):
                mapped = header_map.get(h.strip(), h.strip())
                row[mapped] = parts[i]
        
        row['Ticker'] = parse_ticker(row.get('Ticker', ''))
        if not row['Ticker']:
            continue
        
        roe_val = row.get('ROE', '')
        if isinstance(roe_val, str) and '%' not in roe_val and not re.match(r'^[\d\.\,\-\+]+$', roe_val.strip()):
            continue
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    if len(df) == 0:
        logger.error(f"Brak danych w pliku '{filepath}'")
        return None
    
    # Konwersja kolumn procentowych
    percent_cols = ['ROE', 'ROA', 'ROE_QQ', 'ROE_YY', 'ROA_QQ', 'ROA_YY', 
                    'Margin_QQ', 'Margin_YY', 'EBIT_3Y', 'Rev_3Y',
                    'Rev_QQ', 'Rev_O4K', 'OpMargin',
                    'Cash_Conv']  # NOWA KOLUMNA
    for col in percent_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_percent)
    
    # Konwersja kolumn numerycznych
    numeric_cols = ['P_EBIT', 'P_E', 'P_BV', 'Debt_Ratio', 'Asset_Coverage',
                    'Coverage_I', 'Current_Ratio']  # NOWE KOLUMNY
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_percent(x) if pd.notna(x) else 0)
    
    logger.info(f"Wczytano {len(df)} spółek z '{os.path.basename(filepath)}'")
    return df


def load_config(config_path: str) -> dict:
    """Wczytuje konfigurację YAML"""
    if not os.path.exists(config_path):
        logger.warning(f"Brak pliku konfiguracji: {config_path}")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


class BaseScanner(ABC):
    """Bazowa klasa dla wszystkich skanerów"""
    
    # Każdy skaner musi zdefiniować wymagane kolumny
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'ROE', 'ROA'}
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.weights: Dict[str, float] = {}
        self.results: Optional[pd.DataFrame] = None
        self.logger = logging.getLogger(f"scanner.{self.__class__.__name__}")
    
    @abstractmethod
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Oblicza score dla każdej spółki. Musi zwrócić df z kolumną 'Total'"""
        pass
    
    @abstractmethod
    def get_flags(self, row) -> str:
        """Zwraca flagi jako string do wyświetlania"""
        pass
    
    def get_flags_list(self, row) -> List[str]:
        """Zwraca flagi jako listę (do programowego filtrowania)"""
        flags_str = self.get_flags(row)
        return re.findall(r'\[([A-Z!?]+)\]', flags_str)
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """Sprawdza czy dane zawierają wymagane kolumny"""
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            self.logger.error(f"Brakujące kolumny: {missing}")
            return False
        return True
    
    def normalize_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizuje score do zakresu 0-100"""
        if 'Total' not in df.columns:
            return df
        
        min_score = df['Total'].min()
        max_score = df['Total'].max()
        
        if max_score > min_score:
            df['Total_Raw'] = df['Total']
            df['Total'] = ((df['Total'] - min_score) / (max_score - min_score)) * 100
        
        return df
    
    def run(self, df: pd.DataFrame, normalize: bool = True) -> Optional[pd.DataFrame]:
        """Uruchamia skaner i zwraca posortowane wyniki"""
        self.logger.info(f"Uruchamiam skaner: {self.name}")
        
        if not self.validate_data(df):
            return None
        
        self.results = self.score(df)
        
        if normalize:
            self.results = self.normalize_scores(self.results)
        
        self.results['Flags'] = self.results.apply(self.get_flags, axis=1)
        self.results['Flags_List'] = self.results.apply(self.get_flags_list, axis=1)
        self.results = self.results.sort_values('Total', ascending=False).reset_index(drop=True)
        self.results['Rank'] = range(1, len(self.results) + 1)
        
        self.logger.info(f"Przetworzono {len(self.results)} spółek")
        return self.results
    
    def get_top(self, n: int = 10) -> Optional[pd.DataFrame]:
        """Zwraca top N wyników"""
        if self.results is None:
            return None
        return self.results.head(n)
    
    def get_output_columns(self) -> List[str]:
        """Zwraca listę kolumn do eksportu. Override w klasach dziedziczących."""
        return ['Rank', 'Ticker', 'Rynek', 'Flags', 'Total']
    
    def filter_by_flags(self, flags: List[str], mode: str = 'any') -> pd.DataFrame:
        """
        Filtruje wyniki po flagach.
        mode='any': spółka ma przynajmniej jedną z flag
        mode='all': spółka ma wszystkie flagi
        """
        if self.results is None:
            return pd.DataFrame()
        
        if mode == 'any':
            mask = self.results['Flags_List'].apply(lambda x: bool(set(x) & set(flags)))
        else:  # all
            mask = self.results['Flags_List'].apply(lambda x: set(flags).issubset(set(x)))
        
        return self.results[mask]
