from datetime import date
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session
from app.config import DATABASE_URL


engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Draw(Base):
    """Stores a single lottery drawing."""
    __tablename__ = "draws"
    __table_args__ = (
        # Prevent duplicate rows for the same game + draw date
        UniqueConstraint("game", "draw_date", name="uq_draws_game_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    game = Column(String(20), index=True)  # lotto | twostep | powerball
    draw_date = Column(Date, index=True)
    n1 = Column(Integer)
    n2 = Column(Integer)
    n3 = Column(Integer)
    n4 = Column(Integer)
    n5 = Column(Integer, nullable=True)   # null for twostep main picks (only 4)
    n6 = Column(Integer, nullable=True)   # null for twostep/powerball main picks
    bonus = Column(Integer, nullable=True)  # bonus ball / powerball number
    power_play = Column(Integer, nullable=True)  # powerball power play
    era = Column(String(10))              # era1 | era2 | era3
    is_bonus_era = Column(Boolean, default=False)  # Texas Lotto era2 flag


class JackpotEntry(Base):
    """Manual jackpot entries entered by the user."""
    __tablename__ = "jackpot_entries"

    id = Column(Integer, primary_key=True, index=True)
    game = Column(String(20), index=True)
    amount = Column(Float)
    next_draw_date = Column(Date, nullable=True)
    is_annuity = Column(Boolean, default=True)  # for Powerball
    updated_at = Column(Date)


class JackpotHistory(Base):
    """Tracks historical jackpot values for rollover analysis."""
    __tablename__ = "jackpot_history"

    id = Column(Integer, primary_key=True, index=True)
    game = Column(String(20))
    draw_date = Column(Date)
    jackpot_amount = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    with Session(engine) as session:
        yield session
