from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all OfficeHub models (imported by each module's models.py)."""
