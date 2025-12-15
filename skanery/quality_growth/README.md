# Quality Growth

## Cel modelu

Identyfikacja spółek z **powtarzalnym wzrostem zysków operacyjnych** (EBIT).

Szukamy firm gdzie:
- EBIT rośnie 30-50% rocznie przez 3 lata
- Wzrost jest potwierdzony wzrostem przychodów (nie tylko cięcie kosztów)
- Unikamy jednorazowych skoków (EBIT >100%)

## Inspiracje

- **Warren Buffett** - jakość biznesu, economic moat
- **Peter Lynch** - earnings growth, GARP

## Komponenty scoringu

| Komponent | Waga | Opis |
|-----------|------|------|
| Quality | 30% | ROE (60%) + ROA (40%) |
| Growth | 25% | Wzrost EBIT 3Y CAGR |
| Revenue Confirm | 15% | Potwierdzenie wzrostem przychodów |
| Value | 20% | P/E + P/EBIT |
| P/BV Sanity | 10% | Unikanie pułapek wartości |

## Scoring szczegółowy

### Quality (30%)
- ROE 25% = max score
- ROA 15% = max score
- Proporcja: ROE 60%, ROA 40%

### Growth (25%)
| EBIT 3Y | Score | Komentarz |
|---------|-------|-----------|
| < 0% | 20 | Spadek zysków |
| 0-10% | 20-70 | Słaby wzrost |
| 10-20% | 70-85 | Umiarkowany |
| 20-30% | 85-100 | Dobry |
| **30-50%** | **100** | **Sweet spot** |
| 50-100% | 90 | Bardzo wysoki |
| > 100% | 60 | Podejrzany - sprawdź! |

### Revenue Confirm (15%)
- Rev 3Y < 5% = 30 pkt (sam cost cutting)
- Rev 3Y > 20% = 100 pkt

### Value (20%)
| P/E | Score |
|-----|-------|
| < 5 | 70 (value trap risk) |
| **5-8** | **100** |
| 8-12 | 90 |
| 12-15 | 70 |
| > 20 | spadek |

### P/BV Sanity (10%)
- P/BV < 0.5 = 40 pkt (value trap)
- P/BV 1.0-2.0 = 100 pkt (zdrowa)
- P/BV > 4.0 = spadek

## Flagi

| Flaga | Znaczenie | Warunek |
|-------|-----------|---------|
| `[Q]` | High Quality | ROE > 25% |
| `[G]` | Healthy Growth | EBIT 3Y 30-80% |
| `[V]` | Good Value | P/E 5-10 |
| `[R]` | Revenue Growth | Rev 3Y > 15% |
| `[!]` | Value Trap Risk | P/BV < 0.6 |
| `[?]` | Verify Growth | EBIT 3Y > 100% |

## Idealna spółka

Flagi: `[Q][G][V][R]`
- Wysoka jakość (ROE > 25%)
- Zdrowy wzrost (EBIT 30-80%)
- Dobra wycena (P/E 5-10)
- Potwierdzony przychodami (Rev > 15%)

## Użycie

```bash
# Standalone
cd skanery/quality_growth
python model.py

# Przez run.py
cd gpw_screener
python run.py
```

## Źródło danych

BiznesRadar.pl - skaner z kolumnami:
- ROE, ROA
- Zysk operacyjny na akcję 3 lata (średnio)
- Przychody dynamika 3 lata (średnio)
- Cena/Zysk, Cena/Wartość księgowa
