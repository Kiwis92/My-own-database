"""
Universeel multi-country datamodel (zie docs/project_brief.md).

Ontwerpprincipes:
- Elk land is een rij in `countries`; alle politieke entiteiten hangen daaronder.
  Nieuwe landen (EU, ES, DE, US, GB, AU, BR) zijn plug-and-play: een nieuwe
  Country-rij + een ingestie-adapter (zie app/ingestion/).
- Landspecifieke stem-data (bv. Spaanse *votaciones*, Amerikaanse *roll-call votes*)
  wordt door de adapters gemapt naar het universele Motion/VoteRecord-schema.
- Beloftes bestaan in twee soorten: uit een verkiezingsprogramma (partij + jaar)
  of uit een regeerakkoord (kabinet). PromiseMatch koppelt parlementair gedrag
  (moties/wetten/stemmingen) aan beloftes — de plek waar de AI-matching landt.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, Date, DateTime,
    ForeignKey, Table, Enum, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base


class PromiseStatus(str, enum.Enum):
    beloofd = "Beloofd"
    in_uitvoering = "In Uitvoering"
    deels_waargemaakt = "Deels Waargemaakt"
    waargemaakt = "Waargemaakt"
    gebroken = "Gebroken"
    geparkeerd = "Geparkeerd"


class PromiseSource(str, enum.Enum):
    regeerakkoord = "Regeerakkoord"
    verkiezingsprogramma = "Verkiezingsprogramma"


class VoteChoice(str, enum.Enum):
    voor = "Voor"
    tegen = "Tegen"
    onthouden = "Onthouden"
    afwezig = "Afwezig"


class MotionKind(str, enum.Enum):
    wet = "Wet"
    motie = "Motie"
    amendement = "Amendement"


class MatchRelation(str, enum.Enum):
    steunt = "Steunt belofte"
    weerspreekt = "Weerspreekt belofte"
    gerelateerd = "Gerelateerd"


cabinet_party = Table(
    "cabinet_party",
    Base.metadata,
    Column("cabinet_id", Integer, ForeignKey("cabinets.id"), primary_key=True),
    Column("party_id", Integer, ForeignKey("parties.id"), primary_key=True),
)


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    code = Column(String(5), unique=True, nullable=False)   # nl, eu, es, de, us, gb, au, br
    name = Column(String(100), nullable=False)              # weergavenaam (NL-default)
    legislature_name = Column(String(150), nullable=True)   # bv. "Tweede Kamer", "Congreso de los Diputados"
    api_source = Column(String(300), nullable=True)         # basis-URL van de open-data API
    enabled = Column(Boolean, default=True)

    parties = relationship("Party", back_populates="country")
    cabinets = relationship("Cabinet", back_populates="country")
    elections = relationship("Election", back_populates="country")
    motions = relationship("Motion", back_populates="country")


class Party(Base):
    __tablename__ = "parties"
    __table_args__ = (UniqueConstraint("country_id", "abbreviation"),)

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(20), nullable=False)
    color = Column(String(7), default="#3B82F6")
    ideology = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    active = Column(Boolean, default=True)
    current_seats = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    country = relationship("Country", back_populates="parties")
    cabinets = relationship("Cabinet", secondary=cabinet_party, back_populates="parties")
    promises = relationship("Promise", back_populates="party")
    votes = relationship("VoteRecord", back_populates="party")
    seat_results = relationship("SeatResult", back_populates="party")
    finances = relationship("PartyFinance", back_populates="party", cascade="all, delete-orphan")
    attendance = relationship("PartyAttendance", back_populates="party", cascade="all, delete-orphan")


class Election(Base):
    __tablename__ = "elections"
    __table_args__ = (UniqueConstraint("country_id", "year"),)

    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year = Column(Integer, nullable=False)
    date = Column(Date, nullable=True)
    turnout = Column(Float, nullable=True)  # opkomstpercentage

    country = relationship("Country", back_populates="elections")
    seat_results = relationship("SeatResult", back_populates="election", cascade="all, delete-orphan")


class SeatResult(Base):
    __tablename__ = "seat_results"
    __table_args__ = (UniqueConstraint("election_id", "party_id"),)

    id = Column(Integer, primary_key=True)
    election_id = Column(Integer, ForeignKey("elections.id"), nullable=False)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=False)
    seats = Column(Integer, nullable=False)

    election = relationship("Election", back_populates="seat_results")
    party = relationship("Party", back_populates="seat_results")


class Cabinet(Base):
    __tablename__ = "cabinets"

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    slug = Column(String(50), unique=True, nullable=True)   # bv. "kok2", "schoof"
    name = Column(String(255), nullable=False)
    premier = Column(String(150), nullable=True)
    premier_party_id = Column(Integer, ForeignKey("parties.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)                  # NULL = zittend
    seats = Column(Integer, nullable=True)                  # coalitiezetels bij aantreden
    fell = Column(Boolean, default=False)
    fall_reason = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)                # JSON-lijst met hoogtepunten
    coalition_agreement_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    country = relationship("Country", back_populates="cabinets")
    premier_party = relationship("Party", foreign_keys=[premier_party_id])
    parties = relationship("Party", secondary=cabinet_party, back_populates="cabinets")
    promises = relationship("Promise", back_populates="cabinet")

    # Compatibiliteit met templates die op jaartallen leunen
    @property
    def year_start(self):
        return self.start_date.year if self.start_date else None

    @property
    def year_end(self):
        return self.end_date.year if self.end_date else None


class Promise(Base):
    __tablename__ = "promises"

    id = Column(Integer, primary_key=True, index=True)
    source_kind = Column(Enum(PromiseSource), default=PromiseSource.regeerakkoord, nullable=False)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=True)   # bij regeerakkoord
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=True)     # bij verkiezingsprogramma
    election_year = Column(Integer, nullable=True)                           # bij verkiezingsprogramma
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="Overig")     # vrije categorie (i18n via vertaalsleutel)
    status = Column(Enum(PromiseStatus), default=PromiseStatus.beloofd)
    source_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    cabinet = relationship("Cabinet", back_populates="promises")
    party = relationship("Party", back_populates="promises")
    evidence = relationship("Evidence", back_populates="promise", cascade="all, delete-orphan")
    matches = relationship("PromiseMatch", back_populates="promise", cascade="all, delete-orphan")


class Motion(Base):
    """Universele parlementaire handeling: wet, motie of amendement."""
    __tablename__ = "motions"
    __table_args__ = (UniqueConstraint("country_id", "external_id"),)

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    external_id = Column(String(100), nullable=True)    # ID in de bron-API (bv. TK Zaak-nummer)
    kind = Column(Enum(MotionKind), default=MotionKind.motie)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    date = Column(Date, nullable=True)
    year = Column(Integer, nullable=True)
    source_url = Column(String(500), nullable=True)     # verificatielink naar officiële bron
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    country = relationship("Country", back_populates="motions")
    votes = relationship("VoteRecord", back_populates="motion", cascade="all, delete-orphan")
    matches = relationship("PromiseMatch", back_populates="motion", cascade="all, delete-orphan")


class VoteRecord(Base):
    """Stem van een fractie (of, bij roll-call, een individueel lid) op een Motion."""
    __tablename__ = "vote_records"

    id = Column(Integer, primary_key=True)
    motion_id = Column(Integer, ForeignKey("motions.id"), nullable=False)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=False)
    vote = Column(Enum(VoteChoice), nullable=False)
    is_roll_call = Column(Boolean, default=False)       # hoofdelijke stemming
    politician = Column(String(150), nullable=True)     # gevuld bij roll-call votes

    motion = relationship("Motion", back_populates="votes")
    party = relationship("Party", back_populates="votes")


class PromiseMatch(Base):
    """Koppeling tussen parlementair gedrag en een belofte (de AI-matching uit de brief)."""
    __tablename__ = "promise_matches"

    id = Column(Integer, primary_key=True)
    promise_id = Column(Integer, ForeignKey("promises.id"), nullable=False)
    motion_id = Column(Integer, ForeignKey("motions.id"), nullable=False)
    relation = Column(Enum(MatchRelation), default=MatchRelation.gerelateerd)
    confidence = Column(Float, nullable=True)           # 0..1, van het AI-model
    verified = Column(Boolean, default=False)           # redactioneel geverifieerd
    note = Column(Text, nullable=True)

    promise = relationship("Promise", back_populates="matches")
    motion = relationship("Motion", back_populates="matches")


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


class PartyFinance(Base):
    __tablename__ = "party_finances"
    __table_args__ = (UniqueConstraint("party_id", "year"),)

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=False)
    year = Column(Integer, nullable=False)
    subsidy = Column(Integer, nullable=True)        # overheidssubsidie in €
    donations = Column(Integer, nullable=True)
    contributions = Column(Integer, nullable=True)  # ledencontributies

    party = relationship("Party", back_populates="finances")


class PartyAttendance(Base):
    __tablename__ = "party_attendance"
    __table_args__ = (UniqueConstraint("party_id", "year"),)

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=False)
    year = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)      # aanwezigheid bij stemmingen

    party = relationship("Party", back_populates="attendance")
