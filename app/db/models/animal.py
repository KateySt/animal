import datetime

from sqlalchemy import Date, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Gender, IDMixin, TimestampMixin
from app.db.models.base import Base
from app.db.models.health_log import HealthLog


class Animal(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    caretaker_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda gender_item: [gender.value for gender in gender_item]))
    birth_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    health_logs: Mapped[list["HealthLog"]] = relationship("HealthLog", back_populates="animal", cascade="all, delete-orphan", lazy="raise")

    @property
    def age(self) -> int:
        today = datetime.date.today()

        age_years = today.year - self.birth_date.year

        has_birthday_passed = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        if not has_birthday_passed:
            age_years -= 1
        return max(0, age_years)
