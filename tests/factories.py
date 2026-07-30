import datetime
import uuid

import factory
from factory import LazyFunction, Sequence

from app.core.security import hash_password
from app.db.enums import Gender, Locale
from app.db.models.animal import Animal, AnimalTranslation
from app.db.models.health_log import HealthLog, HealthLogTranslation
from app.db.models.user import User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid.uuid4)
    email = Sequence(lambda n: f"factory_user_{n}@test.com")
    hashed_password = LazyFunction(lambda: hash_password("TestPass123!"))
    is_active = True
    is_superuser = False
    is_verified = True
    permissions_version = 1


class AnimalFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Animal
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid.uuid4)
    gender = Gender.male
    birth_date = LazyFunction(lambda: datetime.date(2020, 1, 1))


class AnimalTranslationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = AnimalTranslation
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid.uuid4)
    locale = Locale.en
    name = Sequence(lambda n: f"Animal {n}")
    caretaker_notes = None


class HealthLogFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = HealthLog
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid.uuid4)


class HealthLogTranslationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = HealthLogTranslation
        sqlalchemy_session_persistence = "flush"

    id = LazyFunction(uuid.uuid4)
    locale = Locale.en
    procedure_name = Sequence(lambda n: f"Procedure {n}")
    examination_findings = None
