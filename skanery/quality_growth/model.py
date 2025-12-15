#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL: Quality Growth
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


class QualityGrowthScanner(BaseScanner):
    
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'ROE', 'ROA'}
    
    def __init__(self, config_path: str = None):
        super().__init__(
            name="Quality Growth",
            description="Spółki z powtarzalnym wzrostem zysków operacyjnych"
        )
        
        # Załaduj config
        if config_path is None:
            config_path = os.path.join(SCANNER_DIR, "config.yaml")
        self.config = load_config(config_path)
        
        # Wagi z configu lub domyślne
        wagi = self.config.get('wagi', {})
        self.weights = {
            'quality': wagi.get('quality', 0.30),
            'growth': wagi.get('growth', 0.25),
            'rev_confirm': wagi.get('rev_confirm', 0.15),
            'value': wagi.get('value', 0.20),
            'pbv_sanity': wagi.get('pbv_sanity', 0.10)
        }
    
    def _score_quality(self, row) -> float:
        roe = row.get('ROE', 0)
        roa = row.get('ROA', 0)
        
        roe_score = min(100, max(0, roe / 25 * 100))
        roa_score = min(100, max(0, roa / 15 * 100))
        return roe_score * 0.6 + roa_score * 0.4
    
    def _score_growth(self, row) -> float:
        ebit = row.get('EBIT_3Y', 0)
        
        if ebit <= 0:
            return 20
        elif ebit > 100:
            return 60  # Podejrzanie wysoki
        elif ebit > 50:
            return 90
        elif ebit > 30:
            return 100  # Sweet spot
        elif ebit > 20:
            return 85
        elif ebit > 10:
            return 70
        else:
            return max(20, ebit * 5)
    
    def _score_revenue_confirm(self, row) -> float:
        rev = row.get('Rev_3Y', 0)
        
        if rev < 5:
            return 30
        elif rev > 20:
            return 100
        else:
            return 50 + rev * 2.5
    
    def _score_value(self, row) -> float:
        pe = row.get('P_E', 0)
        p_ebit = row.get('P_EBIT', 0)
        
        # P/E scoring
        if pe <= 0:
            pe_score = 0
        elif pe < 5:
            pe_score = 70
        elif pe < 8:
            pe_score = 100
        elif pe < 12:
            pe_score = 90
        elif pe < 15:
            pe_score = 70
        elif pe < 20:
            pe_score = 50
        else:
            pe_score = max(0, 100 - (pe - 20) * 3)
        
        # P/EBIT scoring
        if p_ebit <= 0:
            ebit_score = 0
        elif p_ebit < 3:
            ebit_score = 70
        elif p_ebit < 6:
            ebit_score = 100
        elif p_ebit < 10:
            ebit_score = 80
        else:
            ebit_score = max(0, 100 - (p_ebit - 10) * 5)
        
        return pe_score * 0.5 + ebit_score * 0.5
    
    def _score_pbv_sanity(self, row) -> float:
        pbv = row.get('P_BV', 0)
        
        if pbv <= 0:
            return 0
        elif pbv < 0.5:
            return 40  # Value trap risk
        elif pbv < 1.0:
            return 70
        elif pbv < 2.0:
            return 100
        elif pbv < 4.0:
            return 80
        else:
            return max(30, 100 - (pbv - 4) * 10)
    
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df['S_Quality'] = df.apply(self._score_quality, axis=1)
        df['S_Growth'] = df.apply(self._score_growth, axis=1)
        df['S_RevConf'] = df.apply(self._score_revenue_confirm, axis=1)
        df['S_Value'] = df.apply(self._score_value, axis=1)
        df['S_PBV'] = df.apply(self._score_pbv_sanity, axis=1)
        
        df['Total'] = (
            df['S_Quality'] * self.weights['quality'] +
            df['S_Growth'] * self.weights['growth'] +
            df['S_RevConf'] * self.weights['rev_confirm'] +
            df['S_Value'] * self.weights['value'] +
            df['S_PBV'] * self.weights['pbv_sanity']
        )
        
        return df
    
    def get_flags(self, row) -> str:
        flags = []
        if row.get('ROE', 0) > 25:
            flags.append('[Q]')
        if 30 < row.get('EBIT_3Y', 0) < 80:
            flags.append('[G]')
        if 5 < row.get('P_E', 0) < 10:
            flags.append('[V]')
        if row.get('Rev_3Y', 0) > 15:
            flags.append('[R]')
        if row.get('P_BV', 0) < 0.6:
            flags.append('[!]')
        if row.get('EBIT_3Y', 0) > 100:
            flags.append('[?]')
        return ''.join(flags)
    
    def get_output_columns(self) -> List[str]:
        return ['Rank', 'Ticker', 'Rynek', 'Flags', 'Total', 
                'S_Quality', 'S_Growth', 'S_RevConf', 'S_Value', 'S_PBV',
                'ROE', 'ROA', 'EBIT_3Y', 'Rev_3Y', 'P_E', 'P_BV']


# Standalone run
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    # Ścieżka do danych
    config = load_config(os.path.join(SCANNER_DIR, "config.yaml"))
    data_filename = config.get('dane', 'biznesradar_qg.txt')
    data_path = os.path.join(BASE_DIR, "dane", data_filename)
    
    df = load_data(data_path)
    
    if df is not None:
        scanner = QualityGrowthScanner()
        results = scanner.run(df)
        
        if results is not None:
            print(f"\n{'='*70}")
            print(f"TOP 10 - {scanner.name}")
            print(f"{'='*70}")
            print(f"{'Rank':<5} {'Ticker':<8} {'Flags':<12} {'Score':<7} {'ROE%':<7} {'EBIT3Y':<8} {'P/E':<7}")
            print("-" * 70)
            
            for _, row in scanner.get_top(10).iterrows():
                print(f"{row['Rank']:<5} {row['Ticker']:<8} {row['Flags']:<12} {row['Total']:<7.1f} "
                      f"{row.get('ROE',0):<7.1f} {row.get('EBIT_3Y',0):<8.0f} {row.get('P_E',0):<7.2f}")
