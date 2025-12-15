#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GPW SCREENER - Aplikacja do agregacji i analizy wyników
================================================================================

TODO: Planowane funkcje:
- Wizualizacja wyników (wykresy, heatmapy)
- Porównanie spółek między modelami
- Filtrowanie po flagach
- Consensus scoring (meta-model)
- Historia i tracking zmian
- Eksport raportów (PDF, HTML)

================================================================================
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DIR = os.path.join(BASE_DIR, "main")
LATEST_FILE = os.path.join(MAIN_DIR, "wyniki_latest.xlsx")


def show_status():
    """Pokazuje status systemu"""
    print("\n" + "=" * 60)
    print("GPW SCREENER - Status")
    print("=" * 60)
    
    # Sprawdź wyniki
    if os.path.exists(LATEST_FILE):
        import datetime
        mtime = os.path.getmtime(LATEST_FILE)
        mod_time = datetime.datetime.fromtimestamp(mtime)
        print(f"\n📊 Ostatnie wyniki: {mod_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Plik: {LATEST_FILE}")
    else:
        print("\n⚠️  Brak wyników. Uruchom: python run.py")
    
    # Sprawdź archive
    archive_dir = os.path.join(MAIN_DIR, "archive")
    if os.path.exists(archive_dir):
        archives = [f for f in os.listdir(archive_dir) if f.endswith('.xlsx')]
        print(f"\n📁 Archiwum: {len(archives)} plików")
    
    # Sprawdź skanery
    skanery_dir = os.path.join(BASE_DIR, "skanery")
    if os.path.exists(skanery_dir):
        skanery = [d for d in os.listdir(skanery_dir) 
                   if os.path.isdir(os.path.join(skanery_dir, d)) 
                   and not d.startswith('__')]
        print(f"\n🔍 Skanery: {len(skanery)}")
        for s in skanery:
            print(f"   - {s}")


def find_consensus():
    """Znajduje spółki które są wysoko we wszystkich modelach"""
    if not os.path.exists(LATEST_FILE):
        print("⚠️  Brak wyników. Uruchom: python run.py")
        return
    
    import pandas as pd
    
    print("\n" + "=" * 60)
    print("CONSENSUS - Spółki wysoko we wszystkich modelach")
    print("=" * 60)
    
    # Wczytaj wszystkie arkusze
    xl = pd.ExcelFile(LATEST_FILE)
    
    rankings = {}
    for sheet in xl.sheet_names:
        if sheet == "PODSUMOWANIE":
            continue
        df = pd.read_excel(xl, sheet_name=sheet)
        if 'Ticker' in df.columns and 'Rank' in df.columns:
            for _, row in df.iterrows():
                ticker = row['Ticker']
                rank = row['Rank']
                if ticker not in rankings:
                    rankings[ticker] = {}
                rankings[ticker][sheet] = rank
    
    # Oblicz średni ranking
    consensus = []
    for ticker, ranks in rankings.items():
        if len(ranks) >= 2:  # W co najmniej 2 modelach
            avg_rank = sum(ranks.values()) / len(ranks)
            consensus.append({
                'Ticker': ticker,
                'Avg_Rank': avg_rank,
                'Models': len(ranks),
                'Ranks': ranks
            })
    
    # Sortuj
    consensus.sort(key=lambda x: x['Avg_Rank'])
    
    print(f"\n{'Ticker':<10} {'Śr.Rank':<10} {'Modele':<8} {'Rankingi'}")
    print("-" * 60)
    
    for item in consensus[:15]:
        ranks_str = ', '.join([f"{k[:10]}:{v}" for k, v in item['Ranks'].items()])
        print(f"{item['Ticker']:<10} {item['Avg_Rank']:<10.1f} {item['Models']:<8} {ranks_str}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GPW Screener - Aplikacja')
    parser.add_argument('--status', action='store_true', help='Status systemu')
    parser.add_argument('--consensus', action='store_true', help='Znajdź consensus')
    args = parser.parse_args()
    
    if args.consensus:
        find_consensus()
    else:
        show_status()
        print("\n" + "=" * 60)
        print("Dostępne komendy:")
        print("  python app.py --status     Status systemu")
        print("  python app.py --consensus  Znajdź spółki w wielu modelach")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
