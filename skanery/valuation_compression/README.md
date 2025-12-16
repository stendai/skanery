# Valuation Compression

## Cel modelu

Identyfikacja spółek gdzie **wycena się kompresuje** (P/E i P/BV spadają r/r), co może oznaczać:
- Zyski rosną szybciej niż cena akcji
- Rynek nie nadąża z wyceną poprawy fundamentów
- Potencjał do re-ratingu (wzrostu mnożników)

## Inspiracje

- **Mean Reversion** - wyceny wracają do średniej sektorowej
- **Earnings Momentum → Price Lag** - cena reaguje z opóźnieniem
- **PEG Ratio Logic** - spadający P/E przy wzroście zysków = okazja
- **Dogs of the Dow** - zbite spółki często odbijają

## Filozofia

> "Kupuj gdy wycena spada, ale biznes się poprawia"

Kluczowe założenie: **spadek P/E r/r** może oznaczać:
1. ✅ **Dobre:** Zyski rosną szybciej niż cena → undervalued
2. ❌ **Złe:** Cena spada bo biznes się pogarsza → value trap

Dlatego łączymy kompresję wyceny z:
- Potwierdzeniem trendu (k/k wspiera r/r)
- Absolutną wartością (P/BV, EV/EBITDA)
- Filtrem bezpieczeństwa (nie ekstremalne przypadki)

## Komponenty scoringu

| Komponent | Waga | Opis |
|-----------|------|------|
| P/E Compression | 30% | Spadek P/E r/r |
| P/BV Compression | 25% | Spadek P/BV r/r |
| Trend Confirmation | 20% | k/k potwierdza r/r |
| Absolute Value | 15% | Aktualne P/BV i EV/EBITDA |
| Safety Check | 10% | Unikanie ekstremalnych przypadków |

## Scoring szczegółowy

### P/E Compression (30%)

**Spadek P/E r/r (im bardziej ujemny, tym lepiej - do pewnego momentu):**

| P/E r/r | Score | Komentarz |
|---------|-------|-----------|
| > +20% | 10 | Drożeje - źle |
| +10% do +20% | 25 | Lekko drożeje |
| 0% do +10% | 40 | Stabilna |
| -10% do 0% | 55 | Lekka kompresja |
| **-20% do -10%** | **75** | **Dobra kompresja** |
| **-40% do -20%** | **100** | **Sweet spot** |
| **-60% do -40%** | **100** | **Sweet spot** |
| -80% do -60% | 80 | Silna kompresja |
| < -80% | 50 | Ekstremalna - sprawdź! |

### P/BV Compression (25%)

| P/BV r/r | Score | Komentarz |
|----------|-------|-----------|
| > +10% | 15 | Drożeje |
| 0% do +10% | 35 | Stabilna |
| -10% do 0% | 55 | Lekka kompresja |
| **-20% do -10%** | **85** | **Dobra** |
| **-35% do -20%** | **100** | **Sweet spot** |
| -50% do -35% | 75 | Silna |
| < -50% | 50 | Ekstremalna |

### Trend Confirmation (20%)

Sprawdzamy czy **k/k potwierdza r/r**:

| Sytuacja | Score | Komentarz |
|----------|-------|-----------|
| k/k < r/r < 0 | 100 | Kompresja przyspiesza! |
| k/k < 0, r/r < 0 | 85 | Trend potwierdzony |
| k/k > 0, r/r < 0 | 60 | Odbicie w krótkim terminie |
| k/k < 0, r/r > 0 | 50 | Nowy trend spadkowy? |
| k/k > 0, r/r > 0 | 25 | Drożeje - źle |

### Absolute Value (15%)

**P/BV (50%):**
| P/BV | Score |
|------|-------|
| < 0.5 | 70 | Value trap risk |
| 0.5-1.0 | 100 | Poniżej book value |
| 1.0-1.5 | 90 | Tania |
| 1.5-2.5 | 70 | OK |
| 2.5-4.0 | 50 | Droga |
| > 4.0 | 30 | Bardzo droga |

**EV/EBITDA (50%):**
| EV/EBITDA | Score |
|-----------|-------|
| < 3 | 90 | Bardzo tania |
| 3-5 | 100 | Sweet spot |
| 5-8 | 80 | OK |
| 8-12 | 50 | Droga |
| > 12 | 30 | Bardzo droga |

### Safety Check (10%)

Filtr bezpieczeństwa - kara za ekstremalne wartości:

| Sytuacja | Kara |
|----------|------|
| P/E r/r < -90% | -30 pkt |
| P/BV r/r < -50% | -20 pkt |
| P/BV < 0.3 | -20 pkt (value trap) |
| EV/EBITDA < 1 | -20 pkt (kryzys?) |

## Flagi

| Flaga | Znaczenie | Warunek |
|-------|-----------|---------|
| `[C]` | Compression | P/E r/r < -30% i P/BV r/r < -15% |
| `[V]` | Value | P/BV < 1.0 lub EV/EBITDA < 5 |
| `[A]` | Acceleration | k/k < r/r (kompresja przyspiesza) |
| `[D]` | Deep Compression | P/E r/r < -50% i P/BV r/r < -25% |
| `[T]` | Trend Confirmed | k/k i r/r oba negatywne |
| `[!]` | Warning | Ekstremalne wartości |
| `[?]` | Verify | P/E r/r > 0 (wycena rośnie) |

## Idealna spółka

Flagi: `[C][V][A][T]`
- Kompresja wyceny (P/E i P/BV spadają r/r)
- Aktualna wycena atrakcyjna (value)
- Kompresja przyspiesza (k/k < r/r)
- Trend potwierdzony (oba kierunki zgodne)

## Kiedy model działa najlepiej?

- **Po korekcie rynkowej** - dobre spółki zbite z całym rynkiem
- **Earnings season** - zyski lepsze od oczekiwań, cena nie nadąża
- **Sector rotation** - pieniądze wychodzą z sektora tymczasowo
- **Small/mid caps** - mniej analityków, wolniejszy re-rating

## Kiedy uważać?

⚠️ **Value trap** - sprawdź czy spadek wyceny nie wynika z:
- Pogorszenia fundamentów
- Problemów branżowych
- Złego zarządzania
- Jednorazowych zysków w poprzednim roku

## Najlepsze połączenia z innymi modelami

| Kombinacja | Interpretacja |
|------------|---------------|
| Valuation Compression + Quality Growth | Zdrowy biznes, tanieje → ideał |
| Valuation Compression + Revenue Momentum | Przychody rosną, wycena spada → undervalued |
| Valuation Compression + Cash Quality | Solidny bilans, tanieje → bezpieczny value |
| Valuation Compression + Turnaround | Double confirmation dla contrarian play |

## Horyzont

3-12 miesięcy - czekasz na re-rating wyceny

## Dane wejściowe

BiznesRadar.pl - skaner z kolumnami:
- Cena/Wartość księgowa k/k, r/r
- Cena/Zysk k/k, r/r
- EV/EBITDA
