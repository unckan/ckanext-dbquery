import datetime

from sqlalchemy import Column, types

from ckan import model
from ckan.plugins import toolkit

from ckan.model.types import make_uuid


class DBQueryExecuted(toolkit.BaseModel):
    """Model for storing executed queries by users."""

    __tablename__ = 'dbquery_executed'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    query = Column(types.UnicodeText, nullable=False)
    user_id = Column(types.UnicodeText, nullable=False)
    timestamp = Column(types.DateTime, default=datetime.datetime.utcnow)

    def dictize(self):
        return {
            'id': self.id,
            'query': self.query,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
        }

    def save(self):
        model.Session.add(self)
        model.Session.commit()
        model.Session.refresh(self)
        return self

    @classmethod
    def get_queries(user, date, limit=10):
        """
        Return a list of executed queries filtered by user and date
        """
        query = model.Session.query(DBQueryExecuted)
        if user:
            query = query.filter_by(user_id=user)
        if date:
            query = query.filter_by(timestamp=date)
        query = query.order_by(DBQueryExecuted.timestamp.desc())
        return query.limit(limit).all()
