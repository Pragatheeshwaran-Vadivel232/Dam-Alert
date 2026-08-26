from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from models.farmer import Base
from datetime import datetime, timezone

class DamReading(Base):
    __tablename__ = "dam_readings"

    id               = Column(Integer, primary_key=True, index=True)
    dam_name         = Column(String(50), nullable=False)
    reading_date     = Column(Date, nullable=False)
    full_depth_ft    = Column(Numeric(6, 2))
    full_cap_mcft    = Column(Numeric(10, 2))
    level_ft         = Column(Numeric(6, 2))
    storage_mcft     = Column(Numeric(10, 2))
    inflow_cusecs    = Column(Numeric(10, 2))
    outflow_cusecs   = Column(Numeric(10, 2))
    fill_percent     = Column(Numeric(5, 2))
    ttf_hours        = Column(Numeric(8, 1))
    alert_level      = Column(String(20))
    source           = Column(String(20), default="SCRAPER")
    created_at       = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))