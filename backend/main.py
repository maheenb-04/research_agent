from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from agent.scraper import search
from agent.summarizer import summarize
from db.database import Base, engine, SessionLocal
from db.models import Report
from agent.scheduler import start_scheduler
from datetime import datetime
import json  # ✅ IMPORTANT

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ DB
Base.metadata.create_all(bind=engine)

# ✅ scheduler
start_scheduler()


# 🚀 MAIN AGENT
@app.get("/run/{topic}")
def run_agent(topic: str):
    try:
        # 🔥 better query expansion
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

        # ✅ SAFETY CHECK
        if not summary_data:
            return {
                "data": None,
                "sources": [s["link"] for s in sources],
                "message": "Summarization failed."
            }

        # 3. SAVE TO DB (FIXED JSON STORAGE)
        db = SessionLocal()
        report = Report(
            topic=topic,
            summary=json.dumps(summary_data),  # ✅ FIX
            sources=",".join([s["link"] for s in sources]),
            date=str(datetime.now())
        )
        db.add(report)
        db.commit()
        db.close()

        # 4. RETURN CLEAN RESPONSE
        return {
            "data": summary_data,
            "sources": [s["link"] for s in sources]
        }

    except Exception as e:
        print("ERROR:", e)  # ✅ DEBUG LOG
        return {
            "error": str(e),
            "data": None,
            "sources": []
        }


# 📊 HISTORY
@app.get("/reports")
def get_reports():
    db = SessionLocal()
    reports = db.query(Report).all()
    db.close()
    return reports