from apscheduler.schedulers.background import BackgroundScheduler
from agent.scraper import search
from agent.summarizer import summarize
from db.database import SessionLocal
from db.models import Report
from datetime import datetime

def run_job():
    topic = "AI agents"

    sources = search(topic)

    if not sources:
        return

    summary = summarize(topic, sources)

    db = SessionLocal()
    report = Report(
        topic=topic,
        summary=summary,
        sources=",".join([s["link"] for s in sources]),
        date=str(datetime.now())
    )

    db.add(report)
    db.commit()
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_job, "cron", hour=8)
    scheduler.start()
