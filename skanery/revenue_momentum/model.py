#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL: Revenue Momentum & Financial Safety
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


class RevenueMomentumScanner(BaseScanner):
    
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'ROE', 'ROA'}
    
    def __init__(self, config_path: str = None):
        super().__init__(
            name="Revenue Momentum & Safety",
            description="GARP + Momentum + Bezpieczeństwo finansowe"
        )
        
        if config_path is None:
            config_path = os.path.join(SCANNER_DIR, "config.yaml")
        self.config = load_config(config_path)
        
        wagi = self.config.get('wagi', {})
        self.weights = {
            'momentum': wagi.get('momentum', 0.25),
            'quality': wagi.get('quality', 0.25),
            'safety': wagi.get('safety', 0.20),
            'value': wagi.get('value', 0.20),
            'consistency': wagi.get('consistency', 0.10)
        }
    
    def _score_momentum(self, row) -> float:
        rev_qq = row.get('Rev_QQ', 0)
        rev_o4k = row.get('Rev_O4K', 0)
        
        # QQ scoring
        if rev_qq < 0:
            qq_score = max(0, 30 + rev_qq)
        elif rev_qq < 5:
            qq_score = 40
        elif rev_qq < 15:
            qq_score = 60 + rev_qq
        elif rev_qq < 30:
            qq_score = 90
        elif rev_qq < 50:
            qq_score = 100
        elif rev_qq < 100:
            qq_score = 85
        else:
            qq_score = 60
        
        # O4K scoring
        if rev_o4k < 0:
            o4k_score = max(0, 30 + rev_o4k)
        elif rev_o4k < 5:
            o4k_score = 50
        elif rev_o4k < 15:
            o4k_score = 70
        elif rev_o4k < 30:
            o4k_score = 100
        elif rev_o4k < 50:
            o4k_score = 90
        else:
            o4k_score = 70
        
        return qq_score * 0.5 + o4k_score * 0.5
    
    def _score_quality(self, row) -> float:
        roe = row.get('ROE', 0)
        roa = row.get('ROA', 0)
        op_margin = row.get('OpMargin', 0)
        
        # ROE (35%)
        if roe < 5:
            roe_score = max(0, roe * 10)
        elif roe < 10:
            roe_score = 50 + (roe - 5) * 6
        elif roe < 15:
            roe_score = 80 + (roe - 10) * 2
        elif roe < 25:
            roe_score = 90 + (roe - 15) * 1
        elif roe < 40:
            roe_score = 100
        else:
            roe_score = 95
        
        # ROA (25%)
        if roa < 3:
            roa_score = max(0, roa * 15)
        elif roa < 8:
            roa_score = 45 + (roa - 3) * 8
        elif roa < 15:
            roa_score = 85 + (roa - 8) * 2
        else:
            roa_score = 100
        
        # Marża (40%)
        if op_margin < 3:
            margin_score = max(0, op_margin * 15)
        elif op_margin < 8:
            margin_score = 45 + (op_margin - 3) * 7
        elif op_margin < 15:
            margin_score = 80 + (op_margin - 8) * 2
        elif op_margin < 25:
            margin_score = 94 + (op_margin - 15) * 0.6
        else:
            margin_score = 100
        
        return roe_score * 0.35 + roa_score * 0.25 + margin_score * 0.40
    
    def _score_safety(self, row) -> float:
        debt_ratio = row.get('Debt_Ratio', 0)
        asset_cov = row.get('Asset_Coverage', 0)
        
        # Zadłużenie (60%)
        if debt_ratio <= 0:
            debt_score = 50
        elif debt_ratio < 0.2:
            debt_score = 100
        elif debt_ratio < 0.35:
            debt_score = 90
        elif debt_ratio < 0.5:
            debt_score = 75
        elif debt_ratio < 0.6:
            debt_score = 55
        elif debt_ratio < 0.7:
            debt_score = 35
        else:
            debt_score = max(0, 35 - (debt_ratio - 0.7) * 100)
        
        # Pokrycie (40%)
        if asset_cov <= 0:
            cov_score = 30
        elif asset_cov < 1.0:
            cov_score = max(20, asset_cov * 50)
        elif asset_cov < 1.3:
            cov_score = 50 + (asset_cov - 1.0) * 100
        elif asset_cov < 2.0:
            cov_score = 80 + (asset_cov - 1.3) * 28
        elif asset_cov < 3.0:
            cov_score = 100
        else:
            cov_score = 95
        
        return debt_score * 0.60 + cov_score * 0.40
    
    def _score_value(self, row) -> float:
        pe = row.get('P_E', 0)
        rev_3y = row.get('Rev_3Y', 0)
        rev_o4k = row.get('Rev_O4K', 0)
        
        growth = max(1, (rev_3y + rev_o4k) / 2) if rev_3y > 0 or rev_o4k > 0 else 10
        
        # P/E (60%)
        if pe <= 0:
            pe_score = 20
        elif pe < 5:
            pe_score = 60
        elif pe < 8:
            pe_score = 90
        elif pe < 12:
            pe_score = 100
        elif pe < 16:
            pe_score = 85
        elif pe < 20:
            pe_score = 65
        elif pe < 25:
            pe_score = 45
        else:
            pe_score = max(10, 45 - (pe - 25) * 2)
        
        # PEG (40%)
        if pe <= 0 or growth <= 0:
            peg_score = 30
        else:
            peg = pe / growth
            if peg < 0.3:
                peg_score = 70
            elif peg < 0.5:
                peg_score = 90
            elif peg < 1.0:
                peg_score = 100
            elif peg < 1.5:
                peg_score = 80
            elif peg < 2.0:
                peg_score = 60
            else:
                peg_score = max(20, 60 - (peg - 2) * 15)
        
        return pe_score * 0.60 + peg_score * 0.40
    
    def _score_consistency(self, row) -> float:
        rev_qq = row.get('Rev_QQ', 0)
        rev_o4k = row.get('Rev_O4K', 0)
        rev_3y = row.get('Rev_3Y', 0)
        
        all_positive = rev_qq > 0 and rev_o4k > 0 and rev_3y > 0
        
        if not all_positive:
            positive_count = sum([1 for x in [rev_qq, rev_o4k, rev_3y] if x > 0])
            return 30 + positive_count * 15
        
        avg = (rev_qq + rev_o4k + rev_3y) / 3
        if avg <= 0:
            return 40
        
        variance = ((rev_qq - avg)**2 + (rev_o4k - avg)**2 + (rev_3y - avg)**2) / 3
        cv = (variance ** 0.5) / avg if avg > 0 else 1
        
        # Trend
        if rev_qq >= rev_o4k >= rev_3y:
            trend_bonus = 15
        elif rev_qq >= rev_o4k or rev_o4k >= rev_3y:
            trend_bonus = 5
        elif rev_qq < rev_3y * 0.5:
            trend_bonus = -15
        else:
            trend_bonus = 0
        
        if cv < 0.2:
            base_score = 100
        elif cv < 0.4:
            base_score = 85
        elif cv < 0.6:
            base_score = 70
        elif cv < 1.0:
            base_score = 55
        else:
            base_score = 40
        
        return min(100, max(0, base_score + trend_bonus))
    
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        df['S_Momentum'] = df.apply(self._score_momentum, axis=1)
        df['S_Quality'] = df.apply(self._score_quality, axis=1)
        df['S_Safety'] = df.apply(self._score_safety, axis=1)
        df['S_Value'] = df.apply(self._score_value, axis=1)
        df['S_Consistency'] = df.apply(self._score_consistency, axis=1)
        
        df['Total'] = (
            df['S_Momentum'] * self.weights['momentum'] +
            df['S_Quality'] * self.weights['quality'] +
            df['S_Safety'] * self.weights['safety'] +
            df['S_Value'] * self.weights['value'] +
            df['S_Consistency'] * self.weights['consistency']
        )
        
        return df
    
    def get_flags(self, row) -> str:
        flags = []
        if row.get('Rev_QQ', 0) > 20 and row.get('Rev_O4K', 0) > 15:
            flags.append('[M]')
        if row.get('ROE', 0) > 20 and row.get('OpMargin', 0) > 15:
            flags.append('[Q]')
        if row.get('Debt_Ratio', 1) < 0.35 and row.get('Asset_Coverage', 0) > 1.5:
            flags.append('[S]')
        pe = row.get('P_E', 0)
        growth = (row.get('Rev_3Y', 0) + row.get('Rev_O4K', 0)) / 2
        if pe > 0 and growth > 0 and pe / growth < 1.0:
            flags.append('[G]')
        if row.get('Rev_QQ', 0) > row.get('Rev_O4K', 0) > row.get('Rev_3Y', 0) > 0:
            flags.append('[A]')
        if row.get('Debt_Ratio', 0) > 0.6:
            flags.append('[!]')
        if row.get('Rev_QQ', 0) > 100:
            flags.append('[?]')
        return ''.join(flags)
    
    def get_output_columns(self) -> List[str]:
        return ['Rank', 'Ticker', 'Rynek', 'Flags', 'Total',
                'S_Momentum', 'S_Quality', 'S_Safety', 'S_Value', 'S_Consistency',
                'Rev_QQ', 'Rev_O4K', 'Rev_3Y', 'ROE', 'OpMargin',
                'Debt_Ratio', 'Asset_Coverage', 'P_E', 'P_BV']


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    config = load_config(os.path.join(SCANNER_DIR, "config.yaml"))
    data_filename = config.get('dane', 'biznesradar_rms.txt')
    data_path = os.path.join(BASE_DIR, "dane", data_filename)
    
    df = load_data(data_path)
    
    if df is not None:
        scanner = RevenueMomentumScanner()
        results = scanner.run(df)
        
        if results is not None:
            print(f"\n{'='*70}")
            print(f"TOP 10 - {scanner.name}")
            print(f"{'='*70}")
            print(f"{'Rank':<5} {'Ticker':<8} {'Flags':<14} {'Score':<7} {'RevQQ':<7} {'RevO4K':<7} {'Debt':<6}")
            print("-" * 70)
            
            for _, row in scanner.get_top(10).iterrows():
                print(f"{row['Rank']:<5} {row['Ticker']:<8} {row['Flags']:<14} {row['Total']:<7.1f} "
                      f"{row.get('Rev_QQ',0):<7.1f} {row.get('Rev_O4K',0):<7.1f} {row.get('Debt_Ratio',0):<6.2f}")
