#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL: Turnaround
"""

import sys
import os

SCANNER_DIR = os.path.dirname(os.path.abspath(__file__))
SKANERY_DIR = os.path.dirname(SCANNER_DIR)
BASE_DIR = os.path.dirname(SKANERY_DIR)
sys.path.insert(0, SKANERY_DIR)

import pandas as pd
from typing import Set, List
from base import BaseScanner, load_data, load_config


class TurnaroundScanner(BaseScanner):
    
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'ROE', 'ROA'}
    
    def __init__(self, config_path: str = None):
        super().__init__(
            name="Turnaround",
            description="Spółki zbite przez rynek z dobrymi fundamentami"
        )
        
        if config_path is None:
            config_path = os.path.join(SCANNER_DIR, "config.yaml")
        self.config = load_config(config_path)
        
        wagi = self.config.get('wagi', {})
        self.weights = {
            'value': wagi.get('value', 0.35),
            'quality': wagi.get('quality', 0.25),
            'contrarian': wagi.get('contrarian', 0.25),
            'deep_value': wagi.get('deep_value', 0.15)
        }
    
    def _score_value(self, row) -> float:
        pbv = row.get('P_BV', 0)
        pe = row.get('P_E', 0)
        
        pbv_score = max(0, min(100, (1.5 - pbv) / 1.5 * 100)) if pbv > 0 else 50
        pe_score = max(0, min(100, (15 - pe) / 15 * 100)) if pe > 0 else 50
        
        return pbv_score * 0.5 + pe_score * 0.5
    
    def _score_quality(self, row) -> float:
        roe = row.get('ROE', 0)
        roa = row.get('ROA', 0)
        
        roe_score = max(0, min(100, roe / 30 * 100))
        roa_score = max(0, min(100, roa / 20 * 100))
        return roe_score * 0.7 + roa_score * 0.3
    
    def _score_contrarian(self, row) -> float:
        margin_yy = row.get('Margin_YY', 0)
        margin_qq = row.get('Margin_QQ', 0)
        
        if margin_yy < 50 and margin_qq > 0:
            return 80
        elif margin_yy > 200:
            return 40
        else:
            return 60
    
    def _score_deep_value(self, row) -> float:
        pbv = row.get('P_BV', 0)
        
        if pbv <= 0:
            return 0
        elif pbv < 0.5:
            return 100
        elif pbv < 0.7:
            return 80
        elif pbv < 1.0:
            return 50
        else:
            return 0
    
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df['S_Value'] = df.apply(self._score_value, axis=1)
        df['S_Quality'] = df.apply(self._score_quality, axis=1)
        df['S_Contrarian'] = df.apply(self._score_contrarian, axis=1)
        df['S_DeepVal'] = df.apply(self._score_deep_value, axis=1)
        
        df['Total'] = (
            df['S_Value'] * self.weights['value'] +
            df['S_Quality'] * self.weights['quality'] +
            df['S_Contrarian'] * self.weights['contrarian'] +
            df['S_DeepVal'] * self.weights['deep_value']
        )
        
        return df
    
    def get_flags(self, row) -> str:
        flags = []
        if row.get('P_BV', 0) < 0.5:
            flags.append('[D]')
        if row.get('ROE', 0) > 20:
            flags.append('[Q]')
        if row.get('Margin_QQ', 0) > 20 and row.get('Margin_YY', 0) < 100:
            flags.append('[T]')
        if row.get('P_E', 0) < 5 and row.get('P_E', 0) > 0 and row.get('ROE', 0) > 10:
            flags.append('[S]')
        return ''.join(flags)
    
    def get_output_columns(self) -> List[str]:
        return ['Rank', 'Ticker', 'Rynek', 'Flags', 'Total',
                'S_Value', 'S_Quality', 'S_Contrarian', 'S_DeepVal',
                'ROE', 'ROA', 'P_E', 'P_BV', 'Margin_QQ', 'Margin_YY']


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    config = load_config(os.path.join(SCANNER_DIR, "config.yaml"))
    data_filename = config.get('dane', 'biznesradar_qg.txt')
    data_path = os.path.join(BASE_DIR, "dane", data_filename)
    
    df = load_data(data_path)
    
    if df is not None:
        scanner = TurnaroundScanner()
        results = scanner.run(df)
        
        if results is not None:
            print(f"\n{'='*70}")
            print(f"TOP 10 - {scanner.name}")
            print(f"{'='*70}")
            print(f"{'Rank':<5} {'Ticker':<8} {'Flags':<12} {'Score':<7} {'ROE%':<7} {'P/BV':<7} {'P/E':<7}")
            print("-" * 70)
            
            for _, row in scanner.get_top(10).iterrows():
                print(f"{row['Rank']:<5} {row['Ticker']:<8} {row['Flags']:<12} {row['Total']:<7.1f} "
                      f"{row.get('ROE',0):<7.1f} {row.get('P_BV',0):<7.2f} {row.get('P_E',0):<7.2f}")
