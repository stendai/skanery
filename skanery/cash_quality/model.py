#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL: Cash Quality & Balance Sheet Strength

Identyfikacja spółek z wysoką jakością zysków (cash conversion) i solidnym bilansem.
"""

import sys
import os

# Setup path
SCANNER_DIR = os.path.dirname(os.path.abspath(__file__))
SKANERY_DIR = os.path.dirname(SCANNER_DIR)
BASE_DIR = os.path.dirname(SKANERY_DIR)
sys.path.insert(0, SKANERY_DIR)

import pandas as pd
from typing import Set, List
from base import BaseScanner, load_data, load_config


class CashQualityScanner(BaseScanner):
    """
    Skaner szukający spółek z:
    - Wysoką jakością zysków (cash conversion)
    - Solidnym bilansem (niskie zadłużenie, wysoka płynność)
    - Wysoką rentownością (ROE, ROA, marża)
    - Rozsądną wyceną (P/E)
    """
    
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'ROE', 'ROA', 'P_E'}
    
    def __init__(self, config_path: str = None):
        super().__init__(
            name="Cash Quality & Balance Sheet",
            description="Spółki z wysoką jakością zysków i solidnym bilansem"
        )
        
        # Załaduj config
        if config_path is None:
            config_path = os.path.join(SCANNER_DIR, "config.yaml")
        self.config = load_config(config_path)
        
        # Wagi z configu lub domyślne
        wagi = self.config.get('wagi', {})
        self.weights = {
            'cash_quality': wagi.get('cash_quality', 0.30),
            'balance_sheet': wagi.get('balance_sheet', 0.25),
            'profitability': wagi.get('profitability', 0.25),
            'value': wagi.get('value', 0.20)
        }
    
    def _score_cash_quality(self, row) -> float:
        """
        Ocenia jakość zysków na podstawie udziału w przepływach operacyjnych.
        Wysoki udział = zyski są realne (gotówka), nie papierowe.
        """
        cash_conv = row.get('Cash_Conv', 0)
        
        if cash_conv < 0:
            return 10  # Negatywny - zyski papierowe
        elif cash_conv < 20:
            return 30  # Słaby
        elif cash_conv < 50:
            return 50 + cash_conv * 0.6  # 50-80
        elif cash_conv < 100:
            return 80 + (cash_conv - 50) * 0.4  # 80-100
        elif cash_conv < 150:
            return 100  # Sweet spot
        elif cash_conv < 200:
            return 90  # Bardzo wysoki
        else:
            return 70  # Ekstremalnie wysoki - weryfikuj
    
    def _score_balance_sheet(self, row) -> float:
        """
        Ocenia solidność bilansu:
        - Zadłużenie ogólne (40%)
        - Płynność bieżąca (30%)
        - I stopień pokrycia (30%)
        """
        debt = row.get('Debt_Ratio', 0)
        liquidity = row.get('Current_Ratio', 0)
        coverage = row.get('Coverage_I', 0)
        
        # Zadłużenie (40%) - im niższe tym lepiej
        if debt <= 0:
            debt_score = 50  # Brak danych
        elif debt < 0.15:
            debt_score = 100
        elif debt < 0.30:
            debt_score = 90
        elif debt < 0.45:
            debt_score = 70
        elif debt < 0.60:
            debt_score = 50
        else:
            debt_score = max(20, 50 - (debt - 0.6) * 100)
        
        # Płynność bieżąca (30%)
        if liquidity <= 0:
            liq_score = 30  # Brak danych
        elif liquidity < 1.0:
            liq_score = 20  # Problemy z płynnością
        elif liquidity < 1.5:
            liq_score = 50
        elif liquidity < 3.0:
            liq_score = 80
        elif liquidity < 6.0:
            liq_score = 100
        else:
            liq_score = 90  # Bardzo wysoka (może nieefektywna?)
        
        # I stopień pokrycia (30%) - złota reguła finansowania
        if coverage <= 0:
            cov_score = 30  # Brak danych
        elif coverage < 1.0:
            cov_score = 30  # Złota reguła naruszona
        elif coverage < 1.5:
            cov_score = 60
        elif coverage < 3.0:
            cov_score = 90
        else:
            cov_score = 100
        
        return debt_score * 0.40 + liq_score * 0.30 + cov_score * 0.30
    
    def _score_profitability(self, row) -> float:
        """
        Ocenia rentowność biznesu:
        - ROE (40%)
        - ROA (30%)
        - Marża operacyjna (30%)
        """
        roe = row.get('ROE', 0)
        roa = row.get('ROA', 0)
        margin = row.get('OpMargin', 0)
        
        # ROE (40%)
        if roe <= 0:
            roe_score = 0
        elif roe < 10:
            roe_score = roe * 5  # 0-50
        elif roe < 20:
            roe_score = 50 + (roe - 10) * 3  # 50-80
        elif roe < 30:
            roe_score = 80 + (roe - 20) * 2  # 80-100
        elif roe < 50:
            roe_score = 100
        else:
            roe_score = 95  # Bardzo wysoki (zweryfikuj dźwignię)
        
        # ROA (30%)
        if roa <= 0:
            roa_score = 0
        elif roa < 5:
            roa_score = roa * 10  # 0-50
        elif roa < 10:
            roa_score = 50 + (roa - 5) * 6  # 50-80
        elif roa < 20:
            roa_score = 80 + (roa - 10) * 2  # 80-100
        else:
            roa_score = 100
        
        # Marża operacyjna (30%)
        if margin <= 0:
            margin_score = 0
        elif margin < 5:
            margin_score = margin * 8  # 0-40
        elif margin < 10:
            margin_score = 40 + (margin - 5) * 6  # 40-70
        elif margin < 20:
            margin_score = 70 + (margin - 10) * 2  # 70-90
        elif margin < 30:
            margin_score = 90 + (margin - 20)  # 90-100
        else:
            margin_score = 100
        
        return roe_score * 0.40 + roa_score * 0.30 + margin_score * 0.30
    
    def _score_value(self, row) -> float:
        """
        Ocenia wycenę - nie przepłacamy za jakość.
        """
        pe = row.get('P_E', 0)
        
        if pe <= 0:
            return 20  # Ujemny P/E lub brak danych
        elif pe < 3:
            return 50  # Bardzo niski - value trap?
        elif pe < 6:
            return 90
        elif pe < 10:
            return 100  # Sweet spot
        elif pe < 15:
            return 80
        elif pe < 20:
            return 60
        elif pe < 30:
            return 40
        else:
            return max(10, 40 - (pe - 30))
    
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Oblicza score dla każdej spółki."""
        df = df.copy()
        
        # Oblicz komponenty
        df['S_CashQual'] = df.apply(self._score_cash_quality, axis=1)
        df['S_Balance'] = df.apply(self._score_balance_sheet, axis=1)
        df['S_Profit'] = df.apply(self._score_profitability, axis=1)
        df['S_Value'] = df.apply(self._score_value, axis=1)
        
        # Oblicz łączny score
        df['Total'] = (
            df['S_CashQual'] * self.weights['cash_quality'] +
            df['S_Balance'] * self.weights['balance_sheet'] +
            df['S_Profit'] * self.weights['profitability'] +
            df['S_Value'] * self.weights['value']
        )
        
        return df
    
    def get_flags(self, row) -> str:
        """Generuje flagi dla spółki."""
        flags = []
        
        # [C] Cash King - wysoka konwersja gotówkowa
        if row.get('Cash_Conv', 0) > 100:
            flags.append('[C]')
        
        # [B] Strong Balance - solidny bilans
        if row.get('Debt_Ratio', 1) < 0.25 and row.get('Current_Ratio', 0) > 3:
            flags.append('[B]')
        
        # [Q] Quality - wysoka rentowność
        if row.get('ROE', 0) > 25 and row.get('ROA', 0) > 15:
            flags.append('[Q]')
        
        # [V] Value - dobra wycena
        if 0 < row.get('P_E', 0) < 10:
            flags.append('[V]')
        
        # [L] Liquid - bardzo wysoka płynność
        if row.get('Current_Ratio', 0) > 5:
            flags.append('[L]')
        
        # [!] Warning - niska konwersja gotówkowa
        if row.get('Cash_Conv', 100) < 20:
            flags.append('[!]')
        
        # [?] Verify - ekstremalna konwersja (jednorazowe?)
        if row.get('Cash_Conv', 0) > 200:
            flags.append('[?]')
        
        return ''.join(flags)
    
    def get_output_columns(self) -> List[str]:
        """Zwraca listę kolumn do eksportu."""
        return [
            'Rank', 'Ticker', 'Rynek', 'Flags', 'Total',
            'S_CashQual', 'S_Balance', 'S_Profit', 'S_Value',
            'Cash_Conv', 'Debt_Ratio', 'Current_Ratio', 'Coverage_I',
            'ROE', 'ROA', 'OpMargin', 'P_E'
        ]


# Standalone run
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Ścieżka do danych
    config = load_config(os.path.join(SCANNER_DIR, "config.yaml"))
    data_filename = config.get('dane', 'biznesradar_cq.txt')
    data_path = os.path.join(BASE_DIR, "dane", data_filename)
    
    df = load_data(data_path)
    
    if df is not None:
        scanner = CashQualityScanner()
        results = scanner.run(df)
        
        if results is not None:
            print(f"\n{'='*80}")
            print(f"TOP 10 - {scanner.name}")
            print(f"{'='*80}")
            print(f"{'Rank':<5} {'Ticker':<10} {'Flags':<14} {'Score':<7} {'CashConv':<9} {'Debt':<6} {'ROE%':<7} {'P/E':<7}")
            print("-" * 80)
            
            for _, row in scanner.get_top(10).iterrows():
                print(f"{row['Rank']:<5} {row['Ticker']:<10} {row['Flags']:<14} {row['Total']:<7.1f} "
                      f"{row.get('Cash_Conv', 0):<9.1f} {row.get('Debt_Ratio', 0):<6.2f} "
                      f"{row.get('ROE', 0):<7.1f} {row.get('P_E', 0):<7.2f}")
