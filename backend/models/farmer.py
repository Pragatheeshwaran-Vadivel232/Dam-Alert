from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class Farmer(Base):
    __tablename__ = "farmers"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    phone           = Column(String(15), unique=True, nullable=False)
    village         = Column(String(100))
    farm_size_acres = Column(Numeric(6, 2))
    dam_preference  = Column(String(20), default="BOTH")
    language        = Column(String(10), default="TAMIL")
    is_active       = Column(Boolean, default=True)
    registered_at   = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))