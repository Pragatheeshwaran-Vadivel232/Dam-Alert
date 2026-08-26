from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from models.farmer import Base
from datetime import datetime, timezone

class AlertLog(Base):
    __tablename__ = "alert_logs"

    id               = Column(Integer, primary_key=True, index=True)
    farmer_id        = Column(Integer, ForeignKey("farmers.id"))
    dam_name         = Column(String(50))
    alert_level      = Column(String(20))
    message_text     = Column(Text)
    sms_status       = Column(String(20), default="QUEUED")
    sms_provider_id  = Column(String(100))
    sent_at          = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))