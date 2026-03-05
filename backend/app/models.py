import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CardStatus(str, enum.Enum):
    processing = "processing"
    identified = "identified"
    unidentified = "unidentified"

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    scryfall_id: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    colors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array string
    color_identity: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    mana_cost: Mapped[str | None] = mapped_column(String, nullable=True)
    oracle_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CardStatus] = mapped_column(SAEnum(CardStatus), default=CardStatus.processing)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_image: Mapped[str] = mapped_column(String)
