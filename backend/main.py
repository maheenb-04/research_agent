from dotenv import load_dotenv
load_dotenv()

import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from agent.scraper import search
from agent.summarizer import summarize
from db.database import Base, engine, SessionLocal
from db.models import Report
from agent.scheduler import start_scheduler
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research_agent")

app = FastAPI()

# CORS - restricted to the local frontend only, not open to any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# DB
Base.metadata.create_all(bind=engine)

# scheduler
start_scheduler()

# --- simple in-memory rate limiter ---
# limits each client IP to RATE_LIMIT requests per RATE_WINDOW seconds
RATE_LIMIT = 10
RATE_WINDOW = 60
request_log = defaultdict(deque)


def check_rate_limit(client_ip: str):
    now = time.time()
    q = request_log[client_ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    q.append(now)


MAX_TOPIC_LENGTH = 200


def validate_topic(topic: str) -> str:
    topic = topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    if len(topic) > MAX_TOPIC_LENGTH:
        raise HTTPException(status_code=400, detail=f"Topic must be under {MAX_TOPIC_LENGTH} characters.")
    return topic


# MAIN AGENT
@app.get("/run/{topic}")
def run_agent(topic: str, request: Request):
    check_rate_limit(request.client.host)
    topic = validate_topic(topic)

    try:
        enhanced_topic = f"{topic} latest news research breakthroughs industry trends"

        # 1. SEARCH
        sources = search(enhanced_topic)

        if not sources or len(sources) == 0:
            return {
                "data": None,
                "sources": [],
                "message": "No sources found. Try a more specific topic."
            }

        # 2. SUMMARIZE (returns structured JSON)
        summary_data = summarize(topic, sources)

        if not summary_data:
            return {
                "data": None,
                "sources": [s["link"] for s in sources],
                "message": "Summarization failed."
            }

        # 3. SAVE TO DB
        db = SessionLocal()
        try:
            report = Report(
                topic=topic,
                summary=json.dumps(summary_data),
                sources=",".join([s["link"] for s in sources]),
                date=str(datetime.now())
            )
            db.add(report)
            db.commit()
        finally:
            db.close()

        # 4. RETURN CLEAN RESPONSE
        return {
            "data": summary_data,
            "sources": [s["link"] for s in sources]
        }

    except HTTPException:
        raise
    except Exception as e:
        # log full details server-side only - never leak internals to the client
        logger.exception("run_agent failed for topic=%r", topic)
        return {
            "error": "Something went wrong while processing your request. Please try again.",
            "data": None,
            "sources": []
        }


# HISTORY
@app.get("/reports")
def get_reports():
    db = SessionLocal()
    try:
        reports = db.query(Report).all()
        return reports
    finally:
        db.close()
