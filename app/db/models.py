from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))
    role: Mapped[str] = mapped_column(String(32), default="user")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    current_plan: Mapped[str] = mapped_column(String(32), default="free")
    transcription_quality: Mapped[str] = mapped_column(String(32), default="fast")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    balance: Mapped["Balance | None"] = relationship(back_populates="user")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user")
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        back_populates="user"
    )
    transcriptions: Mapped[list["Transcription"]] = relationship(
        back_populates="user"
    )
    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user",
        uselist=False,
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    profile_type: Mapped[str | None] = mapped_column(String(64))
    primary_goal: Mapped[str | None] = mapped_column(String(255))
    preferred_output: Mapped[str | None] = mapped_column(String(255))
    audio_source: Mapped[str | None] = mapped_column(String(255))
    quality_preference: Mapped[str | None] = mapped_column(String(32))
    usage_frequency: Mapped[str | None] = mapped_column(String(64))
    recommended_plan: Mapped[str | None] = mapped_column(String(32))
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="profile")


class Balance(Base):
    __tablename__ = "balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    minutes_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    minutes_used: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    minutes_remaining: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="balance")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    package_name: Mapped[str] = mapped_column(String(64))
    minutes: Mapped[int] = mapped_column()
    payment_method: Mapped[str] = mapped_column(String(32), default="sbp")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger)

    user: Mapped[User] = relationship(back_populates="payments")


class BalanceTransaction(Base):
    __tablename__ = "balance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    minutes_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reason: Mapped[str | None] = mapped_column(Text)
    admin_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="balance_transactions")


class Transcription(Base):
    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    audio_duration_seconds: Mapped[int] = mapped_column()
    transcript_text: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    cost_estimate: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="transcriptions")
