from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        class_name = cls.__name__.lower()
        if class_name.endswith("y"):
            return class_name[:-1] + "ies"
        if class_name.endswith(("s", "x", "z", "ch", "sh")):
            return class_name + "es"
        return class_name + "s"

    def __repr__(self) -> str:
        column_values = [f"{column_name}={getattr(self, column_name)}" for column_name in self.__table__.columns.keys()]
        return f"{self.__class__.__name__}, table_name={self.__tablename__} ({', '.join(column_values)})"

    @classmethod
    def subject(cls) -> str:
        return cls.__tablename__
