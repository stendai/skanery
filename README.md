# GPW Screener

System screeningu spółek z GPW i NewConnect oparty na wielu modelach inwestycyjnych z **Signal Aggregation** do generowania consensus rankingu.

## Szybki start

```bash
# 1. Skopiuj dane z BiznesRadar do folderu dane/
# 2. Uruchom wszystkie modele
python run.py

# 3. Wygeneruj consensus i investment thesis
python app.py

# 4. Wyniki:
#    - main/wyniki_latest.xlsx        (wyniki poszczególnych modeli)
#    - main/wyniki_ostateczne.xlsx    (consensus ranking + thesis)
```

## Struktura projektu

```
gpw_screener/
├── run.py                 # Uruchamia wszystkie skanery
├── app.py                 # Signal Aggregation + Investment Thesis
├── config.yaml            # Globalna konfiguracja
│
├── dane/                  # Dane wejściowe (z BiznesRadar)
│   ├── biznesradar_qg.txt # Dane dla Quality Growth / Turnaround
│   ├── biznesradar_rms.txt # Dane dla Revenue Momentum
│   ├── biznesradar_cq.txt # Dane dla Cash Quality
│   ├── biznesradar_qm.txt # Dane dla Quality Momentum
│   └── biznesradar_vc.txt # Dane dla Valuation Compression
│
├── skanery/               # Modele screeningowe
│   ├── base.py            # Bazowa klasa + funkcje wspólne
│   ├── quality_growth/    # Model Quality Growth
│   ├── turnaround/        # Model Turnaround
│   ├── revenue_momentum/  # Model Revenue Momentum
│   ├── cash_quality/      # Model Cash Quality & Balance Sheet
│   ├── quality_momentum/  # Model Quality Momentum
│   └── valuation_compression/ # Model Valuation Compression
│
├── main/                  # Wyniki
│   ├── wyniki_latest.xlsx       # Najnowsze wyniki modeli
│   ├── wyniki_ostateczne.xlsx   # Consensus ranking + thesis
│   └── archive/                 # Historia wyników
│
├── logs/                  # Logi
└── docs/                  # Dokumentacja
```

## Modele

| Model | Cel | Inspiracja |
|-------|-----|------------|
| **Quality Growth** | Spółki z powtarzalnym wzrostem EBIT | Buffett, Lynch |
| **Turnaround** | Zbite spółki z dobrymi fundamentami | Graham, Contrarian |
| **Revenue Momentum** | Momentum + Bezpieczeństwo + GARP | O'Neil, Piotroski |
| **Cash Quality** | Jakość zysków + solidny bilans | Piotroski, Accrual Anomaly |
| **Quality Momentum** | Stabilna poprawa wyników (nie jednorazowe skoki) | Momentum Factor |
| **Valuation Compression** | Spadająca wycena przy rosnących zyskach | Mean Reversion, PEG |

## Użycie

### 1. Uruchomienie modeli (run.py)

```bash
# Uruchom wszystkie modele
python run.py

# Lista dostępnych skanerów
python run.py --list

# Uruchom wybrane modele
python run.py --only quality_growth turnaround
```

### 2. Signal Aggregation (app.py)

```bash
# Generuj consensus ranking i investment thesis
python app.py

# Pokaż TOP 20 w konsoli
python app.py --top 20

# Szczegółowy profil spółki
python app.py --ticker MLB

# Status systemu
python app.py --status

# Bez zapisywania do pliku
python app.py --no-save
```

### 3. Przykładowy output

```
================================================================================
CONSENSUS - TOP 15
================================================================================
Rank  Ticker   Signal   Cover    Elite   Thesis
--------------------------------------------------------------------------------
1     QNT      35.4     5/6      21      VALUE (Strong): TOP5 w 3 modelach, niska...
2     MLB      35.5     5/6      21      DEFENSIVE (Strong): TOP5 w 3 modelach, b...
3     GEN      27.8     4/6      14      QUALITY (Strong): TOP5: Cash Quality, wy...
4     MND      27.4     3/6      11      GROWTH (Strong): TOP5: Quality Growth, w...
5     BLO      25.9     4/6      12      MOMENTUM (Strong): TOP5: Quality Growth,...
```

### 4. Profil spółki

```bash
python app.py --ticker QNT
```

```
============================================================
PROFIL: QNT
============================================================

📊 Signal Strength: 35.4
📈 Coverage: 5/6 modeli
🏆 Elite Score: 21 (TOP5: 3x, TOP10: 5x)
🚩 Flagi: [G][Q][S][V]
⚠️  Warnings: 0

💡 INVESTMENT THESIS:
   VALUE (Strong): TOP5 w 3 modelach, niska wycena, bezpieczeństwo

📋 WYSTĄPIENIA W MODELACH:
   • Quality Growth              Rank: #5  Score: 91.4 Flags: [Q][V]
   • Revenue Momentum & Safety   Rank: #4  Score: 98.0 Flags: [S][G]
   • Valuation Compression       Rank: #2  Score: 97.9 Flags: [C][V][T]
   ...

📊 SIŁA W KATEGORIACH:
   value        █████ 3.6
   safety       ████░ 2.8
   quality      ███░░ 1.5
```

## Signal Aggregation - Jak to działa

### Metryki

| Metryka | Opis |
|---------|------|
| **Signal Strength** | Główna metryka rankingowa (combo poniższych) |
| **Coverage** | W ilu modelach spółka występuje (1-6) |
| **Elite Score** | Suma punktów: TOP5=5pkt, TOP10=3pkt, TOP20=1pkt |
| **TOP5 Count** | Ile razy w TOP5 różnych modeli |
| **Flag Density** | Średnia liczba pozytywnych flag na model |
| **Warning Count** | Ile flag ostrzegawczych [!] i [?] |

### Wzór Signal Strength

```
Signal Strength = Elite Score 
                + Flag Density × 3 
                + Coverage Bonus (max 6)
                - Warning Penalty × 2
                + Consistency Bonus (max 2.5)
```

### Kategoryzacja flag

| Kategoria | Flagi | Znaczenie |
|-----------|-------|-----------|
| Quality | [Q] | Jakość biznesu |
| Growth | [G], [R] | Wzrost |
| Value | [V], [D] | Niska wycena |
| Momentum | [M], [A] | Momentum |
| Safety | [S], [B], [L] | Bezpieczeństwo |
| Cash | [C] | Cash flow |
| Turnaround | [T] | Sygnały odbicia |
| Warning | [!], [?] | Ostrzeżenia |

### Investment Thesis

System automatycznie generuje "Investment Thesis" dla każdej spółki:

```
{DOMINANT_CATEGORY} ({CONVICTION}): {DETAILS}

Przykłady:
- "VALUE (Strong): TOP5 w 3 modelach, niska wycena, bezpieczeństwo"
- "QUALITY (Medium): TOP5: Cash Quality, wysoka jakość, wzrost"
- "MOMENTUM (Weak): momentum, ⚠️ 2x warning"
```

## Wyniki Excel

### wyniki_ostateczne.xlsx

| Arkusz | Zawartość |
|--------|-----------|
| **CONSENSUS** | Główny ranking po Signal Strength + Investment Thesis |
| **FLAG_HEATMAP** | Macierz spółek vs flag (TOP 30) |
| **BEST_OF** | TOP 3 w każdej kategorii |
| **PROFILES** | Szczegóły wystąpień każdej spółki w modelach |

### Kolorowanie

- 🟢 Zielone tło - TOP 3
- 🟡 Żółte tło - TOP 4-10
- 🔴 Różowe tło - Warnings > 0

## Flagi

| Flaga | Znaczenie | Modele |
|-------|-----------|--------|
| `[Q]` | High Quality / Quality Momentum | QG, TA, CQ, QM |
| `[G]` | Growth | QG, RM |
| `[V]` | Value | QG, RM, CQ, QM, VC |
| `[M]` | Momentum / Margin Expansion | RM, QM |
| `[S]` | Safe | RM, TA |
| `[D]` | Deep Value / Deep Compression | TA, VC |
| `[A]` | Acceleration | RM, QM, VC |
| `[R]` | Revenue Support | QG, QM |
| `[C]` | Cash King / Compression | CQ, VC |
| `[B]` | Strong Balance | CQ |
| `[L]` | Liquid | CQ |
| `[T]` | Turnaround / Trend Confirmed | TA, VC |
| `[!]` | Warning | RM, CQ, QM, VC |
| `[?]` | Verify | QG, RM, CQ, QM, VC |

## Filozofia

### Szukamy spółek które:

1. **Są fundamentalnie dobre** (Quality, Growth, Cash)
2. **Są niedowartościowane** (Value, Compression)
3. **Mają momentum** (Momentum, Acceleration)
4. **Są bezpieczne** (Safety, Balance)
5. **Są ignorowane przez rynek** (brak coverage, niska płynność = okazja)

### Przewaga systemu:

```
Multi-model consensus > Single metric ranking

Spółka wysoko w JEDNYM modelu = może być przypadek
Spółka wysoko w WIELU modelach = silny sygnał
```

## Wymagania

```bash
pip install pandas openpyxl pyyaml
```

## Dodawanie nowego modelu

1. Utwórz folder w `skanery/`:
```bash
mkdir skanery/moj_model
```

2. Stwórz `config.yaml`:
```yaml
nazwa: "Mój Model"
opis: "Opis modelu"
aktywny: true
dane: "biznesradar_qg.txt"
wagi:
  komponent1: 0.50
  komponent2: 0.50
```

3. Stwórz `model.py` dziedziczący po `BaseScanner`

4. Uruchom:
```bash
python run.py
python app.py
```

## Workflow

```
1. Pobierz dane z BiznesRadar (co tydzień/miesiąc)
2. python run.py           → wyniki_latest.xlsx
3. python app.py           → wyniki_ostateczne.xlsx
4. Przejrzyj TOP 10-20 w consensus
5. python app.py --ticker XYZ  → deep dive na kandydatów
6. Podjęcie decyzji inwestycyjnej
```

## Licencja

MIT
