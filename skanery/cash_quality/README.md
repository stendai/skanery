# Cash Quality & Balance Sheet Strength

## Cel modelu

Identyfikacja spółek z **wysoką jakością zysków** (realne cash flow) i **solidnym bilansem**.

Szukamy firm gdzie:
- Zyski przekładają się na gotówkę (nie są "papierowe")
- Bilans jest bezpieczny (niska dźwignia, wysoka płynność)
- Rentowność jest wysoka i stabilna

## Inspiracje

- **Accrual Anomaly** - spółki z wysokim cash conversion outperformują
- **Piotroski F-Score** - jakość finansowa jako predyktor
- **Marty Whitman** - Balance Sheet Investing
- **Joel Greenblatt** - jakość biznesu (ROIC)

## Filozofia

> "Zysk to opinia, gotówka to fakt"

- Wysoki udział zysku w przepływach = zyski są realne
- Niskie zadłużenie = bezpieczeństwo w kryzysie
- Wysoka płynność = elastyczność operacyjna
- I stopień pokrycia > 1 = złota reguła finansowania

## Komponenty scoringu

| Komponent | Waga | Opis |
|-----------|------|------|
| Cash Quality | 30% | Udział zysku netto w przepływach operacyjnych |
| Balance Sheet | 25% | Zadłużenie + Płynność + I stopień pokrycia |
| Profitability | 25% | ROE + ROA + Marża operacyjna |
| Value | 20% | P/E (nie przepłacamy za jakość) |

## Scoring szczegółowy

### Cash Quality (30%)

**Udział zysku netto w przepływach operacyjnych:**
| Cash Conversion | Score | Komentarz |
|-----------------|-------|-----------|
| < 0% | 10 | Negatywny - zyski papierowe |
| 0-20% | 30 | Słaby |
| 20-50% | 50 | Umiarkowany |
| **50-100%** | **80** | **Dobry** |
| **100-150%** | **100** | **Excellent** |
| 150-200% | 90 | Bardzo wysoki |
| > 200% | 70 | Weryfikuj (jednorazowe?) |

### Balance Sheet (25%)

**Zadłużenie ogólne (40%):**
| Debt Ratio | Score |
|------------|-------|
| < 0.15 | 100 |
| 0.15-0.30 | 90 |
| 0.30-0.45 | 70 |
| 0.45-0.60 | 50 |
| > 0.60 | 30 |

**Płynność bieżąca (30%):**
| Current Ratio | Score |
|---------------|-------|
| < 1.0 | 20 |
| 1.0-1.5 | 50 |
| 1.5-3.0 | 80 |
| 3.0-6.0 | 100 |
| > 6.0 | 90 |

**I stopień pokrycia (30%):**
| Coverage I | Score | Komentarz |
|------------|-------|-----------|
| < 1.0 | 30 | Złota reguła naruszona |
| 1.0-1.5 | 60 | OK |
| 1.5-3.0 | 90 | Dobry |
| > 3.0 | 100 | Excellent |

### Profitability (25%)

- **ROE** (40%): >25% = świetny biznes
- **ROA** (30%): >15% = efektywne aktywa
- **Marża operacyjna** (30%): >20% = pricing power

### Value (20%)

| P/E | Score |
|-----|-------|
| < 3 | 50 (value trap?) |
| 3-6 | 90 |
| **6-10** | **100** |
| 10-15 | 80 |
| 15-20 | 60 |
| > 20 | 40 |

## Flagi

| Flaga | Znaczenie | Warunek |
|-------|-----------|---------|
| `[C]` | Cash King | Cash conversion > 100% |
| `[B]` | Strong Balance | Debt < 0.25 i Płynność > 3 |
| `[Q]` | Quality | ROE > 25% i ROA > 15% |
| `[V]` | Value | P/E < 10 |
| `[L]` | Liquid | Płynność bieżąca > 5 |
| `[!]` | Warning | Cash conversion < 20% |
| `[?]` | Verify | Cash conversion > 200% |

## Idealna spółka

Flagi: `[C][B][Q][V]`
- Cash King - zyski to gotówka
- Silny bilans - bezpieczeństwo
- Wysoka jakość - rentowność
- Dobra wycena - nie przepłacamy

## Kiedy model działa najlepiej?

- W niepewnych czasach (recesja, kryzys)
- Gdy szukasz "defensive quality"
- Gdy chcesz uniknąć "earnings manipulation"

## Ryzyko

⚠️ **Cash conversion może być jednorazowy** - sprawdź:
- Czy to nie sprzedaż aktywów?
- Czy to nie jednorazowe rozliczenie?
- Porównaj z poprzednimi kwartałami

## Horyzont

1-3 lata - jakość bilansowa chroni w trudnych czasach
