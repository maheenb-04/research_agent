from sqlalchemy import Column, Integer, String, Text
from db.database import Base

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    topic = Column(String)
    summary = Column(Text)
    sources = Column(Text)
    date = Column(String)
