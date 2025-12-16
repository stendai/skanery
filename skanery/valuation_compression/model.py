#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL: Valuation Compression

Identyfikacja spółek gdzie wycena się kompresuje (P/E i P/BV spadają r/r),
co może oznaczać undervalued growth lub re-rating opportunity.
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


class ValuationCompressionScanner(BaseScanner):
    """
    Skaner szukający spółek z:
    - Kompresją P/E r/r (sweet spot -20% do -60%)
    - Kompresją P/BV r/r (sweet spot -10% do -35%)
    - Potwierdzeniem trendu (k/k wspiera r/r)
    - Atrakcyjną absolutną wyceną (P/BV, EV/EBITDA)
    """
    
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'P_E_YY', 'P_BV_YY', 'P_BV'}
    
    def __init__(self, config_path: str = None):
        super().__init__(
            name="Valuation Compression",
            description="Spółki ze spadającą wyceną przy rosnących zyskach"
        )
        
        if config_path is None:
            config_path = os.path.join(SCANNER_DIR, "config.yaml")
        self.config = load_config(config_path)
        
        wagi = self.config.get('wagi', {})
        self.weights = {
            'pe_compression': wagi.get('pe_compression', 0.30),
            'pbv_compression': wagi.get('pbv_compression', 0.25),
            'trend_confirmation': wagi.get('trend_confirmation', 0.20),
            'absolute_value': wagi.get('absolute_value', 0.15),
            'safety_check': wagi.get('safety_check', 0.10)
        }
    
    def _score_pe_compression(self, row) -> float:
        """
        Ocenia kompresję P/E r/r.
        Im bardziej ujemny (do -60%), tym lepiej.
        Ekstremalne wartości (<-80%) są podejrzane.
        """
        pe_yy = row.get('P_E_YY', 0)
        
        # Wycena rośnie - źle
        if pe_yy > 20:
            return 10
        elif pe_yy > 10:
            return 25
        elif pe_yy > 0:
            return 40
        # Lekka kompresja
        elif pe_yy > -10:
            return 55
        elif pe_yy > -20:
            return 75
        # Sweet spot: -20% do -60%
        elif pe_yy > -40:
            return 100
        elif pe_yy > -60:
            return 100
        # Silna kompresja
        elif pe_yy > -80:
            return 80
        # Ekstremalna - podejrzana
        elif pe_yy > -90:
            return 60
        else:
            return 50  # Bardzo ekstremalna - sprawdź!
    
    def _score_pbv_compression(self, row) -> float:
        """
        Ocenia kompresję P/BV r/r.
        Sweet spot: -10% do -35%
        """
        pbv_yy = row.get('P_BV_YY', 0)
        
        # Wycena rośnie - źle
        if pbv_yy > 10:
            return 15
        elif pbv_yy > 0:
            return 35
        # Lekka kompresja
        elif pbv_yy > -10:
            return 55
        # Sweet spot: -10% do -35%
        elif pbv_yy > -20:
            return 85
        elif pbv_yy > -35:
            return 100
        # Silna kompresja
        elif pbv_yy > -50:
            return 75
        # Ekstremalna
        else:
            return 50
    
    def _score_trend_confirmation(self, row) -> float:
        """
        Sprawdza czy k/k potwierdza r/r.
        Najlepiej gdy kompresja przyspiesza (k/k < r/r < 0).
        """
        pe_yy = row.get('P_E_YY', 0)
        pe_qq = row.get('P_E_QQ', 0)
        pbv_yy = row.get('P_BV_YY', 0)
        pbv_qq = row.get('P_BV_QQ', 0)
        
        scores = []
        
        # P/E trend
        if pe_yy < 0 and pe_qq < 0:
            if pe_qq < pe_yy:  # Kompresja przyspiesza
                scores.append(100)
            else:
                scores.append(85)  # Trend potwierdzony
        elif pe_qq < 0 and pe_yy >= 0:
            scores.append(50)  # Nowy trend spadkowy
        elif pe_qq >= 0 and pe_yy < 0:
            scores.append(60)  # Odbicie krótkoterminowe
        else:
            scores.append(25)  # Oba rosną - źle
        
        # P/BV trend
        if pbv_yy < 0 and pbv_qq < 0:
            if pbv_qq < pbv_yy:  # Kompresja przyspiesza
                scores.append(100)
            else:
                scores.append(85)  # Trend potwierdzony
        elif pbv_qq < 0 and pbv_yy >= 0:
            scores.append(50)  # Nowy trend spadkowy
        elif pbv_qq >= 0 and pbv_yy < 0:
            scores.append(60)  # Odbicie krótkoterminowe
        else:
            scores.append(25)  # Oba rosną - źle
        
        return sum(scores) / len(scores) if scores else 50
    
    def _score_absolute_value(self, row) -> float:
        """
        Ocenia absolutną wycenę (P/BV i EV/EBITDA).
        """
        pbv = row.get('P_BV', 0)
        ev_ebitda = row.get('EV_EBITDA', 0)
        
        # P/BV scoring (50%)
        if pbv <= 0:
            pbv_score = 30  # Brak danych lub ujemny
        elif pbv < 0.5:
            pbv_score = 70  # Value trap risk
        elif pbv < 1.0:
            pbv_score = 100  # Poniżej book value
        elif pbv < 1.5:
            pbv_score = 90  # Tania
        elif pbv < 2.5:
            pbv_score = 70  # OK
        elif pbv < 4.0:
            pbv_score = 50  # Droga
        elif pbv < 7.0:
            pbv_score = 35  # Bardzo droga
        else:
            pbv_score = 20  # Ekstremalnie droga
        
        # EV/EBITDA scoring (50%)
        if ev_ebitda <= 0:
            ev_score = 30  # Brak danych
        elif ev_ebitda < 1:
            ev_score = 50  # Bardzo niski - kryzys?
        elif ev_ebitda < 3:
            ev_score = 90  # Bardzo tania
        elif ev_ebitda < 5:
            ev_score = 100  # Sweet spot
        elif ev_ebitda < 8:
            ev_score = 80  # OK
        elif ev_ebitda < 10:
            ev_score = 60  # Droga
        elif ev_ebitda < 12:
            ev_score = 45  # Bardzo droga
        else:
            ev_score = 30  # Ekstremalnie droga
        
        return pbv_score * 0.50 + ev_score * 0.50
    
    def _score_safety_check(self, row) -> float:
        """
        Filtr bezpieczeństwa - kara za ekstremalne wartości.
        """
        pe_yy = row.get('P_E_YY', 0)
        pbv_yy = row.get('P_BV_YY', 0)
        pbv = row.get('P_BV', 0)
        ev_ebitda = row.get('EV_EBITDA', 0)
        
        base_score = 80  # Neutralny start
        
        # Kary za ekstremalne wartości
        if pe_yy < -90:
            base_score -= 30  # Ekstremalna kompresja P/E
        elif pe_yy < -80:
            base_score -= 15
        
        if pbv_yy < -50:
            base_score -= 20  # Ekstremalna kompresja P/BV
        elif pbv_yy < -40:
            base_score -= 10
        
        if 0 < pbv < 0.3:
            base_score -= 20  # Value trap risk
        
        if 0 < ev_ebitda < 1:
            base_score -= 20  # Kryzys?
        
        # Bonus za "zdrową" kompresję
        if -60 < pe_yy < -20 and -35 < pbv_yy < -10:
            base_score += 20  # Idealny zakres
        
        return max(0, min(100, base_score))
    
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Oblicza score dla każdej spółki."""
        df = df.copy()
        
        df['S_PE_Comp'] = df.apply(self._score_pe_compression, axis=1)
        df['S_PBV_Comp'] = df.apply(self._score_pbv_compression, axis=1)
        df['S_TrendConf'] = df.apply(self._score_trend_confirmation, axis=1)
        df['S_AbsValue'] = df.apply(self._score_absolute_value, axis=1)
        df['S_Safety'] = df.apply(self._score_safety_check, axis=1)
        
        df['Total'] = (
            df['S_PE_Comp'] * self.weights['pe_compression'] +
            df['S_PBV_Comp'] * self.weights['pbv_compression'] +
            df['S_TrendConf'] * self.weights['trend_confirmation'] +
            df['S_AbsValue'] * self.weights['absolute_value'] +
            df['S_Safety'] * self.weights['safety_check']
        )
        
        return df
    
    def get_flags(self, row) -> str:
        """Generuje flagi dla spółki."""
        flags = []
        
        pe_yy = row.get('P_E_YY', 0)
        pe_qq = row.get('P_E_QQ', 0)
        pbv_yy = row.get('P_BV_YY', 0)
        pbv_qq = row.get('P_BV_QQ', 0)
        pbv = row.get('P_BV', 0)
        ev_ebitda = row.get('EV_EBITDA', 0)
        
        # [C] Compression - podstawowa kompresja wyceny
        if pe_yy < -30 and pbv_yy < -15:
            flags.append('[C]')
        
        # [V] Value - atrakcyjna absolutna wycena
        if pbv < 1.0 or (0 < ev_ebitda < 5):
            flags.append('[V]')
        
        # [A] Acceleration - kompresja przyspiesza (k/k < r/r)
        accel_count = 0
        if pe_qq < pe_yy < 0:
            accel_count += 1
        if pbv_qq < pbv_yy < 0:
            accel_count += 1
        if accel_count >= 1:
            flags.append('[A]')
        
        # [D] Deep Compression - silna kompresja
        if pe_yy < -50 and pbv_yy < -25:
            flags.append('[D]')
        
        # [T] Trend Confirmed - k/k i r/r zgodne
        if pe_qq < 0 and pe_yy < 0 and pbv_qq < 0 and pbv_yy < 0:
            flags.append('[T]')
        
        # [!] Warning - ekstremalne wartości
        if pe_yy < -90 or pbv_yy < -50:
            flags.append('[!]')
        
        # [?] Verify - wycena rośnie (przeciwny sygnał)
        if pe_yy > 0 and pbv_yy > 0:
            flags.append('[?]')
        
        return ''.join(flags)
    
    def get_output_columns(self) -> List[str]:
        """Zwraca listę kolumn do eksportu."""
        return [
            'Rank', 'Ticker', 'Rynek', 'Flags', 'Total',
            'S_PE_Comp', 'S_PBV_Comp', 'S_TrendConf', 'S_AbsValue', 'S_Safety',
            'P_E_YY', 'P_E_QQ', 'P_BV_YY', 'P_BV_QQ', 'P_BV', 'EV_EBITDA'
        ]


# Standalone run
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    config = load_config(os.path.join(SCANNER_DIR, "config.yaml"))
    data_filename = config.get('dane', 'biznesradar_vc.txt')
    data_path = os.path.join(BASE_DIR, "dane", data_filename)
    
    df = load_data(data_path)
    
    if df is not None:
        scanner = ValuationCompressionScanner()
        results = scanner.run(df)
        
        if results is not None:
            print(f"\n{'='*85}")
            print(f"TOP 10 - {scanner.name}")
            print(f"{'='*85}")
            print(f"{'Rank':<5} {'Ticker':<10} {'Flags':<14} {'Score':<7} {'P/E_YY':<9} {'P/BV_YY':<9} {'P/BV':<7} {'EV/EBITDA':<9}")
            print("-" * 85)
            
            for _, row in scanner.get_top(10).iterrows():
                print(f"{row['Rank']:<5} {row['Ticker']:<10} {row['Flags']:<14} {row['Total']:<7.1f} "
                      f"{row.get('P_E_YY', 0):<9.1f} {row.get('P_BV_YY', 0):<9.1f} "
                      f"{row.get('P_BV', 0):<7.2f} {row.get('EV_EBITDA', 0):<9.2f}")
