import logging
import hashlib
import os
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from agent.scraper import search
from agent.summarizer import generate_digest_intro
from agent.mailer import send_email
from db.database import SessionLocal
from db.models import DigestSubscription, DigestLog

logger = logging.getLogger("research_agent.scheduler")

FREQUENCY_DAYS = {
    "weekly": 6,
    "biweekly": 13,
    "monthly": 27,
}

CONFIRM_TOKEN_MAX_AGE_SECONDS = 48 * 3600  # confirmation links expire after 48 hours


def _get_app_secret():
    secret = os.getenv("APP_SECRET")
    if not secret:
        raise RuntimeError(
            "APP_SECRET must be set in .env - it's required to sign unsubscribe "
            "and account-access links securely. Add a long random string to your "
            "backend/.env file, e.g. APP_SECRET=some-long-random-string-here"
        )
    return secret


def _sign(*parts):
    secret = _get_app_secret()
    raw = ":".join(str(p) for p in parts) + f":{secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def make_unsubscribe_token(subscription_id, email):
    # intentionally does NOT expire: an unsubscribe link may sit unopened in
    # someone's inbox for months, and per standard email best practice
    # (CAN-SPAM/GDPR expectations), an unsubscribe link must keep working for
    # as long as you might still be emailing that person - expiring it would
    # trap someone into continuing to receive mail they no longer want.
    return _sign(subscription_id, email, "unsubscribe")


def verify_unsubscribe_token(subscription_id, email, token):
    return make_unsubscribe_token(subscription_id, email) == token


def make_confirm_token(subscription_id, email):
    # DOES expire (see CONFIRM_TOKEN_MAX_AGE_SECONDS): confirmation is a
    # one-time action that should happen soon after signup. Bounding its
    # validity window limits how long a stale, unconfirmed subscription
    # can be activated by an old link, and is standard practice for
    # email-confirmation flows generally.
    ts = int(time.time())
    sig = _sign(subscription_id, email, "confirm", ts)
    return f"{ts}.{sig}"


def verify_confirm_token(subscription_id, email, token):
    try:
        ts_str, sig = token.split(".", 1)
        ts = int(ts_str)
    except (ValueError, AttributeError):
        return False

    if time.time() - ts > CONFIRM_TOKEN_MAX_AGE_SECONDS:
        return False

    expected_sig = _sign(subscription_id, email, "confirm", ts)
    return expected_sig == sig


def make_email_access_token(email):
    """A per-email token that proves someone has confirmed ownership of that
    email address (via clicking a confirmation link sent to it). Required to
    view/manage subscriptions for that email - without this, anyone could
    type in someone else's email and see or change their subscriptions.
    Intentionally does not expire - this is meant to work like a bookmarked
    "manage my subscriptions" link the person can return to anytime."""
    return _sign(email.lower().strip(), "access")


def verify_email_access_token(email, token):
    return make_email_access_token(email) == token


def is_due(sub, now_utc):
    """Check whether a subscription is due to send, in the subscriber's own
    timezone, respecting their chosen day/hour/frequency. Unconfirmed
    subscriptions are never due - confirmation is required first."""
    if not sub.confirmed:
        return False

    try:
        tz = ZoneInfo(sub.timezone or "America/New_York")
    except Exception:
        tz = ZoneInfo("America/New_York")

    local_now = now_utc.astimezone(tz)

    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    target_day = day_map.get((sub.day_of_week or "mon").lower(), 0)

    if local_now.weekday() != target_day:
        return False
    if local_now.hour != (sub.hour if sub.hour is not None else 8):
        return False

    if not sub.last_sent_at:
        return True

    try:
        last_sent = datetime.fromisoformat(sub.last_sent_at)
    except Exception:
        return True

    min_gap_days = FREQUENCY_DAYS.get(sub.frequency or "weekly", 6)
    return (now_utc.replace(tzinfo=None) - last_sent) >= timedelta(days=min_gap_days)


def build_unsubscribe_url(subscription_id, email):
    token = make_unsubscribe_token(subscription_id, email)
    return f"http://localhost:8000/digests/unsubscribe?id={subscription_id}&token={token}"


def build_confirm_url(subscription_id, email):
    token = make_confirm_token(subscription_id, email)
    return f"http://localhost:8000/digests/confirm?id={subscription_id}&token={token}"


def build_confirmation_email_html(topic, confirm_url):
    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #22201A; font-size: 20px;">Confirm your digest subscription</h1>
      <p style="color: #444; line-height: 1.5;">
        Someone (hopefully you!) requested a weekly digest for <strong>"{topic}"</strong>
        from Research Agent. If this was you, click below to confirm - if not, you can
        safely ignore this email and nothing will be sent.
      </p>
      <p>
        <a href="{confirm_url}" style="display: inline-block; background: #6B8FE0; color: #2A4A9E;
           font-weight: 700; padding: 12px 24px; border-radius: 999px; text-decoration: none;">
          Confirm subscription
        </a>
      </p>
    </div>
    """


def build_combined_digest_html(topic_sections):
    """topic_sections: list of dicts with topic, intro, sources, unsubscribe_url"""
    sections_html = ""
    for section in topic_sections:
        rows = ""
        for s in section["sources"][:8]:
            rows += f"""
            <tr>
              <td style="padding: 10px 0; border-bottom: 1px solid #eee;">
                <a href="{s['link']}" style="font-weight: 600; color: #2A4A9E; text-decoration: none;">{s['title']}</a>
              </td>
            </tr>
            """
        sections_html += f"""
        <div style="margin-bottom: 32px;">
          <h2 style="color: #22201A; margin-bottom: 8px;">{section['topic']}</h2>
          <p style="color: #444; line-height: 1.5;">{section['intro']}</p>
          <table style="width: 100%; border-collapse: collapse;">{rows}</table>
          <p style="font-size: 12px; margin-top: 10px;">
            <a href="{section['unsubscribe_url']}" style="color: #999;">Unsubscribe from "{section['topic']}" digests</a>
          </p>
        </div>
        """

    return f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
      <h1 style="color: #22201A; font-size: 20px;">Your research digest</h1>
      {sections_html}
    </div>
    """


def send_digests():
    """Runs every hour. Finds all CONFIRMED subscriptions that are due right
    now (in their own timezone/day/hour/frequency), batches every
    subscriber's due topics into ONE combined email per address, sends it,
    and logs each topic to DigestLog."""
    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

    db = SessionLocal()
    try:
        subscriptions = db.query(DigestSubscription).all()
    finally:
        db.close()

    due_by_email = {}
    for sub in subscriptions:
        if is_due(sub, now_utc):
            due_by_email.setdefault(sub.email, []).append(sub)

    if not due_by_email:
        return

    for email, subs in due_by_email.items():
        topic_sections = []
        sent_subs = []

        for sub in subs:
            try:
                sources = search(sub.topic)
                if not sources:
                    logger.info("No sources found for digest topic=%r, skipping.", sub.topic)
                    continue

                intro = generate_digest_intro(sub.topic, sources)
                topic_sections.append({
                    "topic": sub.topic,
                    "intro": intro,
                    "sources": sources,
                    "unsubscribe_url": build_unsubscribe_url(sub.id, sub.email),
                })
                sent_subs.append((sub, len(sources)))
            except Exception:
                logger.exception("Failed to build digest section for subscription id=%r", sub.id)

        if not topic_sections:
            continue

        try:
            html = build_combined_digest_html(topic_sections)
            subject = (
                f"Your digest: {topic_sections[0]['topic']}"
                if len(topic_sections) == 1
                else f"Your digest: {len(topic_sections)} topics"
            )
            send_email(to_address=email, subject=subject, html_body=html)

            db = SessionLocal()
            try:
                now_str = datetime.now().isoformat()
                for sub, source_count in sent_subs:
                    row = db.query(DigestSubscription).filter(DigestSubscription.id == sub.id).first()
                    if row:
                        row.last_sent_at = now_str
                    db.add(DigestLog(
                        subscription_id=sub.id,
                        email=sub.email,
                        topic=sub.topic,
                        sent_at=now_str,
                        source_count=source_count,
                    ))
                db.commit()
            finally:
                db.close()

            logger.info("Sent combined digest to %r covering %d topic(s)", email, len(topic_sections))

        except Exception:
            logger.exception("Failed to send combined digest to %r", email)


def start_scheduler():
    scheduler = BackgroundScheduler()
    # check every hour on the hour - each subscription's own day/hour/timezone
    # determines whether it's actually due during that check
    scheduler.add_job(send_digests, "cron", minute=0)
    scheduler.start()
