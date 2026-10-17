# CV Optimizer — lokalna aplikacja Docker v1.2

Aplikacja przeznaczona do uruchomienia na własnym komputerze. Udostępnia edytor profilu, import tekstowego PDF/DOCX, zapisywanie ofert pracy, raport kompetencji oparty na słowniku i dowodach z CV, ręczny edytor wersji, historię, eksport DOCX/PDF i podstawową kontrolę odczytanego tekstu.

## Szybki start z Docker Compose (zalecany)

Wymagany Docker Desktop lub Docker Engine z pluginem Compose oraz internet do jednorazowego pobrania obrazów i pakietów przy budowaniu.

W katalogu głównym (tam gdzie jest `docker-compose.yml`):

```bash
docker compose up --build -d
```

Otwórz: **http://localhost:8080**. Backend dostępny jest wyłącznie wewnątrz sieci Compose, a frontend (Nginx) przekazuje do niego ruch `/api/`. Na hoście aplikacja nasłuchuje tylko pod adresem 127.0.0.1.

Przydatne polecenia:

```bash
docker compose ps
docker compose logs -f
docker compose down                 # zatrzymuje, zachowuje bazę danych
docker compose up -d --build        # aktualizacja obrazów z zachowaniem bazy
```

**Nie używaj `docker compose down -v` bez kopii danych** — to usuwa wolumen SQLite. Nazwa wolumenu: `cv_optimizer_data` (z prefiksem projektu Compose).

Eksport PDF działa w kontenerze backendu (LibreOffice i fonty są dostarczane przez Dockerfile); niczego dodatkowego nie trzeba instalować na hoście.

### Szablony CV

W sekcji **3. Edytor wersji CV** wybierz jeden z trzech bezgrafikowych szablonów:

- **Classic:** wyśrodkowany nagłówek, tradycyjny układ.
- **Editorial:** lewostronny nagłówek, typografia czarno-szara i cienkie separatory sekcji (bez grafik).
- **Compact:** mniejsze marginesy i odstępy do dłuższych CV.

Wszystkie są jednokolumnowe, zachowują tekst do skopiowania i mają zwykłe nagłówki. Nie są gwarancją odczytu przez każdy ATS.

### Podtytuł i linki zawodowe

W **Mój profil → Dane podstawowe** dostępny jest opcjonalny podtytuł, np. `Senior Fullstack Developer`. W **Mój profil → Linki zawodowe** można dodać dowolną liczbę linków z własnymi etykietami, np. `GitHub`, `Portfolio`, `Strona osobista`, `LinkedIn`. Każdy wpis wymaga poprawnego adresu `http://` lub `https://`. Linki można usuwać z profilu. Zapisane wersje CV przechowują własną kopię linków, a w edytorze CV można je modyfikować i usuwać tylko z danej wersji. Pola są opcjonalne i trafiają do wyeksportowanego DOCX/PDF jako zwykły tekst.

**Migracja:** uruchom `docker compose up -d --build` — backend wykona `alembic upgrade head` i przeniesie istniejący `headline` do nowego `subtitle`, nie usuwając starego pola. Dawny identyfikator szablonu `modern` pozostaje obsługiwany jako alias `editorial` przy eksporcie starszych wersji CV.

### Ścieżka kariery — grupowanie ról u tego samego pracodawcy

Zaznacz **Ścieżka kariery — grupuj stanowiska z tej samej firmy** przed zapisaniem wersji CV. Dla tej samej nazwy firmy (bez znaczenia wielkości liter i powielonych spacji) zapisze się jeden nagłówek pracodawcy i lista stanowisk w kolejności od najnowszego. Zachowane są indywidualne okresy i opisy. Ta opcja **nie scala wpisów w bazie** i można ją wyłączyć w następnej wersji CV. Dla różnych nazw prawnych tego samego pracodawcy ujednolić nazwy w profilu przed zapisaniem wersji.

## Wymagania

- Python 3.12+ (testowano w Python 3.13)
- Node.js 20.19+ albo 22.12+ i npm
- LibreOffice w systemowej ścieżce PATH — wymagane tylko do eksportu PDF
- Połączenie z internetem potrzebne przy pierwszej instalacji zależności. Sama aplikacja nie korzysta z zewnętrznego AI ani serwisów online.

## Uruchomienie

Rozpakuj ZIP. W pierwszym terminalu:

```bash
cd cv-optimizer/backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

W drugim terminalu:

```bash
cd cv-optimizer/frontend
npm install
npm run dev
```

Otwórz `http://127.0.0.1:5173`. Dokumentacja REST API: `http://127.0.0.1:8000/docs`.

## Jak korzystać

1. Utwórz profil w zakładce **Mój profil**. Wypełnij doświadczenie, projekty, edukację i umiejętności. Dla umiejętności wpisuj konkretne dowody.
2. W zakładce **CV i analiza ATS** można odczytać dokument PDF/DOCX. Import pokazuje tekst; nie przepisuje samodzielnie danych do profilu.
3. Wklej ofertę i wybierz **Analizuj dopasowanie**. Silnik rozpoznaje wybrane technologie i słowa z ogłoszenia (nie jest to symulacja rzeczywistego ATS).
4. W edytorze popraw nagłówek, podsumowanie i opisy. Zmiany wymagają Twojego zatwierdzenia przez zapis wersji; bazowy profil pozostaje bez zmian.
5. Zapisz wersję CV, pobierz DOCX lub PDF i uruchom **Kontrola tekstu**. PDF wymaga LibreOffice.

## Testy

```bash
cd cv-optimizer/backend
python -m pytest -q
```

Frontend:

```bash
cd cv-optimizer/frontend
npm run build
```

## Ograniczenia

- Brak chmurowego LLM. Porównanie ofert działa na ograniczonym słowniku, ma charakter heurystyczny i nie gwarantuje skuteczności aplikacji do pracy.
- PDF/DOCX: tylko pliki z tekstem; brak OCR dla zeskanowanych obrazów.
- Kontrola ATS sprawdza podstawowe ostrzeżenia, a nie rzeczywisty system Greenhouse/Workday/Lever.
- Import wymaga ręcznego przeniesienia danych. Nie ma automatycznego rozpoznawania wszystkich pól CV.
- Program lokalny, bez uwierzytelniania. Nie wystawiaj serwera na publiczny Internet.
- Nie ma automatycznego pobierania ogłoszeń ani wysyłania CV.
- Autorska punktacja to nie prawdopodobieństwo zatrudnienia.

## Dane i migracje

Przy ręcznym uruchomieniu dane są zapisywane w `backend/data/cvoptimizer.db`. Przy uruchomieniu Docker Compose baza znajduje się w nazwanym wolumenie `cv_optimizer_data` w `/app/data/cvoptimizer.db` w kontenerze backendu. Twórz kopie zapasowe. Dane poprzedniej instalacji lokalnej nie migrują automatycznie do Dockera. Migracje wykonuj z katalogu backend przez `alembic upgrade head`.

## Struktura

- `backend/app/main.py` — FastAPI
- `backend/app/models.py` — modele SQLAlchemy
- `backend/app/optimizer.py` — deterministyczna analiza kompetencji
- `backend/app/documents.py` — import, eksport, lint
- `backend/alembic/versions` — migracje
- `backend/tests` — testy API i integracyjne
- `frontend/src/App.tsx` — profil
- `frontend/src/Workflow.tsx` — oferty, analiza, edytor, historia i eksport

## Weryfikacja wydania

Backend: 11 testów pytest zaliczonych, w tym szablony i grupowanie. W środowisku przygotowania archiwum nie działała usługa pobierania npm, a CLI Dockera nie było dostępne, zatem build frontendu i pełny start Compose **nie zostały zweryfikowane**. Przy pierwszym uruchomieniu użyj `docker compose up --build` i w razie błędu sprawdź `docker compose logs`.

## v1.3 — archiwum LinkedIn i podgląd CV na żywo

W zakładce **Mój profil** wybierz **Import z LinkedIn**. Pobierz własne dane przez ustawienia prywatności LinkedIn i załaduj plik ZIP. Program odczytuje obsługiwane pliki `Positions.csv`, `Education.csv`, `Skills.csv` i `Projects.csv` (jeśli znajdują się w archiwum). Najpierw pokazuje listę rozpoznanych rekordów z możliwością odznaczenia, następnie zapisuje tylko zatwierdzone wpisy. Nie wymaga logowania do LinkedIn i nie korzysta z jego API.

Powtórny import nie dodaje rozpoznanych duplikatów. W przypadku nieobsługiwanych lub błędnych dat rekord może zostać pominięty z ostrzeżeniem. Zawartość archiwum nie jest zapisywana na dysku przez importera. Limit pliku ZIP to 15 MB; limit danych po rozpakowaniu to 22 MB.

W zakładce **CV i analiza ATS** dostępny jest orientacyjny podgląd A4 wariantów Classic, Editorial i Compact, uwzględniający ścieżkę kariery. Podgląd HTML nie jest identyczny z układem generowanym przez LibreOffice, dlatego końcowy PDF należy sprawdzić przed wysyłką.

Aktualizacja wersji Docker: w katalogu projektu uruchom `docker compose up --build -d`. Nie używaj `docker compose down -v`, jeśli chcesz zachować dane w wolumenie.

## v1.4 — diagnostyka techniczna ATS na żądanie

W **Historii, kontroli i eksporcie** zapisz CV, a następnie użyj przycisku **Sprawdź Greenhouse / Workday / Lever**. Test uruchamia się **wyłącznie na kliknięcie**, nigdy przy wpisywaniu zmian. Testuje wygenerowany DOCX, tworzy PDF za pomocą LibreOffice i sprawdza możliwość odczytu oraz zgodność tekstu obu plików.

Panel pokazuje osobne autorskie profile ryzyka technicznego dla trzech systemów, wraz z wynikami każdej reguły, linkiem do dokumentacji i udziałem reguł rzeczywiście przetestowanych. Punkty i wagi są heurystyką CV Optimizera, **nie oceną wystawianą przez producentów ATS**. Nie zapewniają wiernej emulacji ich parserów ani możliwości przewidzenia odrzucenia CV. Istnieje również możliwość wywołania `POST /api/v1/resumes/{id}/ats-check?format=docx` bez LibreOffice (wyniki kontroli PDF będą wtedy nieznane).

Podstawowe kontrole: poprawność ekstrakcji tekstu, e-mail, standardowe nagłówki, obecność dat, tabele/grafiki/pola tekstowe, dane kontaktowe w nagłówkach/stopkach, limit rozmiaru Greenhouse, ekstrakcja PDF i zgodność tokenów DOCX→PDF. Parametry i ograniczenia kontrolowane są w `backend/app/ats_diagnostics.py`.

Źródła: https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse , https://doc.workday.com/admin-guide/en-us/human-capital-management/recruiting/candidates/set-up-prospects-and-candidates/hdc1552497830785.html , https://help.lever.co/s/article/Understanding-Resume-Parsing . Nie wszystkie heurystyki są wymaganiami tych dostawców.

## v1.5 — Historia ATS i przywracanie wersji CV

- Wyniki kontroli Greenhouse / Workday / Lever są zapisywane w SQLite **tylko po ręcznym uruchomieniu** przycisku „Sprawdź Greenhouse / Workday / Lever”.
- W sekcji „Historia diagnostyki ATS” wybierz dwa raporty tego samego formatu (`PDF` lub `DOCX`) i kliknij „Porównaj raporty”. Zobaczysz różnice ocen i zmiany statusów poszczególnych testów. Porównania między formatami są celowo blokowane.
- Przycisk „Przywróć jako nową wersję” tworzy kopię wskazanej wersji CV i oznacza jej pochodzenie. **Nie usuwa ani nie nadpisuje późniejszych wersji**. Zapisane raporty pozostają zachowane. Po przywróceniu uruchom diagnostykę ponownie, jeśli potrzebujesz raportu nowego identyfikatora.
- API: `GET /api/v1/profiles/{profile_id}/ats-history`, `GET /api/v1/resumes/{resume_id}/ats-history`, `GET /api/v1/ats-reports/compare?before_id=...&after_id=...`, `POST /api/v1/resumes/{resume_id}/restore`.
- Migracja `0004` wprowadza tabelę `ats_reports` i pole `restored_from_id`. Backend stosuje ją automatycznie przy starcie kontenera.

### Aktualizacja wersji Docker

Zrób kopię zapasową wolumenu bazy przed aktualizacją i uruchom `docker compose up --build -d` z katalogu projektu. Nie używaj `docker compose down -v`, ponieważ usuwa wolumeny. Kompletna kompilacja frontendu i start kontenerów wymagają weryfikacji lokalnej — środowisko budowania tej paczki nie ma dostępnych zależności React ani silnika Docker.

## v1.6: porównanie zawartości dwóch wersji CV

W sekcji **Historia, kontrola i eksport** dostępny jest panel **Porównanie treści CV (Diff)**. Wybierz wcześniejszą i późniejszą wersję, następnie kliknij **Porównaj treść**. Zmiany są oznaczone kolorami: czerwonym (usunięto) i zielonym (dodano), z podziałem na pola profilu, doświadczenie, projekty i umiejętności. Odczyt porównania nie przelicza ATS ani nie modyfikuje zapisanych CV.

Endpoint: `GET /api/v1/resumes/compare-content?before_id=<UUID>&after_id=<UUID>` (obie wersje muszą należeć do tego samego profilu).

**Przywróć jako nową wersję** pozostaje osobną operacją, która nie kasuje istniejących wersji ani raportów ATS. Porównanie dotyczy zapisanej treści JSON, a nie wizualnego obrazu PDF; różnice w układzie stron wymagają osobnej kontroli eksportów.

Uruchomienie / aktualizacja: `docker compose up --build -d`. Zachowaj wolumen bazy danych, nie stosuj `docker compose down -v`.

## v1.7 — English UI and AI review (GPT / Claude)

The application interface, A4 preview, and generated CV section headings use English. Existing profile data is preserved exactly as entered: changing the language does **not** translate previously saved free-text content. Translate those fields manually before exporting an English CV.

Optional external AI review is available under **Job Analysis > AI CV Review**. Save/select a job posting, select OpenAI GPT or Anthropic Claude, acknowledge the data-sharing consent, and click **Run AI review**. It is never run on every keystroke, and suggestions are **not** applied automatically. ATS compatibility diagnostics remain a separate manual action.

Copy `.env.example` to `.env` at the repository root and enter one or both credentials. Docker Compose passes these values only to the backend:

```
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4.1-mini
ANTHROPIC_API_KEY=your-key
ANTHROPIC_MODEL=claude-sonnet-4-5
```

Run `docker compose up --build -d`. Available provider models and API pricing may change; update model IDs if your account does not have access. External API calls require internet access and may incur provider charges. Name, direct contact data, location, and links are omitted by the AI payload allowlist, but **professional free-text fields can still contain personal data**; review them before opting in. Do not expose the unauthenticated local backend publicly. API errors do not reveal API key values. API results are displayed only and are not persisted as accepted CV changes.
