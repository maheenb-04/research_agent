# Research Agent

An AI-powered research assistant that searches academic sources on any topic and generates a structured summary — key insights, trends, and real-world applications — with a saved history of past reports.

Built as a learning project: cloned from an open-source starter, then rebuilt with a new data pipeline, a custom UI, and security hardening.

## Features

- **Search any topic** and pull up to 25 relevant academic sources
- **AI-generated summaries** — insights, trends, applications, and a "why it matters" breakdown per source
- **Search history** — every report is saved locally and can be revisited anytime
- **RAG search pipeline** — tries Semantic Scholar first, automatically falls back to CrossRef if rate-limited

## Tech stack

**Backend**
- FastAPI (Python)
- [Groq](https://groq.com) API (`llama-3.3-70b-versatile`) for summarization — OpenAI-compatible endpoint
- [Semantic Scholar API](https://api.semanticscholar.org) and [CrossRef API](https://api.crossref.org) for source search
- SQLite (via SQLAlchemy) for saved report history
- APScheduler for background scheduling

**Frontend**
- React + Vite
- Tailwind CSS
- Custom fonts: Fredoka, Permanent Marker, Geist Pixel

**Security**
- Restricted CORS
- Per-IP rate limiting (10 requests/minute)
- Input length validation
- Server-side error logging with no internal detail leakage to the client

## Getting started

### Prerequisites
- Python 3.9+
- Node.js 18+
- A free [Groq API key](https://console.groq.com/keys)

### Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:
```
GROQ_API_KEY=your_groq_api_key_here
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

Open `http://localhost:5173` in your browser, enter any research topic, and hit **Go**. Past searches are saved automatically under the **History** tab.

## Project structure

```
research_agent/
├── backend/
│   ├── main.py                # FastAPI app, routes, rate limiting, validation
│   ├── agent/
│   │   ├── scraper.py         # Semantic Scholar + CrossRef search
│   │   ├── summarizer.py      # Groq LLM summarization
│   │   └── scheduler.py       # background job scheduling
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   └── models.py          # Report model
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx             # main UI
    │   └── index.css           # global styles
    ├── index.html
    └── tailwind.config.js
```

## Credits

Originally based on [ShaquilleTaj/ai-research-agent](https://github.com/ShaquilleTaj/ai-research-agent), modified and redesigned.
