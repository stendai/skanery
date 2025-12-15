# Revenue Momentum & Financial Safety

## Cel modelu

Identyfikacja spółek z **silnym momentum przychodów** + **bezpieczną strukturą finansową** + **uczciwą wyceną**.

## Inspiracje

- **GARP** (Growth at Reasonable Price) - Peter Lynch
- **CANSLIM** - William O'Neil (bieżący kwartał)
- **Piotroski F-Score** - zdrowie finansowe
- **DuPont Analysis** - dekompozycja ROE

## Filozofia

Łączymy:
1. **Momentum** - krótkoterminowe sygnały wzrostu
2. **Bezpieczeństwo** - niskie zadłużenie chroni w kryzysie
3. **GARP** - płacimy uczciwie za wzrost, nie przepłacamy

## Komponenty scoringu

| Komponent | Waga | Opis |
|-----------|------|------|
| Momentum | 25% | Rev QQ + Rev O4K |
| Quality | 25% | ROE + ROA + Marża operacyjna |
| Safety | 20% | Zadłużenie + Pokrycie aktywów |
| Value | 20% | P/E + PEG-like |
| Consistency | 10% | Spójność wzrostu |

## Scoring szczegółowy

### Momentum (25%)

**Przychody kwartalne (QQ):**
| Rev QQ | Score | Komentarz |
|--------|-------|-----------|
| < 0% | kara | Spadek |
| 0-15% | 40-75 | Słaby |
| **15-50%** | **90-100** | **Sweet spot** |
| 50-100% | 85 | Wysoki |
| > 100% | 60 | Podejrzany |

**Przychody O4K:**
- 15-30% = sweet spot (100 pkt)

### Quality (25%)
- **ROE** (35%): >15% = dobry biznes (Buffett)
- **ROA** (25%): >10% = świetny zwrot
- **Marża operacyjna** (40%): >15% = pricing power

### Safety (20%)

**Zadłużenie ogólne:**
| Debt Ratio | Score |
|------------|-------|
| < 0.2 | 100 |
| 0.2-0.35 | 90 |
| 0.35-0.5 | 75 |
| 0.5-0.6 | 55 |
| > 0.6 | ⚠️ kara |

**Pokrycie aktywów:**
- Golden Rule: > 1.0
- Idealne: > 1.5

### Value (20%)
- **P/E** 8-12 = sweet spot
- **PEG** < 1.0 = idealne GARP

### Consistency (10%)
- Rev QQ ≈ Rev O4K ≈ Rev 3Y = spójny wzrost
- **Akceleracja** (QQ > O4K > 3Y) = bonus +15 pkt
- **Deceleracja** (QQ << 3Y) = kara -15 pkt

## Flagi

| Flaga | Znaczenie | Warunek |
|-------|-----------|---------|
| `[M]` | Momentum | Rev QQ > 20%, O4K > 15% |
| `[Q]` | Quality | ROE > 20%, Marża > 15% |
| `[S]` | Safe | Debt < 0.35, Coverage > 1.5 |
| `[G]` | GARP | PEG < 1.0 |
| `[A]` | Acceleration | QQ > O4K > 3Y |
| `[!]` | Warning | Debt > 0.6 |
| `[?]` | Verify | Rev QQ > 100% |

## Idealna spółka

Flagi: `[M][Q][S][G][A]`
- Silne momentum
- Wysokiej jakości biznes
- Bezpieczna struktura
- Dobra wycena (GARP)
- Wzrost przyspiesza

## Horyzont

1-3 lata - dopóki momentum trwa

## Ryzyko

⚠️ **Momentum może się skończyć** - gdy:
- Rynek się nasyci
- Konkurencja dogoni
- Cykl się odwróci

Monitoruj flagi `[A]` vs decelerację!
