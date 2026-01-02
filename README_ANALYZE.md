# 📊 Company Analyzer - README

## Opis

Skrypt `analyze.py` generuje interaktywne raporty HTML z analizą finansową spółek na podstawie danych z BiznesRadar i ręcznie przygotowanego kontekstu z raportów kwartalnych.

## Wymagania

```bash
pip install pandas matplotlib PyPDF2 python-docx
```

## Struktura folderów

```
raporty/
└── {ticker}/                              # np. gen/
    ├── {ticker}_bilans_YYYY_Q.txt         # Bilans z BiznesRadar
    ├── {ticker}_rzis_YYYY_Q.txt           # RZiS z BiznesRadar
    ├── {ticker}_przeplywy_YYYY_Q.txt      # Cash Flow z BiznesRadar
    ├── {ticker}_kontekst.txt              # Ręczny kontekst (WAŻNE!)
    ├── {ticker}_YYYY_Q.pdf                # Raport kwartalny ESPI
    ├── {ticker}_*.docx                    # Dodatkowe analizy (załączniki)
    └── {ticker}_raport_analityczny.html   # ← OUTPUT
```

### Przykład dla Genomed Q3 2025:

```
raporty/gen/
├── gen_bilans_2025_3.txt
├── gen_rzis_2025_3.txt
├── gen_przeplywy_2025_3.txt
├── gen_kontekst.txt
├── gen_2025_3.pdf
├── gen_Cross_Market_Analysis_Q3_2025.docx
└── gen_raport_analityczny.html
```

## Użycie

```bash
# Interaktywne (pyta o ticker)
python analyze.py

# Bezpośrednie
python analyze.py GEN
python analyze.py gen
```

## Format pliku `{ticker}_kontekst.txt`

Plik kontekstu to **ręcznie przygotowany wyciąg** z raportu kwartalnego. Claude pomaga go stworzyć na podstawie PDF.

### Struktura:

```
# Komentarze zaczynają się od #
# Źródło: Raport Kwartalny XYZ S.A. za okres...
# Data publikacji: DD.MM.YYYY

[ZATRUDNIENIE]
FTE: 53.2

[AKCJONARIAT]
Nazwa Akcjonariusza 1: 44.46% kapitału / 30.59% głosów
Nazwa Akcjonariusza 2: 20.07% kapitału / 27.45% głosów
Osoba Fizyczna (Prezes): 9.18% kapitału / 12.01% głosów

[KOMENTARZ ZARZĄDU]
Tekst wieloliniowy z kluczowymi informacjami.
Wzrost przychodów o X% dzięki...
Podpisano umowy z:
- Klient 1
- Klient 2
- Klient 3

[INNOWACJE / R&D]
- Projekt 1: opis
- Projekt 2: opis
- Nowa technologia/produkt

[RYZYKA / UWAGI]
- Ryzyko 1 (np. koncentracja akcjonariatu)
- Ryzyko 2 (np. zależność od klienta)
- Uwaga: brak prognoz finansowych
```

### Sekcje (wszystkie opcjonalne):

| Sekcja | Opis |
|--------|------|
| `[ZATRUDNIENIE]` | Liczba FTE z raportu |
| `[AKCJONARIAT]` | Struktura właścicielska >5% |
| `[KOMENTARZ ZARZĄDU]` | Kluczowe info z sekcji 4 raportu |
| `[INNOWACJE / R&D]` | Projekty badawcze, nowe produkty |
| `[RYZYKA / UWAGI]` | Ryzyka inwestycyjne, czerwone flagi |

### Alternatywne nazwy sekcji (obsługiwane):

- `[KOMENTARZ]` zamiast `[KOMENTARZ ZARZĄDU]`
- `[INNOWACJE]` lub `[R&D]` zamiast `[INNOWACJE / R&D]`
- `[RYZYKA]` lub `[UWAGI]` zamiast `[RYZYKA / UWAGI]`

## Co generuje raport HTML

### 1. KPI Cards
- Przychody (+ YoY%)
- Zysk netto (+ YoY%)
- Gotówka (+ YoY%)
- Marża EBIT / Marża netto
- ROE
- Current Ratio

### 2. Alerty (automatyczne)
- ✅ Silny wzrost przychodów (>20% YoY)
- ✅ Wysoka rentowność (marża >15%)
- ✅ Turnaround (strata → zysk)
- ✅ Wysokie ROE (>20%)
- ✅ Niskie zadłużenie (<30%)
- ✅ Pozytywny FCF
- ⚠️ Niski cash runway (<6 miesięcy)
- ❌ Spadek przychodów (<-10% YoY)
- ❌ Niska płynność (CR <1.0)
- ❌ Wysokie zadłużenie (>50%)

### 3. Wykresy (5 sztuk)
1. **Przychody i Zysk** - bar chart + line (dual axis)
2. **Marże** - EBIT margin, Net margin over time
3. **Gotówka** - Cash position trend
4. **Cash Flow Waterfall** - OCF, ICF, FCF breakdown
5. **Sezonowość** - Box plot Q1/Q2/Q3/Q4

### 4. Kontekst z Raportu (z `_kontekst.txt`)
- 👥 Zatrudnienie
- 💬 Komentarz Zarządu
- 📊 Tabela Akcjonariatu
- 🔬 Innowacje / R&D
- ⚠️ Ryzyka i Uwagi

### 5. Załączniki
- Klikalne linki do PDF i DOCX w folderze
- Automatycznie wykrywa pliki `{ticker}_*.pdf` i `{ticker}_*.docx`

### 6. Dane Historyczne
- Tabela z 8 ostatnimi kwartałami
- Przychody, Zysk, Cash, OCF

## TODO / Przyszłe ulepszenia

### Nowe wykresy:
- [ ] **FCF trend** - Free Cash Flow over time
- [ ] **ROE/ROA trend** - Rentowność w czasie
- [ ] **Debt structure** - Zadłużenie krótko vs długoterminowe
- [ ] **Working capital** - Kapitał obrotowy
- [ ] **DuPont decomposition** - Rozkład ROE

### Nowe metryki:
- [ ] ROIC (Return on Invested Capital)
- [ ] Asset turnover
- [ ] Days Sales Outstanding (DSO)
- [ ] Inventory turnover

### Funkcjonalności:
- [ ] Porównanie z poprzednim kwartałem (QoQ)
- [ ] Eksport do PDF
- [ ] Tryb ciemny w HTML
- [ ] Porównanie wielu spółek side-by-side

## Workflow tworzenia kontekstu

1. **User** uploaduje PDF raportu kwartalnego
2. **Claude** czyta PDF i wypisuje kluczowe info
3. **User** kopiuje do `{ticker}_kontekst.txt`
4. **User** uruchamia `python analyze.py {TICKER}`
5. **Output**: `{ticker}_raport_analityczny.html`

## Przykład sesji z Claude

```
User: [uploaduje gen_2025_3.pdf]
      Wypisz mi kontekst do gen_kontekst.txt

Claude: 
# Kontekst raportu Q3 2025
# Źródło: Raport Kwartalny Genomed S.A.

[ZATRUDNIENIE]
FTE: 53.2

[AKCJONARIAT]
Diagnostyka S.A.: 44.46% kapitału / 30.59% głosów
...

[KOMENTARZ ZARZĄDU]
Wzrost przychodów o 42% r/r...
...
```

## Dane z BiznesRadar

Pliki TXT pobierane z BiznesRadar (zakładki Bilans, RZiS, Przepływy) w formacie tab-separated.

Skrypt automatycznie:
- Obsługuje podwójne taby (`\t\t`)
- Parsuje polskie formatowanie liczb (spacja jako separator tysięcy)
- Mapuje nazwy wierszy na standardowe metryki

## Troubleshooting

### "Nie znaleziono danych finansowych"
- Sprawdź czy pliki mają prefix `{ticker}_` (np. `gen_bilans_...`)
- Sprawdź czy są w folderze `raporty/{ticker}/`

### Brak sekcji kontekstu w HTML
- Sprawdź czy plik `{ticker}_kontekst.txt` istnieje
- Sprawdź format sekcji `[NAZWA]`

### Błędy wykresów
- Zainstaluj matplotlib: `pip install matplotlib`
- Sprawdź czy są dane dla wystarczającej liczby kwartałów

## Autor

Wygenerowane przez Claude (Anthropic) jako narzędzie do analizy spółek GPW.
