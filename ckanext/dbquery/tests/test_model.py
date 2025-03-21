import pytest
import datetime
from ckan import model
from ckanext.dbquery.model import DBQueryExecuted


class TestDBQueryExecutedModel:
    
    def test_init_model(self):
        """Test model initialization."""
        query = DBQueryExecuted(
            query="SELECT * FROM test",
            user_id="test_user"
        )
        
        assert query.query == "SELECT * FROM test"
        assert query.user_id == "test_user"
        assert isinstance(query.timestamp, datetime.datetime)
        assert query.id is not None
        
    def test_dictize(self):
        """Test dictize method."""
        query = DBQueryExecuted(
            query="SELECT * FROM test",
            user_id="test_user"
        )
        
        dict_result = query.dictize()
        
        assert dict_result['query'] == "SELECT * FROM test"
        assert dict_result['user_id'] == "test_user"
        assert 'timestamp' in dict_result
        assert 'id' in dict_result
        
    def test_save(self, clean_db):
        """Test save method."""
        query = DBQueryExecuted(
            query="SELECT * FROM test",
            user_id="test_user"
        )
        
        saved_query = query.save()
        
        # Verify it was saved to DB by retrieving it
        retrieved_query = model.Session.query(DBQueryExecuted).get(saved_query.id)
        assert retrieved_query is not None
        assert retrieved_query.query == "SELECT * FROM test"
        
    def test_get_queries(self, clean_db, mock_executed_queries):
        """Test get_queries method."""
        # Get without filters
        queries = DBQueryExecuted.get_queries(user=None, date=None, limit=10)
        assert len(queries) == 2
        
        # Get with user filter
        user_id = mock_executed_queries[0].user_id
        queries = DBQueryExecuted.get_queries(user=user_id, date=None, limit=10)
        assert len(queries) == 2
        assert all(q.user_id == user_id for q in queries)
        
        # Get with limit
        queries = DBQueryExecuted.get_queries(user=None, date=None, limit=1)
        assert len(queries) == 1
        
        # Test ordering (most recent first)
        assert queries[0].id == mock_executed_queries[1].id
