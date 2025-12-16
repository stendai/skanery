# TODO - GPW Screener

## Status projektu

**Wersja:** 2.0  
**Ostatnia aktualizacja:** 2025-12-16

---

## ✅ Zrobione (v1.0 - v1.3)

### Struktura
- [x] Modularna struktura - każdy model w osobnym folderze
- [x] Centralny folder `dane/` - dane w jednym miejscu
- [x] Config YAML dla każdego modelu
- [x] README.md z dokumentacją per model
- [x] Główny README.md projektu

### Modele (6 aktywnych)
- [x] **Quality Growth** - wzrost EBIT, jakość biznesu (Buffett/Lynch)
- [x] **Turnaround** - deep value, contrarian (Graham)
- [x] **Revenue Momentum & Safety** - GARP + Piotroski + CANSLIM
- [x] **Cash Quality & Balance Sheet** - jakość zysków + solidny bilans
- [x] **Quality Momentum** - stabilna poprawa wyników
- [x] **Valuation Compression** - spadająca wycena przy rosnących zyskach

### Funkcjonalności run.py
- [x] Autodiscovery skanerów
- [x] `run.py --list` - lista skanerów
- [x] `run.py --only X Y` - wybrane skanery
- [x] Timestamp w nazwach plików wyników
- [x] Archiwizacja starych wyników
- [x] `wyniki_latest.xlsx` - zawsze najnowsze
- [x] Logging do pliku i konsoli
- [x] Walidacja wymaganych kolumn
- [x] Normalizacja score do 0-100
- [x] Flagi jako lista i string

---

## ✅ Zrobione (v2.0) - Signal Aggregation

### Nowy app.py - kompletna przebudowa
- [x] **Signal Aggregation** - agregacja sygnałów z wielu modeli
- [x] **Investment Thesis** - automatyczne generowanie tezy inwestycyjnej
- [x] **Consensus Ranking** - ranking oparty na Signal Strength
- [x] **Flag Heatmap** - macierz spółek vs flag
- [x] **Best Of** - TOP 3 w każdej kategorii
- [x] **Profiles** - szczegółowe profile spółek

### Metryki Signal Aggregation
- [x] **Signal Strength** - główna metryka (combo wszystkich)
- [x] **Coverage** - w ilu modelach występuje
- [x] **Elite Score** - punkty za TOP5/TOP10/TOP20
- [x] **Flag Density** - średnia flag na model
- [x] **Warning Count** - liczba ostrzeżeń
- [x] **Category Strength** - siła w kategoriach (Quality, Value, etc.)

### Komendy app.py
- [x] `python app.py` - generuje wyniki_ostateczne.xlsx
- [x] `python app.py --top N` - TOP N w konsoli
- [x] `python app.py --ticker XYZ` - profil spółki
- [x] `python app.py --status` - status systemu
- [x] `python app.py --no-save` - bez zapisu

### Kategoryzacja flag
- [x] Quality: [Q]
- [x] Growth: [G], [R]
- [x] Value: [V], [D]
- [x] Momentum: [M], [A]
- [x] Safety: [S], [B], [L]
- [x] Cash: [C]
- [x] Turnaround: [T]
- [x] Warning: [!], [?]

### Dokumentacja
- [x] Aktualizacja README.md
- [x] Aktualizacja TODO.md

---

## 🔨 Do zrobienia (v2.1)

### Wysoki priorytet

#### Portfolio Health Check
- [ ] `python app.py --check AAA BBB CCC` - sprawdź pozycje portfela
- [ ] Ostrzeżenie gdy spółka poza TOP50
- [ ] Porównanie z poprzednim snapshoteм

#### Filtrowanie
- [ ] `python app.py --rynek GPW` - tylko główny parkiet
- [ ] `python app.py --min-coverage 3` - minimum 3 modele
- [ ] `python app.py --no-warnings` - bez spółek z [!][?]

#### Eksport
- [ ] Eksport consensus do CSV
- [ ] Eksport do Markdown (do notatek)

### Średni priorytet

#### Testy
- [ ] Folder `tests/`
- [ ] Test: czy model się odpala
- [ ] Test: czy score w zakresie 0-100
- [ ] Test: czy Signal Strength się liczy poprawnie
- [ ] Przykładowe dane testowe

#### Cache danych
- [ ] Cache sparsowanych danych (pickle/parquet)
- [ ] Sprawdzanie czy dane się zmieniły (hash)
- [ ] Opcja `--no-cache`

#### Nowe modele
- [ ] **Dividend** - spółki dywidendowe
- [ ] **Momentum Price** - momentum cenowe
- [ ] **Small Cap Growth** - małe spółki z potencjałem
- [ ] **Piotroski F-Score** - pełna implementacja

### Niski priorytet

#### Historia i tracking
- [ ] `python app.py --portfolio` - zapisz snapshot TOP10
- [ ] `python app.py --performance` - porównaj z historią
- [ ] Alerty: "spółka X wskoczyła do TOP 10"
- [ ] Wykres historii rankingu

#### Wizualizacja
- [ ] Heatmapa graficzna (matplotlib/plotly)
- [ ] Wykres radarowy dla spółki
- [ ] Eksport do HTML
- [ ] Eksport do PDF

#### Pakiet Python
- [ ] `setup.py` / `pyproject.toml`
- [ ] Instalacja przez `pip install -e .`

---

## 💡 Pomysły na przyszłość

### Integracje
- [ ] Automatyczne pobieranie danych z BiznesRadar (scraping)
- [ ] Śledzenie ESPI (pozytywne zaskoczenia)
- [ ] Webhook/notyfikacje (Telegram)

### Machine Learning
- [ ] Predykcja które spółki z TOP 10 faktycznie urosną
- [ ] Backtesting modeli na danych historycznych
- [ ] Optymalizacja wag automatycznie

### UI
- [ ] Prosta aplikacja webowa (Streamlit)
- [ ] Dashboard z wykresami
- [ ] Filtrowanie interaktywne

---

## 🐛 Znane problemy

1. **Encoding danych** - pliki z BiznesRadar mają różne kodowanie
2. **MODEL_THEMES zawiera 7 wpisów** - ale mamy 6 modeli (jeden wpis to skrócona nazwa)
3. **Skrócona nazwa arkusza** - "Cash Quality & Balance She" zamiast pełnej

---

## 📝 Decyzje projektowe

### Dlaczego Signal Aggregation zamiast prostego średniego rankingu?

Prosty średni ranking:
- Spółka #1 w 1 modelu, #50 w 5 innych = średnia #41
- Nie łapie "specialist" spółek

Signal Aggregation:
- Punkty za TOP5 (5pkt), TOP10 (3pkt), TOP20 (1pkt)
- Spółka #1 w 1 modelu = 5pkt, nawet jeśli gdzie indziej nie występuje
- Łapie zarówno "broad appeal" jak i "specialist" spółki

### Dlaczego Investment Thesis?

- Szybka orientacja co model widzi w spółce
- Automatyczne podsumowanie bez czytania wszystkich szczegółów
- Kategoryzacja (QUALITY, VALUE, MOMENTUM, etc.) ułatwia porównania

### Dlaczego Category Strength?

- Spółka może mieć wiele flag [Q][Q][Q] w różnych modelach
- To silniejszy sygnał jakości niż jedna [Q]
- Wagi kategorii (quality: 1.5, safety: 1.4, etc.) odzwierciedlają preferencje

---

## 📊 Podsumowanie modeli (v2.0)

| Model | Dane | Główne flagi | Cel |
|-------|------|--------------|-----|
| Quality Growth | biznesradar_qg.txt | [Q][G][R] | Wzrost EBIT |
| Turnaround | biznesradar_qg.txt | [D][T][S] | Deep value |
| Revenue Momentum | biznesradar_rms.txt | [M][S][G][A] | GARP + Safety |
| Cash Quality | biznesradar_cq.txt | [C][B][L][Q] | Jakość zysków |
| Quality Momentum | biznesradar_qm.txt | [Q][M][A][R] | Stabilna poprawa |
| Valuation Compression | biznesradar_vc.txt | [C][V][D][T] | Kompresja wyceny |

**Łącznie: 6 modeli aktywnych**

---

## 🔖 Changelog

### v2.0 (2025-12-16)
- **NOWY APP.PY:** Kompletna przebudowa z Signal Aggregation
  - Consensus ranking oparty na Signal Strength
  - Automatyczne Investment Thesis
  - Flag Heatmap
  - Best Of w kategoriach
  - Profile spółek
- Komendy: `--top N`, `--ticker XYZ`, `--status`, `--no-save`
- Kategoryzacja flag (Quality, Value, Momentum, Safety, etc.)
- Wagi kategorii dla thesis clarity
- wyniki_ostateczne.xlsx z 4 arkuszami
- Aktualizacja dokumentacji

### v1.3 (2025-12-16)
- Model: Valuation Compression

### v1.2 (2025-12-15)
- Model: Quality Momentum

### v1.1 (2025-12-15)
- Model: Cash Quality & Balance Sheet

### v1.0 (2025-12-15)
- Pierwsza wersja
- 3 modele: Quality Growth, Turnaround, Revenue Momentum
- Modularna struktura
- app.py --consensus (stara wersja)

---

## 🎯 Następne kroki (sugerowane)

1. **Teraz:** Przetestuj app.py na swoich danych
2. **Ten tydzień:** Dodaj `--check` dla portfolio health
3. **Ten miesiąc:** Dodaj filtrowanie `--rynek GPW`
4. **Q1 2026:** Dodaj tracking historii i performance
