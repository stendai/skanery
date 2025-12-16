# TODO - GPW Screener

## Status projektu

**Wersja:** 1.3  
**Ostatnia aktualizacja:** 2025-12-16

---

## ✅ Zrobione (v1.0)

### Struktura
- [x] Modularna struktura - każdy model w osobnym folderze
- [x] Centralny folder `dane/` - dane w jednym miejscu
- [x] Config YAML dla każdego modelu
- [x] README.md z dokumentacją per model
- [x] Główny README.md projektu

### Modele
- [x] **Quality Growth** - wzrost EBIT, jakość biznesu (Buffett/Lynch)
- [x] **Turnaround** - deep value, contrarian (Graham)
- [x] **Revenue Momentum & Safety** - GARP + Piotroski + CANSLIM

### Funkcjonalności
- [x] `run.py` - uruchamia wszystkie skanery
- [x] `run.py --list` - lista skanerów
- [x] `run.py --only X Y` - wybrane skanery
- [x] Autodiscovery skanerów
- [x] Timestamp w nazwach plików wyników
- [x] Archiwizacja starych wyników (`main/archive/`)
- [x] `wyniki_latest.xlsx` - zawsze najnowsze
- [x] Logging do pliku i konsoli
- [x] Walidacja wymaganych kolumn
- [x] Normalizacja score do 0-100
- [x] Flagi jako lista (do filtrowania programowego)
- [x] `app.py --consensus` - spółki wysoko we wszystkich modelach

---

## ✅ Zrobione (v1.1)

### Nowy model
- [x] **Cash Quality & Balance Sheet** - jakość zysków (cash conversion) + solidny bilans
  - [x] config.yaml
  - [x] model.py
  - [x] README.md
  - [x] Dane: biznesradar_cq.txt

### Aktualizacje base.py
- [x] Mapowanie nagłówków dla Cash Quality:
  - `Udział zysku netto w przepływach operacyjnych r/r` → `Cash_Conv`
  - `I stopień pokrycia` → `Coverage_I`
  - `Płynność bieżąca` → `Current_Ratio`
- [x] Dodanie nowych kolumn do konwersji (procentowe/numeryczne)

### Dokumentacja
- [x] Aktualizacja głównego README.md
- [x] Aktualizacja TODO.md

---

## ✅ Zrobione (v1.2)

### Nowy model
- [x] **Quality Momentum** - stabilna poprawa wyników (nie jednorazowe skoki)
  - [x] config.yaml
  - [x] model.py
  - [x] README.md
  - [x] Dane: biznesradar_qm.txt

### Filozofia modelu
- Sweet spot scoring - najwyższy score dla umiarkowanych wzrostów (30-80% r/r)
- Kara za ekstremalne skoki (+500%) - często jednorazowe/z niskiej bazy
- Trend confirmation - k/k musi potwierdzać r/r
- 5 komponentów: Profitability Momentum, Margin Momentum, Trend Confirmation, Revenue Support, Value

### Aktualizacje base.py
- [x] Mapowanie nagłówków dla Quality Momentum:
  - `Marża zysku operacyjnego k/k` → `Margin_Op_QQ`
  - `Marża zysku operacyjnego r/r` → `Margin_Op_YY`
  - `Marża zysku netto k/k` → `Margin_Net_QQ`
  - `Marża zysku netto r/r` → `Margin_Net_YY`
  - `Przychody ze sprzedaży kwart r/r` → `Rev_YY`
- [x] Dodanie nowych kolumn do konwersji procentowych

### Dokumentacja
- [x] Aktualizacja głównego README.md
- [x] Aktualizacja TODO.md

---

## ✅ Zrobione (v1.3)

### Nowy model
- [x] **Valuation Compression** - spółki ze spadającą wyceną przy rosnących zyskach
  - [x] config.yaml
  - [x] model.py
  - [x] README.md
  - [x] Dane: biznesradar_vc.txt

### Filozofia modelu
- Szukamy kompresji wyceny (P/E i P/BV spadają r/r)
- Sweet spot: P/E r/r -20% do -60%, P/BV r/r -10% do -35%
- Kara za ekstremalne spadki (< -80%) - może być kryzys
- Trend confirmation - k/k potwierdza r/r
- 5 komponentów: P/E Compression, P/BV Compression, Trend Confirmation, Absolute Value, Safety Check

### Aktualizacje base.py
- [x] Mapowanie nagłówków dla Valuation Compression:
  - `Cena / Wartość księgowa k/k` → `P_BV_QQ`
  - `Cena / Wartość księgowa r/r` → `P_BV_YY`
  - `Cena / Zysk k/k` → `P_E_QQ`
  - `Cena / Zysk r/r` → `P_E_YY`
  - `EV / EBITDA` → `EV_EBITDA`
- [x] Dodanie nowych kolumn do konwersji (procentowe + numeryczne)

### Dokumentacja
- [x] Aktualizacja głównego README.md
- [x] Aktualizacja TODO.md

---

## 🔨 Do zrobienia (v1.4)

### Wysoki priorytet

#### Testy
- [ ] Folder `tests/`
- [ ] Test: czy model się odpala na przykładowych danych
- [ ] Test: czy score jest w zakresie 0-100
- [ ] Test: czy wymagane kolumny są w outputcie
- [ ] Test: czy flagi się generują poprawnie
- [ ] Przykładowe dane testowe (mały plik ~10 spółek)

#### Cache danych
- [ ] Cache sparsowanych danych (pickle/parquet)
- [ ] Sprawdzanie czy dane się zmieniły (hash pliku)
- [ ] Opcja `--no-cache` w run.py

### Średni priorytet

#### Nowe modele
- [ ] **Dividend** - spółki dywidendowe (DY, payout ratio, stabilność)
- [ ] **Momentum Price** - momentum cenowe (52w high, RSI proxy)
- [ ] **Small Cap Growth** - małe spółki z potencjałem
- [ ] **Piotroski F-Score** - pełna implementacja 9 kryteriów

#### Historia i tracking
- [ ] Śledzenie zmian rankingu w czasie
- [ ] Alerty: "spółka X wskoczyła do TOP 10"
- [ ] Alerty: "spółka Y wypadła z TOP 10"
- [ ] Wykres historii rankingu dla spółki

#### Meta-scoring / Consensus
- [ ] Weighted consensus (różne wagi dla różnych modeli)
- [ ] Percentyle zamiast rankingu
- [ ] "Confidence score" - ile modeli się zgadza

### Niski priorytet

#### Pakiet Python
- [ ] `setup.py` / `pyproject.toml`
- [ ] Instalacja przez `pip install -e .`
- [ ] Usunięcie `sys.path.insert` hacków

#### Wizualizacja (app.py)
- [ ] Heatmapa: spółki vs modele
- [ ] Wykres radarowy dla spółki
- [ ] Eksport do HTML
- [ ] Eksport do PDF

#### Integracje
- [ ] Automatyczne pobieranie danych z BiznesRadar (scraping)
- [ ] API do odpytywania wyników
- [ ] Webhook/notyfikacje (Telegram, email)

---

## 💡 Pomysły na przyszłość

### Nowe źródła danych
- Stooq.pl
- GPW API
- Yahoo Finance (dla porównania z zagranicznymi)

### Machine Learning
- Predykcja które spółki z TOP 10 faktycznie urosną
- Backtesting modeli na danych historycznych
- Optymalizacja wag automatycznie

### UI
- Prosta aplikacja webowa (Streamlit/Gradio)
- Dashboard z wykresami
- Filtrowanie interaktywne

---

## 🐛 Znane problemy

1. **Encoding danych** - pliki z BiznesRadar mają różne kodowanie (UTF-8 vs Windows-1250). Parser radzi sobie, ale może być kruchy.

2. **Brak P/EBIT w dane_2** - model Revenue Momentum nie ma tej kolumny, używa tylko P/E.

3. **Hardcoded thresholds** - progi scoringu (np. ROE > 25%) są zahardcodowane w model.py, powinny być w config.yaml.

---

## 📝 Decyzje projektowe

### Dlaczego YAML a nie JSON dla configów?
- Czytelniejszy dla człowieka
- Komentarze
- Multiline strings

### Dlaczego normalizacja 0-100?
- Porównywalność między modelami
- Intuicyjne ("score 85" vs "score 67.3")
- Consensus łatwiejszy do obliczenia

### Dlaczego osobne pliki danych per "typ" skanera?
- BiznesRadar ma różne skanery z różnymi kolumnami
- Quality Growth potrzebuje innych danych niż Revenue Momentum
- Łatwiejsze zarządzanie

### Dlaczego flagi jako string "[Q][G][V]" a nie lista?
- Czytelność w Excel
- Ale mamy też `Flags_List` jako listę do filtrowania w kodzie

### Dlaczego Quality Momentum karze ekstremalne wzrosty?
- Wzrost +1000% r/r to często:
  - Niska baza (rok temu ROE 0.5%, teraz 5%)
  - Jednorazowy event (sprzedaż aktywów)
  - Mean reversion - wróci do normy
- Wzrost 30-80% r/r to często:
  - Systematyczna poprawa biznesu
  - Powtarzalny trend
  - Mniejsze ryzyko

### Dlaczego Valuation Compression szuka spadających wycen?
- Spadek P/E r/r może oznaczać:
  - ✅ Zyski rosną szybciej niż cena → undervalued
  - ❌ Cena spada bo biznes się pogarsza → value trap
- Dlatego łączymy z:
  - Trend confirmation (k/k potwierdza)
  - Absolute value (P/BV, EV/EBITDA)
  - Safety check (filtr ekstremalnych)

---

## 🔖 Changelog

### v1.3 (2025-12-16)
- **NOWY MODEL:** Valuation Compression
  - Kompresja wyceny (P/E i P/BV spadają r/r)
  - Sweet spot: P/E r/r -20% do -60%, P/BV r/r -10% do -35%
  - Kara za ekstremalne spadki (możliwy kryzys)
  - Trend confirmation (k/k vs r/r)
  - 5 komponentów: P/E Comp, P/BV Comp, Trend, Absolute Value, Safety
  - Flagi: [C], [V], [A], [D], [T], [!], [?]
- Aktualizacja base.py o nowe mapowania nagłówków
- Aktualizacja dokumentacji

### v1.2 (2025-12-15)
- **NOWY MODEL:** Quality Momentum
  - Stabilna poprawa wyników (sweet spot 30-80% r/r)
  - Kara za ekstremalne skoki (+500%)
  - Trend confirmation (k/k vs r/r)
  - 5 komponentów: Profitability, Margin, Trend, Revenue, Value
  - Flagi: [Q], [M], [A], [R], [V], [!], [?]
- Aktualizacja base.py o nowe mapowania nagłówków
- Aktualizacja dokumentacji

### v1.1 (2025-12-15)
- **NOWY MODEL:** Cash Quality & Balance Sheet
  - Jakość zysków (cash conversion)
  - Solidność bilansu (zadłużenie, płynność, pokrycie)
  - Rentowność (ROE, ROA, marża)
  - Wycena (P/E)
- Aktualizacja base.py o nowe mapowania nagłówków
- Aktualizacja dokumentacji

### v1.0 (2025-12-15)
- Pierwsza wersja
- 3 modele: Quality Growth, Turnaround, Revenue Momentum
- Modularna struktura
- Config YAML
- Logging
- Archiwizacja
- Consensus

---

## 📊 Podsumowanie modeli (v1.3)

| Model | Dane | Komponenty | Flagi |
|-------|------|------------|-------|
| Quality Growth | biznesradar_qg.txt | Quality, Growth, RevConfirm, Value, PBV | [Q][G][V][R][!][?] |
| Turnaround | biznesradar_qg.txt | Value, Quality, Contrarian, DeepValue | [D][Q][T][S] |
| Revenue Momentum | biznesradar_rms.txt | Momentum, Quality, Safety, Value, Consistency | [M][Q][S][G][A][!][?] |
| Cash Quality | biznesradar_cq.txt | CashQuality, Balance, Profitability, Value | [C][B][Q][V][L][!][?] |
| Quality Momentum | biznesradar_qm.txt | ProfitMom, MarginMom, Trend, Revenue, Value | [Q][M][A][R][V][!][?] |
| Valuation Compression | biznesradar_vc.txt | PE_Comp, PBV_Comp, Trend, AbsValue, Safety | [C][V][A][D][T][!][?] |

**Łącznie: 6 modeli aktywnych**
