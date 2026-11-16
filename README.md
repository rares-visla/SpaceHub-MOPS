# SpaceHub

Portal web pentru explorarea arhivelor vizuale NASA.
Stack: **Django REST Framework + SQLite** (backend), **React + Vite** (frontend),
**pytest + pytest-cov** și **Vitest** (teste).

## Stories implementate (rol: vizitator)

| ID   | Story                  | Backend                                   | Frontend                                 |
|------|------------------------|-------------------------------------------|------------------------------------------|
| US01 | Vizualizare APOD       | `GET /api/apod/`                          | `pages/Home.jsx`                         |
| US02 | Căutare imagini        | `GET /api/images/search/?q=`              | `components/SearchBar.jsx`, `pages/Search.jsx`, `components/ImageGrid.jsx` |
| US03 | Detalii imagine        | `GET /api/images/<nasa_id>/`, `GET /api/apod/?date=` | `pages/ImageDetail.jsx`, `pages/ApodDetail.jsx`, `components/DetailView.jsx` |
| US10 | Filtrare după an       | `...search/?year_start=&year_end=`        | `components/SearchBar.jsx`               |
| US15 | Partajare link         | (pagina de detalii este publică)          | `components/CopyLinkButton.jsx`          |
| US16 | Descărcare imagine     | `GET /api/images/<nasa_id>/download/`, `GET /api/apod/download/` | butonul „Download image” din `DetailView.jsx` |

## Pornire

### Backend (terminal 1)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver         # http://127.0.0.1:8000
```

Nu este nevoie de cheie NASA: nici APOD, nici căutarea de imagini nu cer cheie.

> **APOD și API-ul nou.** Pe 29 septembrie 2026 NASA a mutat APOD pe science.nasa.gov.
> Vechiul `api.nasa.gov/planetary/apod` încă răspunde, dar cu titlul „NASA Science” și
> logo-ul NASA în loc de imagine. Proiectul citește
> `science.nasa.gov/wp-json/wp/v2/apod-basic` (vezi `gallery/nasa_client.py`).

### Frontend (terminal 2)

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Vite trimite cererile `/api/...` către Django (vezi `vite.config.js`).

## Teste

```bash
cd backend && pytest               # teste + raport de coverage (pytest-cov)
cd frontend && npm test            # teste de componentă / criterii de acceptare
cd frontend && npm run coverage    # coverage pentru frontend
```

Testele **nu apelează NASA**: în backend HTTP-ul este simulat cu biblioteca `responses`,
în frontend `fetch` este înlocuit cu un mock.

## Structură

```
backend/
  spacehub/            setări și rute Django
  gallery/
    nasa_client.py     singurul loc care vorbește cu NASA (normalizare, cache APOD)
    views.py           validare parametri + endpoint-uri
    tests/             câte un fișier de teste per story
frontend/
  src/
    api.js             cererile către backend
    pages/             Home, Search, ImageDetail, ApodDetail
    components/        SearchBar, ImageGrid, DetailView, CopyLinkButton
    tests/             app.test.jsx (grupat pe US)
```

## Decizii de proiectare

- **Apelurile către NASA se fac din backend**: datele sunt normalizate într-un singur loc,
  iar o schimbare la NASA (cum a fost mutarea APOD) se repară fără să atingem React.
- **APOD este ținut în cache** (o oră pentru „azi”, o zi pentru o dată anume), ca să nu
  consumăm limita de cereri la fiecare vizită.
- **Descărcarea trece prin backend**: atributul HTML `download` este ignorat de browser
  pentru fișiere de pe alt domeniu. Endpoint-ul acceptă doar adrese `https` de pe
  `images-assets.nasa.gov`, `assets.science.nasa.gov` și `apod.nasa.gov`.
- **Starea căutării stă în URL** (`/search?q=Mars&year_start=2010`), deci și o căutare
  poate fi trimisă ca link.
- **APOD poate fi video** în unele zile: atunci se afișează miniatura și un buton către
  video, fără buton de descărcare.
- Cele 6 stories nu au nevoie de tabele proprii; SQLite e configurat pentru stories de
  conturi, favorite și colecții.
