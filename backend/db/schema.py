'''This module defines the database schema using SQLAlchemy ORM. Not the pydantic models. That is in models/.'''
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import Integer, JSON, String, DateTime
from datetime import datetime
from typing import Optional, Any

from backend.core.config import config

engine = create_engine(
    config.db_url,
    # PostgreSQL optimized settings
    pool_pre_ping=True,          # Verify connections before use - prevents stale connections
    pool_size=20,                # Base connection pool size (good for moderate concurrency)
    max_overflow=30,             # Additional connections allowed beyond pool_size
    pool_timeout=30,             # Wait up to 30 seconds for a connection from the pool
    pool_recycle=3600,           # Recycle connections after 1 hour (PostgreSQL default)
    echo=config.log_level == "WARNING" or config.log_level == "ERROR",
    # PostgreSQL connection arguments for performance
    connect_args={
        "connect_timeout": 10,           # Connection timeout in seconds
        "options": "-c timezone=utc",    # Set timezone to UTC
        "application_name": config.app_name,  # Helps identify connections in pg_stat_activity
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    '''
    args:
        id: int - primary key
        username: str - unique username
        email: str - user's email
        hashed_password: str - hashed password for authentication
        full_name: str - user's full name
        disabled: bool - indicates if the user is active

        categories: [dict[str, Any]] - [category={"name": "", "color":"value", }, category..]
        tags: [dict[str, Any]] - [tag={"name": "", "color":"value", }, tag..]
    '''
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, index=True)
    disabled: Mapped[bool] = mapped_column(default=False)

    categories: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    tags: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    dueDate: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    parameters: Mapped[str] = mapped_column(JSON)  # Store JSON as string
    completed: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    