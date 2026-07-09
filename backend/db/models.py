from sqlalchemy import Column, Integer, String, Text, Boolean
from db.database import Base

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    topic = Column(String)
    summary = Column(Text)
    sources = Column(Text)
    raw_sources = Column(Text, default="[]")  # full source objects (title/link/abstract/etc) as JSON, needed for follow-up questions
    date = Column(String)
    tags = Column(String, default="")  # comma-separated tags, e.g. "cybersecurity,school"


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String)
    topic = Column(String)       # the search topic this source came from
    saved_at = Column(String)


class SearchCache(Base):
    __tablename__ = "search_cache"
    id = Column(Integer, primary_key=True)
    topic_key = Column(String, unique=True, index=True)  # normalized topic
    data = Column(Text)           # full JSON response, cached
    created_at = Column(String)


class DigestSubscription(Base):
    __tablename__ = "digest_subscriptions"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    topic = Column(String)
    created_at = Column(String)
    last_sent_at = Column(String, default="")
    day_of_week = Column(String, default="mon")     # mon/tue/wed/thu/fri/sat/sun
    hour = Column(Integer, default=8)                 # 0-23, in the subscriber's own timezone
    timezone = Column(String, default="America/New_York")  # IANA timezone name
    frequency = Column(String, default="weekly")      # weekly/biweekly/monthly
    confirmed = Column(Boolean, default=False)        # requires clicking a confirmation email link


class DigestLog(Base):
    __tablename__ = "digest_log"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer)
    email = Column(String)
    topic = Column(String)
    sent_at = Column(String)
    source_count = Column(Integer, default=0)
