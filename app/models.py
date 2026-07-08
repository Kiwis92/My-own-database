from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class PromiseStatus(str, enum.Enum):
    beloofd = "Beloofd"
    in_uitvoering = "In Uitvoering"
    waargemaakt = "Waargemaakt"
    gebroken = "Gebroken"
    geparkeerd = "Geparkeerd"


class PromiseCategory(str, enum.Enum):
    economie = "Economie"
    zorg = "Zorg"
    onderwijs = "Onderwijs"
    veiligheid = "Veiligheid"
    klimaat = "Klimaat & Milieu"
    migratie = "Migratie"
    wonen = "Wonen"
    defensie = "Defensie"
    buitenland = "Buitenlandse Zaken"
    financien = "Financiën"
    infrastructuur = "Infrastructuur"
    sociale_zekerheid = "Sociale Zekerheid"
    overig = "Overig"


cabinet_party = Table(
    "cabinet_party",
    Base.metadata,
    Column("cabinet_id", Integer, ForeignKey("cabinets.id"), primary_key=True),
    Column("party_id", Integer, ForeignKey("parties.id"), primary_key=True),
)


class Party(Base):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(20), unique=True, nullable=False)
    color = Column(String(7), default="#3B82F6")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cabinets = relationship("Cabinet", secondary=cabinet_party, back_populates="parties")
    promises = relationship("Promise", back_populates="party")


class Cabinet(Base):
    __tablename__ = "cabinets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    year_start = Column(Integer, nullable=False)
    year_end = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    coalition_agreement_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parties = relationship("Party", secondary=cabinet_party, back_populates="cabinets")
    promises = relationship("Promise", back_populates="cabinet")


class Promise(Base):
    __tablename__ = "promises"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(PromiseCategory), default=PromiseCategory.overig)
    status = Column(Enum(PromiseStatus), default=PromiseStatus.beloofd)
    source_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cabinet = relationship("Cabinet", back_populates="promises")
    party = relationship("Party", back_populates="promises")
    evidence = relationship("Evidence", back_populates="promise", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    promise_id = Column(Integer, ForeignKey("promises.id"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)
    source_type = Column(String(100), nullable=True)
    date_published = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    promise = relationship("Promise", back_populates="evidence")
