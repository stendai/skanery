#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODEL: Quality Momentum

Identyfikacja spółek z systematyczną, stabilną poprawą wyników.
Unikamy jednorazowych skoków (+1000%) - szukamy sweet spot 20-100%.
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


class QualityMomentumScanner(BaseScanner):
    """
    Skaner szukający spółek z:
    - Stabilną poprawą ROE/ROA (sweet spot 30-80% r/r)
    - Ekspansją marż (operacyjna + netto)
    - Potwierdzeniem trendu (k/k wspiera r/r)
    - Wzrostem przychodów (nie tylko cost cutting)
    - Rozsądną wyceną
    """
    
    REQUIRED_COLUMNS: Set[str] = {'Ticker', 'ROE_YY', 'ROA_YY', 'P_E'}
    
    def __init__(self, config_path: str = None):
        super().__init__(
            name="Quality Momentum",
            description="Spółki z systematyczną, stabilną poprawą wyników"
        )
        
        if config_path is None:
            config_path = os.path.join(SCANNER_DIR, "config.yaml")
        self.config = load_config(config_path)
        
        wagi = self.config.get('wagi', {})
        self.weights = {
            'profitability_momentum': wagi.get('profitability_momentum', 0.30),
            'margin_momentum': wagi.get('margin_momentum', 0.25),
            'trend_confirmation': wagi.get('trend_confirmation', 0.20),
            'revenue_support': wagi.get('revenue_support', 0.15),
            'value': wagi.get('value', 0.10)
        }
    
    def _score_in_sweet_spot(self, value: float, sweet_min: float, sweet_max: float, 
                              suspicious: float, floor: float = 10) -> float:
        """
        Uniwersalna funkcja scoringu dla sweet spot.
        Najwyższy score w przedziale [sweet_min, sweet_max].
        Kara za zbyt niskie i zbyt wysokie (podejrzane) wartości.
        """
        if value < 0:
            return floor
        elif value < sweet_min * 0.3:
            # Bardzo niski
            return floor + (value / (sweet_min * 0.3)) * 20
        elif value < sweet_min:
            # Poniżej sweet spot - rośnie do 80
            progress = (value - sweet_min * 0.3) / (sweet_min - sweet_min * 0.3)
            return 30 + progress * 50
        elif value <= sweet_max:
            # Sweet spot - 100
            return 100
        elif value <= suspicious:
            # Powyżej sweet spot - spada do 60
            progress = (value - sweet_max) / (suspicious - sweet_max)
            return 100 - progress * 40
        elif value <= suspicious * 2:
            # Wysoki - spada do 40
            progress = (value - suspicious) / suspicious
            return 60 - progress * 20
        else:
            # Ekstremalny - podejrzany
            return max(floor, 40 - (value - suspicious * 2) / 100)
    
    def _score_profitability_momentum(self, row) -> float:
        """
        Ocenia momentum rentowności (ROE r/r + ROA r/r).
        Sweet spot: ROE 30-80%, ROA 25-70%
        """
        roe_yy = row.get('ROE_YY', 0)
        roa_yy = row.get('ROA_YY', 0)
        
        # ROE r/r (60%)
        roe_score = self._score_in_sweet_spot(roe_yy, 30, 80, 300)
        
        # ROA r/r (40%)
        roa_score = self._score_in_sweet_spot(roa_yy, 25, 70, 120)
        
        return roe_score * 0.60 + roa_score * 0.40
    
    def _score_margin_momentum(self, row) -> float:
        """
        Ocenia ekspansję marż (operacyjna r/r + netto r/r).
        Sweet spot: Op 15-60%, Netto 20-80%
        """
        margin_op_yy = row.get('Margin_Op_YY', 0)
        margin_net_yy = row.get('Margin_Net_YY', 0)
        
        # Marża operacyjna r/r (50%)
        op_score = self._score_in_sweet_spot(margin_op_yy, 15, 60, 120)
        
        # Marża netto r/r (50%)
        net_score = self._score_in_sweet_spot(margin_net_yy, 20, 80, 150)
        
        return op_score * 0.50 + net_score * 0.50
    
    def _score_trend_confirmation(self, row) -> float:
        """
        Sprawdza czy k/k potwierdza r/r (trend jest aktualny).
        Bonus za akcelerację (k/k > r/r).
        Kara za decelerację (r/r > 0 ale k/k < 0).
        """
        roe_yy = row.get('ROE_YY', 0)
        roe_qq = row.get('ROE_QQ', 0)
        roa_yy = row.get('ROA_YY', 0)
        roa_qq = row.get('ROA_QQ', 0)
        margin_op_yy = row.get('Margin_Op_YY', 0)
        margin_op_qq = row.get('Margin_Op_QQ', 0)
        
        scores = []
        acceleration_count = 0
        
        # ROE
        if roe_yy > 0:
            if roe_qq < -20:
                scores.append(20)
            elif roe_qq < 0:
                scores.append(40)
            elif roe_qq < roe_yy:
                scores.append(70)
            else:
                scores.append(100)
                acceleration_count += 1
        else:
            scores.append(30)
        
        # ROA
        if roa_yy > 0:
            if roa_qq < -20:
                scores.append(20)
            elif roa_qq < 0:
                scores.append(40)
            elif roa_qq < roa_yy:
                scores.append(70)
            else:
                scores.append(100)
                acceleration_count += 1
        else:
            scores.append(30)
        
        # Marża operacyjna
        if margin_op_yy > 0:
            if margin_op_qq < -20:
                scores.append(20)
            elif margin_op_qq < 0:
                scores.append(40)
            elif margin_op_qq < margin_op_yy:
                scores.append(70)
            else:
                scores.append(100)
                acceleration_count += 1
        else:
            scores.append(30)
        
        base_score = sum(scores) / len(scores) if scores else 50
        
        # Bonus za pełną akcelerację
        if acceleration_count >= 2:
            base_score = min(100, base_score + 10)
        
        return base_score
    
    def _score_revenue_support(self, row) -> float:
        """
        Sprawdza czy poprawa rentowności jest wsparta wzrostem przychodów.
        Sweet spot: 10-40% r/r
        """
        rev_yy = row.get('Rev_YY', 0)
        rev_qq = row.get('Rev_QQ', 0)
        
        # Przychody r/r
        if rev_yy < -10:
            base_score = 15
        elif rev_yy < 0:
            base_score = 35
        elif rev_yy < 10:
            base_score = 55
        elif rev_yy <= 40:
            base_score = 100  # Sweet spot
        elif rev_yy <= 80:
            base_score = 90
        elif rev_yy <= 150:
            base_score = 70
        else:
            base_score = 50  # Podejrzanie wysoki
        
        # Bonus za spójność k/k
        if rev_qq > 0 and rev_yy > 0:
            base_score = min(100, base_score + 10)
        
        return base_score
    
    def _score_value(self, row) -> float:
        """
        Nie przepłacamy za momentum.
        Sweet spot: P/E 4-12
        """
        pe = row.get('P_E', 0)
        
        if pe <= 0:
            return 20
        elif pe < 4:
            return 50  # Value trap?
        elif pe <= 8:
            return 100  # Sweet spot
        elif pe <= 12:
            return 90
        elif pe <= 18:
            return 70
        elif pe <= 25:
            return 50
        elif pe <= 40:
            return 30
        else:
            return 15
    
    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Oblicza score dla każdej spółki."""
        df = df.copy()
        
        df['S_ProfitMom'] = df.apply(self._score_profitability_momentum, axis=1)
        df['S_MarginMom'] = df.apply(self._score_margin_momentum, axis=1)
        df['S_TrendConf'] = df.apply(self._score_trend_confirmation, axis=1)
        df['S_RevSupport'] = df.apply(self._score_revenue_support, axis=1)
        df['S_Value'] = df.apply(self._score_value, axis=1)
        
        df['Total'] = (
            df['S_ProfitMom'] * self.weights['profitability_momentum'] +
            df['S_MarginMom'] * self.weights['margin_momentum'] +
            df['S_TrendConf'] * self.weights['trend_confirmation'] +
            df['S_RevSupport'] * self.weights['revenue_support'] +
            df['S_Value'] * self.weights['value']
        )
        
        return df
    
    def get_flags(self, row) -> str:
        """Generuje flagi dla spółki."""
        flags = []
        
        roe_yy = row.get('ROE_YY', 0)
        roa_yy = row.get('ROA_YY', 0)
        margin_op_yy = row.get('Margin_Op_YY', 0)
        margin_net_yy = row.get('Margin_Net_YY', 0)
        rev_yy = row.get('Rev_YY', 0)
        pe = row.get('P_E', 0)
        
        roe_qq = row.get('ROE_QQ', 0)
        roa_qq = row.get('ROA_QQ', 0)
        margin_op_qq = row.get('Margin_Op_QQ', 0)
        
        # [Q] Quality Momentum - ROE i ROA w sweet spot
        if 30 <= roe_yy <= 100 and 20 <= roa_yy <= 80:
            flags.append('[Q]')
        
        # [M] Margin Expansion
        if margin_op_yy > 30 and margin_net_yy > 30:
            flags.append('[M]')
        
        # [A] Acceleration - k/k > r/r dla min. 2 metryk
        accel_count = 0
        if roe_qq > roe_yy > 0:
            accel_count += 1
        if roa_qq > roa_yy > 0:
            accel_count += 1
        if margin_op_qq > margin_op_yy > 0:
            accel_count += 1
        if accel_count >= 2:
            flags.append('[A]')
        
        # [R] Revenue Support
        if rev_yy > 15:
            flags.append('[R]')
        
        # [V] Value
        if 4 <= pe <= 12:
            flags.append('[V]')
        
        # [!] Warning - Extreme (którykolwiek > 500%)
        if any(x > 500 for x in [roe_yy, roa_yy, margin_op_yy, margin_net_yy]):
            flags.append('[!]')
        
        # [?] Verify - Deceleration (r/r > 50% ale k/k < 0)
        if (roe_yy > 50 and roe_qq < 0) or (roa_yy > 50 and roa_qq < 0):
            flags.append('[?]')
        
        return ''.join(flags)
    
    def get_output_columns(self) -> List[str]:
        """Zwraca listę kolumn do eksportu."""
        return [
            'Rank', 'Ticker', 'Rynek', 'Flags', 'Total',
            'S_ProfitMom', 'S_MarginMom', 'S_TrendConf', 'S_RevSupport', 'S_Value',
            'ROE_YY', 'ROA_YY', 'ROE_QQ', 'ROA_QQ',
            'Margin_Op_YY', 'Margin_Net_YY', 'Rev_YY', 'P_E'
        ]


# Standalone run
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    config = load_config(os.path.join(SCANNER_DIR, "config.yaml"))
    data_filename = config.get('dane', 'biznesradar_qm.txt')
    data_path = os.path.join(BASE_DIR, "dane", data_filename)
    
    df = load_data(data_path)
    
    if df is not None:
        scanner = QualityMomentumScanner()
        results = scanner.run(df)
        
        if results is not None:
            print(f"\n{'='*80}")
            print(f"TOP 10 - {scanner.name}")
            print(f"{'='*80}")
            print(f"{'Rank':<5} {'Ticker':<10} {'Flags':<14} {'Score':<7} {'ROE_YY':<9} {'ROA_YY':<9} {'Rev_YY':<8} {'P/E':<7}")
            print("-" * 80)
            
            for _, row in scanner.get_top(10).iterrows():
                print(f"{row['Rank']:<5} {row['Ticker']:<10} {row['Flags']:<14} {row['Total']:<7.1f} "
                      f"{row.get('ROE_YY', 0):<9.1f} {row.get('ROA_YY', 0):<9.1f} "
                      f"{row.get('Rev_YY', 0):<8.1f} {row.get('P_E', 0):<7.2f}")
