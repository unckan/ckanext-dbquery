import datetime

from sqlalchemy import types, Column, Table
from sqlalchemy.ext.declarative import declarative_base

from ckan.model.meta import metadata, Session
from ckan.model.types import make_uuid

Base = declarative_base()

__all__ = ['DBQueryExecuted', 'dbquery_executed_table', 'setup']

dbquery_executed_table = Table(
    'dbquery_executed',
    metadata,
    Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    Column('query', types.UnicodeText, nullable=False),
    Column('user_id', types.UnicodeText, nullable=False),
    Column('timestamp', types.DateTime, default=datetime.datetime.utcnow),
)


class DBQueryExecuted(Base):
    """Model for storing executed queries by users."""

    __tablename__ = 'dbquery_executed'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    query = Column(types.UnicodeText, nullable=False)
    user_id = Column(types.UnicodeText, nullable=False)
    timestamp = Column(types.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def create(cls, query, user_id):
        """Create a new record of executed query."""
        query_record = DBQueryExecuted(
            query=query,
            user_id=user_id
        )
        Session.add(query_record)
        Session.commit()
        return query_record

    @classmethod
    def get_all(cls):
        """Return all executed queries."""
        return Session.query(cls).all()

    @classmethod
    def get_by_user(cls, user_id):
        """Return all queries executed by a specific user."""
        return Session.query(cls).filter(cls.user_id == user_id).all()


def setup():
    """Initialize the model."""
    if not dbquery_executed_table.exists():
        dbquery_executed_table.create()
        # Mapped classes need to be available for mapper
        DBQueryExecuted()
