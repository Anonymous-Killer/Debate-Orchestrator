from __future__ import annotations

from typing import Callable, Optional

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def create_db_engine(database_url: Optional[str] = None):
    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=settings.database_echo, connect_args=connect_args)


def create_session_factory(engine) -> Callable[[], Session]:
    def factory() -> Session:
        return Session(engine)

    return factory


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)
