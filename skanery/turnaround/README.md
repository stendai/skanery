# Turnaround

## Cel modelu

Identyfikacja spółek **zbitych przez rynek**, ale z dobrymi fundamentami.

Szukamy firm gdzie:
- Cena spadła (P/BV < 1, P/E niskie)
- Jakość biznesu pozostała (ROE > 10%)
- Pojawiają się sygnały odbicia

## Inspiracje

- **Benjamin Graham** - Deep Value
- **Contrarian Investing** - kupuj gdy inni sprzedają

## Filozofia

> "Bądź chciwy, gdy inni się boją"

- Negatywny sentyment = okazja kupna
- P/BV < 0.5 = rynek wycenia poniżej wartości księgowej
- Ale ROE > 10% = spółka dalej generuje zyski
- Szukamy dna i odbicia

## Komponenty scoringu

| Komponent | Waga | Opis |
|-----------|------|------|
| Value | 35% | Im niższe P/BV i P/E tym lepiej |
| Quality | 25% | ROE + ROA (czy spółka zarabia) |
| Contrarian | 25% | Sygnały odbicia (marża QQ vs YY) |
| Deep Value | 15% | Bonus za P/BV < 0.7 |

## Scoring szczegółowy

### Value (35%)
- P/BV < 0.5 = 100 pkt
- P/E < 5 przy ROE > 10% = sweet spot

### Quality (25%)
- ROE > 30% = 100 pkt
- ROA > 20% = 100 pkt
- Proporcja: ROE 70%, ROA 30%

### Contrarian (25%)
- Marża QQ rośnie + YY < 100% = 80 pkt (turnaround w trakcie)
- YY > 200% = 40 pkt (za późno)

### Deep Value Bonus (15%)
| P/BV | Score |
|------|-------|
| < 0.5 | 100 |
| 0.5-0.7 | 80 |
| 0.7-1.0 | 50 |
| > 1.0 | 0 |

## Flagi

| Flaga | Znaczenie | Warunek |
|-------|-----------|---------|
| `[D]` | Deep Value | P/BV < 0.5 |
| `[Q]` | Quality | ROE > 20% |
| `[T]` | Turnaround Signal | Marża QQ↑, YY < 100% |
| `[S]` | Sweet Spot | P/E < 5 + ROE > 10% |

## Idealna spółka

Flagi: `[D][Q][S]`
- Głęboko niedowartościowana
- Wysokiej jakości biznes
- Sweet spot wyceny

## Ryzyko

⚠️ **Value trap** - spółka może być tania z powodu:
- Strukturalnych problemów
- Spadającego rynku
- Złego zarządzania

Zawsze sprawdzaj **dlaczego** jest tania!

## Horyzont

6-18 miesięcy - czekasz na odbicie sentymentu
