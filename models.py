from sqlalchemy import Boolean, Column, Integer
from database import Base

class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, unique=True, index=True)
    legacy = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
