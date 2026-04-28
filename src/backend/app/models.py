from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, DECIMAL, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)

    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    events_organized = relationship("Event", back_populates="organizer")
    event_participations = relationship("EventParticipant", back_populates="user")
    items_booked = relationship("Item", foreign_keys="Item.booked_by", back_populates="booked_by_user")
    expenses_paid = relationship("Expense", foreign_keys="Expense.paid_by", back_populates="payer")
    expense_shares = relationship("ExpenseShare", back_populates="user")

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="wishlists")
    items = relationship("Item", back_populates="wishlist", cascade="all, delete-orphan")
    event_wishlists = relationship("EventWishlist", back_populates="wishlist")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)
    link = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="active")
    wishlist_id = Column(Integer, ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False)
    booked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    booked_event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)

    wishlist = relationship("Wishlist", back_populates="items")
    booked_by_user = relationship("User", foreign_keys=[booked_by], back_populates="items_booked")
    booked_event = relationship("Event", foreign_keys=[booked_event_id], back_populates="booked_items")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    organizer = relationship("User", back_populates="events_organized")
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")
    wishlists = relationship("EventWishlist", back_populates="event", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="event", cascade="all, delete-orphan")
    booked_items = relationship("Item", foreign_keys=[Item.booked_event_id], back_populates="booked_event")

class EventWishlist(Base):
    __tablename__ = "event_wishlists"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id", ondelete="CASCADE"), primary_key=True)

    event = relationship("Event", back_populates="wishlists")
    wishlist = relationship("Wishlist", back_populates="event_wishlists")

class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    event = relationship("Event", back_populates="participants")
    user = relationship("User", back_populates="event_participations")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    event = relationship("Event", back_populates="expenses")
    payer = relationship("User", foreign_keys=[paid_by], back_populates="expenses_paid")
    shares = relationship("ExpenseShare", back_populates="expense", cascade="all, delete-orphan")

class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    is_paid = Column(Boolean, default=False)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    expense = relationship("Expense", back_populates="shares")
    user = relationship("User", back_populates="expense_shares")
