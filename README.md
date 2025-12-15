# GPW Screener

System screeningu spółek z GPW i NewConnect oparty na wielu modelach inwestycyjnych.

## Szybki start

```bash
# 1. Skopiuj dane z BiznesRadar do folderu dane/
# 2. Uruchom wszystkie modele
python run.py

# 3. Wyniki w main/wyniki_latest.xlsx
```

## Struktura projektu

```
gpw_screener/
├── run.py                 # Uruchamia wszystkie skanery
├── app.py                 # Aplikacja do analizy (consensus, etc.)
├── config.yaml            # Globalna konfiguracja
│
├── dane/                  # Dane wejściowe (z BiznesRadar)
│   ├── biznesradar_qg.txt # Dane dla Quality Growth / Turnaround
│   ├── biznesradar_rms.txt # Dane dla Revenue Momentum
│   ├── biznesradar_cq.txt # Dane dla Cash Quality
│   └── biznesradar_qm.txt # Dane dla Quality Momentum
│
├── skanery/               # Modele screeningowe
│   ├── base.py            # Bazowa klasa + funkcje wspólne
│   ├── quality_growth/    # Model Quality Growth
│   │   ├── model.py
│   │   ├── config.yaml
│   │   └── README.md
│   ├── turnaround/        # Model Turnaround
│   ├── revenue_momentum/  # Model Revenue Momentum
│   ├── cash_quality/      # Model Cash Quality & Balance Sheet
│   └── quality_momentum/  # Model Quality Momentum
│
├── main/                  # Wyniki
│   ├── wyniki_latest.xlsx # Najnowsze wyniki
│   └── archive/           # Historia wyników
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
| **Quality Momentum** | Stabilna poprawa wyników (nie jednorazowe skoki) | Momentum Factor, Mean Reversion |

## Użycie

### Uruchomienie wszystkich modeli
```bash
python run.py
```

### Lista dostępnych skanerów
```bash
python run.py --list
```

### Uruchomienie wybranych modeli
```bash
python run.py --only quality_growth turnaround
```

### Consensus - spółki wysoko we wszystkich modelach
```bash
python app.py --consensus
```

### Uruchomienie pojedynczego modelu (standalone)
```bash
cd skanery/quality_growth
python model.py
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

3. Stwórz `model.py` dziedziczący po `BaseScanner`:
```python
from base import BaseScanner

class MojModelScanner(BaseScanner):
    REQUIRED_COLUMNS = {'Ticker', 'ROE', 'ROA'}
    
    def __init__(self, config_path=None):
        super().__init__("Mój Model", "Opis")
        # ...
    
    def score(self, df):
        # Logika scoringu
        return df
    
    def get_flags(self, row):
        # Zwróć flagi
        return ""
```

4. Opcjonalnie dodaj `README.md` z dokumentacją

5. Uruchom:
```bash
python run.py
```

## Dane wejściowe

Dane pobierane z BiznesRadar.pl - skopiuj tabelę (Ctrl+C) i wklej do pliku .txt.

### Wymagane kolumny dla poszczególnych modeli

**Quality Growth / Turnaround:**
- ROE, ROA
- Zysk operacyjny na akcję 3 lata
- Przychody dynamika 3 lata
- Cena/Zysk, Cena/Wartość księgowa
- Marża zysku operacyjnego k/k, r/r

**Revenue Momentum:**
- ROE, ROA
- Przychody ze sprzedaży kwart r/r
- Przychody ze sprzedaży O4K r/r
- Zadłużenie ogólne
- Pokrycie aktywów trwałych
- Marża zysku operacyjnego

**Cash Quality:**
- ROE, ROA
- Udział zysku netto w przepływach operacyjnych r/r
- Zadłużenie ogólne
- I stopień pokrycia
- Płynność bieżąca
- Marża zysku operacyjnego
- Cena/Zysk

**Quality Momentum:**
- ROE k/k, ROE r/r
- ROA k/k, ROA r/r
- Przychody ze sprzedaży kwart k/k, r/r
- Marża zysku operacyjnego k/k, r/r
- Marża zysku netto k/k, r/r
- Cena/Zysk

## Wyniki

Wyniki zapisywane są w `main/`:
- `wyniki_YYYY-MM-DD_HHMM.xlsx` - z timestampem
- `wyniki_latest.xlsx` - zawsze najnowsze
- `archive/` - historia

### Struktura pliku Excel

1. **PODSUMOWANIE** - tabela z TOP 5 z każdego modelu
2. **Quality Growth** - pełne wyniki modelu
3. **Turnaround** - pełne wyniki modelu
4. **Revenue Momentum** - pełne wyniki modelu
5. **Cash Quality** - pełne wyniki modelu
6. **Quality Momentum** - pełne wyniki modelu

### Kolorowanie

- 🟢 Zielone tło - TOP 5
- 🟡 Żółte tło - TOP 6-10

## Flagi

Każdy model definiuje własne flagi sygnalizujące kluczowe cechy:

| Flaga | Znaczenie | Modele |
|-------|-----------|--------|
| `[Q]` | High Quality / Quality Momentum | QG, TA, CQ, QM |
| `[G]` | Growth | QG, RM |
| `[V]` | Value | QG, RM, CQ, QM |
| `[M]` | Momentum / Margin Expansion | RM, QM |
| `[S]` | Safe | RM, TA |
| `[D]` | Deep Value | TA |
| `[A]` | Acceleration | RM, QM |
| `[R]` | Revenue Support | QG, QM |
| `[C]` | Cash King | CQ |
| `[B]` | Strong Balance | CQ |
| `[L]` | Liquid | CQ |
| `[!]` | Warning | RM, CQ, QM |
| `[?]` | Verify | QG, RM, CQ, QM |

## Wymagania

```bash
pip install pandas openpyxl pyyaml
```

## Licencja

MIT
