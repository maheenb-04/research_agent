# Research Agent

An AI-powered research assistant that searches academic sources on any topic and generates a structured summary — key insights, trends, and real-world applications — with a saved history of past reports.

Built as a learning project: cloned from an open-source starter, then rebuilt with a new data pipeline, a custom UI, and security hardening.

## Features

- **Search any topic** and pull up to 25 relevant, link-validated academic sources
- **AI-generated summaries** — insights, trends, applications, and a "why it matters" breakdown per source, each grounded in and cited back to its actual source
- **Citation export** — one-click copy of APA, MLA, or Chicago citations for any source
- **Favorites** — star sources across searches into a personal reading list
- **Tags** — organize saved reports into custom categories
- **Follow-up questions** — ask a follow-up on a saved report using the same retrieved sources, no new search needed (RAG-style)
- **Weekly email digests** — subscribe to a topic and get a fresh digest of the newest sources every Monday
- **Search caching** — identical searches within 24 hours return instantly instead of re-running
- **RAG search pipeline** — tries Semantic Scholar first, automatically falls back to CrossRef if rate-limited; results are restricted to sources from 2020 onward

## Tech stack

**Backend**
- FastAPI (Python)
- [Groq](https://groq.com) API (`llama-3.3-70b-versatile`) for summarization — OpenAI-compatible endpoint
- [Semantic Scholar API](https://api.semanticscholar.org) and [CrossRef API](https://api.crossref.org) for source search
- SQLite (via SQLAlchemy) for saved reports, favorites, tags, digest subscriptions, and search caching
- APScheduler for the weekly digest job
- Gmail SMTP for sending digest emails

**Frontend**
- React + Vite
- Tailwind CSS
- Fonts: Space Grotesk, DM Sans

**Security**
- Restricted CORS
- Per-IP rate limiting (10 requests/minute)
- Input length validation
- Server-side error logging with no internal detail leakage to the client
- Every source link is validated (checked for dead/removed pages) before being shown

## Getting started

### Prerequisites
- Python 3.9+
- Node.js 18+
- A free [Groq API key](https://console.groq.com/keys)
- A Gmail account with an [app password](https://myaccount.google.com/apppasswords) (only needed for the weekly digest feature)

### Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/` (see `.env.example`):
```
GROQ_API_KEY=your_groq_api_key_here
GMAIL_ADDRESS=your_gmail_address_here
GMAIL_APP_PASSWORD=your_gmail_app_password_here
```

**Note on the Gmail app password**: this must be a Gmail *app password*, not your regular account password. Generate one at https://myaccount.google.com/apppasswords (requires 2-Step Verification to be enabled on your Google account). Never use your real Gmail password here.

If you're setting this up for the first time on a database that predates the digest/favorites/tags features, run the one-time migration:
```bash
python3 migrate_db.py
```

Run the backend:
```bash
uvicorn main:app --reload --reload-exclude "*.db"
```

Backend runs at `http://localhost:8000`.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### How to Use

Open `http://localhost:5173` in your browser, enter any research topic, and hit **Go**. Past searches are saved automatically under the **History** tab. Star sources to save them under **Favorites**. Subscribe to a topic under **Digests** to get a weekly email with the newest sources.

### Running with Docker (alternative to the setup above)

If you'd rather not manage a Python venv and Node install directly, the whole app can run in containers instead:

```bash
docker compose up --build
```

This builds and runs both the backend and frontend in containers, available at the same `http://localhost:5173` and `http://localhost:8000` addresses. Your `.env` file and `data.db` still need to exist in `backend/` beforehand — Docker reads them from there.

**Note**: Docker does not hot-reload code changes — you'll need to re-run with `--build` after editing any code. For active development, the manual setup above (with `--reload`) is more convenient.

### Browser extension (optional)

There's a Chrome extension in `browser-extension/` that lets you right-click any selected text (or a whole page) and research it instantly, without opening the app manually. See `browser-extension/README.md` for install instructions - it's not published to the Chrome Web Store, so it loads as an unpacked developer extension.

## Project structure

```
research_agent/
├── backend/
│   ├── main.py                # FastAPI app, routes, rate limiting, validation
│   ├── migrate_db.py          # one-time DB migration script
│   ├── Dockerfile
│   ├── agent/
│   │   ├── scraper.py         # Semantic Scholar + CrossRef search, link validation
│   │   ├── summarizer.py      # Groq LLM summarization, follow-up Q&A, digest intros
│   │   ├── citations.py       # deterministic APA/MLA/Chicago citation formatting
│   │   ├── mailer.py          # Gmail SMTP email sending
│   │   └── scheduler.py       # weekly digest job
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   └── models.py          # Report, Favorite, SearchCache, DigestSubscription models
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── src/
│   │   ├── App.jsx             # main UI
│   │   └── index.css           # global styles
│   ├── index.html
│   └── tailwind.config.js
├── browser-extension/
│   ├── manifest.json
│   ├── background.js           # context menu + API calls
│   ├── popup.html / popup.js / popup.css
│   └── icons/
└── docker-compose.yml
```

## Notes

Each person running their own copy of this project needs their own `.env` with their own Groq key and Gmail app password — credentials are never shared in the repo, only the code is. The digest feature sends real email from your own Gmail account, so make sure you're comfortable with that before subscribing others to it.

## Credits

Originally based on [ShaquilleTaj/ai-research-agent](https://github.com/ShaquilleTaj/ai-research-agent), modified and redesigned.
