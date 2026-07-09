from dotenv import load_dotenv
load_dotenv()

import logging
import time
import hashlib
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from agent.scraper import search
from agent.summarizer import summarize, answer_followup
from db.database import Base, engine, SessionLocal
from db.models import Report, Favorite, SearchCache, DigestSubscription, DigestLog
from agent.scheduler import (
    start_scheduler,
    send_digests,
    build_combined_digest_html,
    make_unsubscribe_token,
    verify_unsubscribe_token,
    build_unsubscribe_url,
    make_confirm_token,
    verify_confirm_token,
    build_confirm_url,
    build_confirmation_email_html,
    make_email_access_token,
    verify_email_access_token,
)
from agent.summarizer import generate_digest_intro
from agent.mailer import send_email
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("research_agent")

app = FastAPI()

# CORS - restricted to the local frontend only, not open to any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# DB
Base.metadata.create_all(bind=engine)

# scheduler
start_scheduler()

# --- simple in-memory rate limiter ---
# Limits each client IP to RATE_LIMIT requests per RATE_WINDOW seconds.
# Note: this state lives in process memory only. It resets on every server
# restart and would NOT work correctly across multiple worker processes.
# Fine for local/single-process use; a production deployment with multiple
# workers would need a shared store (e.g. Redis) instead.
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
CACHE_TTL_HOURS = 24


def validate_topic(topic: str) -> str:
    topic = topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    if len(topic) > MAX_TOPIC_LENGTH:
        raise HTTPException(status_code=400, detail=f"Topic must be under {MAX_TOPIC_LENGTH} characters.")
    return topic


def cache_key(topic: str) -> str:
    normalized = topic.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached(topic: str):
    db = SessionLocal()
    try:
        key = cache_key(topic)
        row = db.query(SearchCache).filter(SearchCache.topic_key == key).first()
        if not row:
            return None
        created = datetime.fromisoformat(row.created_at)
        if datetime.now() - created > timedelta(hours=CACHE_TTL_HOURS):
            return None
        return json.loads(row.data)
    except Exception:
        return None
    finally:
        db.close()


def set_cached(topic: str, payload: dict):
    db = SessionLocal()
    try:
        key = cache_key(topic)
        row = db.query(SearchCache).filter(SearchCache.topic_key == key).first()
        data_str = json.dumps(payload)
        now_str = datetime.now().isoformat()
        if row:
            row.data = data_str
            row.created_at = now_str
        else:
            db.add(SearchCache(topic_key=key, data=data_str, created_at=now_str))
        db.commit()
    except Exception:
        logger.exception("failed to write search cache")
    finally:
        db.close()


# MAIN AGENT
@app.get("/run/{topic}")
def run_agent(topic: str, request: Request):
    check_rate_limit(request.client.host)
    topic = validate_topic(topic)

    cached = get_cached(topic)
    if cached:
        return {**cached, "cached": True}

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
                raw_sources=json.dumps(sources),
                date=str(datetime.now()),
                tags=""
            )
            db.add(report)
            db.commit()
            report_id = report.id
        finally:
            db.close()

        response = {
            "data": summary_data,
            "sources": [s["link"] for s in sources],
            "report_id": report_id
        }

        # cache the full response for identical repeat searches within the TTL window
        set_cached(topic, response)

        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception("run_agent failed for topic=%r", topic)
        return {
            "error": "Something went wrong while processing your request. Please try again.",
            "data": None,
            "sources": []
        }


# HISTORY
@app.get("/reports")
def get_reports(tag: str = None):
    db = SessionLocal()
    try:
        query = db.query(Report)
        if tag:
            query = query.filter(Report.tags.contains(tag))
        reports = query.all()
        return reports
    finally:
        db.close()


class TagsUpdate(BaseModel):
    tags: str  # comma-separated


@app.patch("/reports/{report_id}/tags")
def update_report_tags(report_id: int, payload: TagsUpdate, request: Request):
    check_rate_limit(request.client.host)
    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        report.tags = payload.tags.strip()
        db.commit()
        return {"id": report.id, "tags": report.tags}
    finally:
        db.close()


# FOLLOW-UP QUESTIONS - reuse the sources already retrieved for a report,
# no new search happens
class FollowupRequest(BaseModel):
    report_id: int
    question: str


@app.post("/followup")
def followup(payload: FollowupRequest, request: Request):
    check_rate_limit(request.client.host)

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > MAX_TOPIC_LENGTH:
        raise HTTPException(status_code=400, detail=f"Question must be under {MAX_TOPIC_LENGTH} characters.")

    db = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == payload.report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found.")
        sources = json.loads(report.raw_sources or "[]")
        previous_summary = json.loads(report.summary or "{}")
    finally:
        db.close()

    if not sources:
        raise HTTPException(
            status_code=400,
            detail="This report doesn't have saved source data to answer follow-up questions (it may predate this feature)."
        )

    try:
        result = answer_followup(report.topic, sources, previous_summary, question)
        return result
    except Exception:
        logger.exception("followup failed for report_id=%r", payload.report_id)
        return {
            "answer": "Something went wrong answering that question. Please try again.",
            "supporting_sources": []
        }


# FAVORITES
class FavoriteCreate(BaseModel):
    title: str
    link: str
    topic: str


@app.post("/favorites")
def add_favorite(payload: FavoriteCreate, request: Request):
    check_rate_limit(request.client.host)
    db = SessionLocal()
    try:
        existing = db.query(Favorite).filter(Favorite.link == payload.link).first()
        if existing:
            return {"id": existing.id, "already_saved": True}
        fav = Favorite(
            title=payload.title,
            link=payload.link,
            topic=payload.topic,
            saved_at=str(datetime.now())
        )
        db.add(fav)
        db.commit()
        return {"id": fav.id, "already_saved": False}
    finally:
        db.close()


@app.get("/favorites")
def list_favorites():
    db = SessionLocal()
    try:
        return db.query(Favorite).all()
    finally:
        db.close()


@app.delete("/favorites/{favorite_id}")
def delete_favorite(favorite_id: int, request: Request):
    check_rate_limit(request.client.host)
    db = SessionLocal()
    try:
        fav = db.query(Favorite).filter(Favorite.id == favorite_id).first()
        if not fav:
            raise HTTPException(status_code=404, detail="Favorite not found.")
        db.delete(fav)
        db.commit()
        return {"deleted": True}
    finally:
        db.close()


# DIGEST SUBSCRIPTIONS
import re as _re

EMAIL_RE = _re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

VALID_DAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
VALID_FREQUENCIES = {"weekly", "biweekly", "monthly"}
VALID_TIMEZONES = {
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Anchorage", "Pacific/Honolulu", "UTC", "Europe/London", "Europe/Paris",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Australia/Sydney",
}


class DigestCreate(BaseModel):
    email: str
    topic: str
    day_of_week: str = "mon"
    hour: int = 8
    timezone: str = "America/New_York"
    frequency: str = "weekly"


def validate_digest_fields(day_of_week, hour, timezone, frequency):
    day_of_week = (day_of_week or "mon").lower()
    if day_of_week not in VALID_DAYS:
        raise HTTPException(status_code=400, detail="Invalid day of week.")
    if hour is None or not (0 <= hour <= 23):
        raise HTTPException(status_code=400, detail="Hour must be between 0 and 23.")
    if timezone not in VALID_TIMEZONES:
        raise HTTPException(status_code=400, detail="Unsupported timezone.")
    if (frequency or "weekly") not in VALID_FREQUENCIES:
        raise HTTPException(status_code=400, detail="Invalid frequency.")
    return day_of_week, hour, timezone, frequency or "weekly"


def require_email_access(email: str, token: str):
    """Every endpoint that reads or manages subscriptions for a given email
    must prove the caller actually confirmed ownership of that email, via
    the token they received in their confirmation email. Without this,
    anyone could type in someone else's email and view/manage their
    subscriptions."""
    if not token or not verify_email_access_token(email, token):
        raise HTTPException(status_code=403, detail="Invalid or missing access token for this email.")


@app.post("/digests")
def create_digest_subscription(payload: DigestCreate, request: Request):
    check_rate_limit(request.client.host)

    email = payload.email.strip().lower()
    topic = payload.topic.strip()

    if not email or not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    if len(topic) > MAX_TOPIC_LENGTH:
        raise HTTPException(status_code=400, detail=f"Topic must be under {MAX_TOPIC_LENGTH} characters.")

    day_of_week, hour, timezone, frequency = validate_digest_fields(
        payload.day_of_week, payload.hour, payload.timezone, payload.frequency
    )

    db = SessionLocal()
    try:
        existing = db.query(DigestSubscription).filter(
            DigestSubscription.email == email,
            DigestSubscription.topic == topic
        ).first()
        if existing:
            return {"id": existing.id, "already_subscribed": True, "pending_confirmation": not existing.confirmed}

        sub = DigestSubscription(
            email=email,
            topic=topic,
            created_at=str(datetime.now()),
            last_sent_at="",
            day_of_week=day_of_week,
            hour=hour,
            timezone=timezone,
            frequency=frequency,
            confirmed=False,
        )
        db.add(sub)
        db.commit()
        sub_id = sub.id
    finally:
        db.close()

    # send confirmation email - subscription stays inactive until this is clicked
    try:
        confirm_url = build_confirm_url(sub_id, email)
        html = build_confirmation_email_html(topic, confirm_url)
        send_email(to_address=email, subject=f'Confirm your digest for "{topic}"', html_body=html)
    except Exception:
        logger.exception("Failed to send confirmation email for subscription id=%r", sub_id)
        raise HTTPException(
            status_code=500,
            detail="Subscription created, but the confirmation email failed to send. Check your Gmail app password setup."
        )

    return {"id": sub_id, "already_subscribed": False, "pending_confirmation": True}


@app.get("/digests/confirm", response_class=HTMLResponse)
def confirm_digest_subscription(id: int, token: str):
    db = SessionLocal()
    try:
        sub = db.query(DigestSubscription).filter(DigestSubscription.id == id).first()
        if not sub or not verify_confirm_token(id, sub.email, token):
            return HTMLResponse(
                "<h2>This confirmation link is invalid or has expired.</h2>"
                "<p>Confirmation links expire after 48 hours. If yours expired, "
                "go back to the app and use \"Resend confirmation email\" for this topic.</p>",
                status_code=400
            )

        sub.confirmed = True
        db.commit()
        email = sub.email
        topic = sub.topic
    finally:
        db.close()

    access_token = make_email_access_token(email)
    manage_url = f"http://localhost:5173/?digest_email={email}&digest_token={access_token}"

    return HTMLResponse(f"""
        <h2>You're confirmed! You'll get a digest for "{topic}" on your chosen schedule.</h2>
        <p><a href="{manage_url}">Manage your subscriptions</a></p>
    """)


class ResendConfirmation(BaseModel):
    email: str


@app.post("/digests/{digest_id}/resend-confirmation")
def resend_confirmation(digest_id: int, payload: ResendConfirmation, request: Request):
    """If a confirmation link expired (or the email never arrived), this
    sends a fresh one - requires knowing the email the subscription was
    created with, since there's no access token yet for an unconfirmed
    subscription. This can only resend to the email already on file for
    that subscription, so it can't be used to leak or redirect anything."""
    check_rate_limit(request.client.host)
    email = payload.email.strip().lower()

    db = SessionLocal()
    try:
        sub = db.query(DigestSubscription).filter(DigestSubscription.id == digest_id).first()
        if not sub or sub.email != email:
            raise HTTPException(status_code=404, detail="Subscription not found for that email.")
        if sub.confirmed:
            return {"already_confirmed": True}
        topic = sub.topic
    finally:
        db.close()

    try:
        confirm_url = build_confirm_url(digest_id, email)
        html = build_confirmation_email_html(topic, confirm_url)
        send_email(to_address=email, subject=f'Confirm your digest for "{topic}"', html_body=html)
        return {"resent": True}
    except Exception:
        logger.exception("Failed to resend confirmation for subscription id=%r", digest_id)
        raise HTTPException(status_code=500, detail="Failed to resend confirmation email.")


@app.get("/digests")
def list_digest_subscriptions(email: str, token: str):
    email = email.strip().lower()
    require_email_access(email, token)
    db = SessionLocal()
    try:
        return db.query(DigestSubscription).filter(DigestSubscription.email == email).all()
    finally:
        db.close()


@app.delete("/digests/{digest_id}")
def delete_digest_subscription(digest_id: int, email: str, token: str, request: Request):
    check_rate_limit(request.client.host)
    email = email.strip().lower()
    require_email_access(email, token)

    db = SessionLocal()
    try:
        sub = db.query(DigestSubscription).filter(DigestSubscription.id == digest_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found.")
        if sub.email != email:
            raise HTTPException(status_code=403, detail="This subscription doesn't belong to that email.")
        db.delete(sub)
        db.commit()
        return {"deleted": True}
    finally:
        db.close()


@app.get("/digests/unsubscribe", response_class=HTMLResponse)
def unsubscribe_via_email_link(id: int, token: str):
    """One-click unsubscribe link that appears in every digest email. No
    login needed - the token proves the link came from an email we actually
    sent, without requiring the person to sign into anything."""
    db = SessionLocal()
    try:
        sub = db.query(DigestSubscription).filter(DigestSubscription.id == id).first()
        if not sub or not verify_unsubscribe_token(id, sub.email, token):
            return HTMLResponse("<h2>This unsubscribe link is invalid or has expired.</h2>", status_code=400)
        topic = sub.topic
        db.delete(sub)
        db.commit()
    finally:
        db.close()

    return HTMLResponse(f'<h2>You\'ve been unsubscribed from "{topic}" digests.</h2>')


@app.get("/digests/preview")
def preview_digest(topic: str, request: Request):
    """Generate a sample digest for a topic WITHOUT saving a subscription or
    sending an email - lets someone see what they'd get before committing."""
    check_rate_limit(request.client.host)
    topic = validate_topic(topic)

    sources = search(topic)
    if not sources:
        raise HTTPException(status_code=400, detail="No sources found for this topic right now.")

    intro = generate_digest_intro(topic, sources)
    return {
        "intro": intro,
        "sources": [{"title": s["title"], "link": s["link"]} for s in sources[:8]],
    }


@app.get("/digests/history")
def digest_history(email: str, token: str):
    email = email.strip().lower()
    require_email_access(email, token)
    db = SessionLocal()
    try:
        logs = db.query(DigestLog).filter(DigestLog.email == email).order_by(DigestLog.sent_at.desc()).all()
        return logs
    finally:
        db.close()


@app.post("/digests/{digest_id}/send-now")
def send_digest_now(digest_id: int, email: str, token: str, request: Request):
    """Manually trigger a single subscription's digest immediately - useful
    for testing without waiting for the scheduled time. Requires the caller
    to prove ownership of the subscription's email, same as other digest
    management endpoints - otherwise anyone could spam someone else's inbox
    on demand."""
    check_rate_limit(request.client.host)
    email = email.strip().lower()
    require_email_access(email, token)

    db = SessionLocal()
    try:
        sub = db.query(DigestSubscription).filter(DigestSubscription.id == digest_id).first()
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found.")
        if sub.email != email:
            raise HTTPException(status_code=403, detail="This subscription doesn't belong to that email.")
        topic = sub.topic
    finally:
        db.close()

    try:
        sources = search(topic)
        if not sources:
            raise HTTPException(status_code=400, detail="No sources found for this topic right now.")

        intro = generate_digest_intro(topic, sources)
        html = build_combined_digest_html([{
            "topic": topic,
            "intro": intro,
            "sources": sources,
            "unsubscribe_url": build_unsubscribe_url(digest_id, email),
        }])
        send_email(to_address=email, subject=f"Your digest: {topic}", html_body=html)

        db = SessionLocal()
        try:
            now_str = datetime.now().isoformat()
            row = db.query(DigestSubscription).filter(DigestSubscription.id == digest_id).first()
            if row:
                row.last_sent_at = now_str
            db.add(DigestLog(
                subscription_id=digest_id,
                email=email,
                topic=topic,
                sent_at=now_str,
                source_count=len(sources),
            ))
            db.commit()
        finally:
            db.close()

        return {"sent": True}
    except HTTPException:
        raise
    except Exception:
        logger.exception("send_digest_now failed for digest_id=%r", digest_id)
        raise HTTPException(status_code=500, detail="Failed to send digest. Check backend logs and your Gmail app password setup.")
