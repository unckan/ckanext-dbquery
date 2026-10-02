import pytest
from ckan.tests import helpers
from ckan.plugins import toolkit
from ckanext.dbquery.model import DBQueryExecuted


@pytest.mark.usefixtures("clean_db")
class TestQueryDatabaseAction:

    def test_query_database_not_authorized(self, normal_user):
        """Test that non-sysadmin users can't run queries."""
        context = {'user': normal_user['name'], 'ignore_auth': False}

        data_dict = {
            'query': 'SELECT * FROM package LIMIT 5',
        }

        # Ensure NotAuthorized is raised
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action('query_database', context, **data_dict)

    def test_query_database_success(self, sysadmin):
        """Test successful query execution."""
        context = {'user': sysadmin['name'], 'ignore_auth': False}

        data_dict = {
            'query': 'SELECT id FROM package LIMIT 5',
        }

        result = helpers.call_action('query_database', context, **data_dict)

        # Check response structure
        assert 'rows' in result
        assert 'colnames' in result
        assert 'message' in result
        assert len(result['colnames']) > 0
        assert 'id' in result['colnames']

        # Check that query was saved
        saved_query = helpers.model.Session.query(DBQueryExecuted).first()
        assert saved_query is not None
        assert saved_query.query == data_dict['query']

    def test_query_database_invalid_query(self, sysadmin):
        """Test handling of invalid SQL queries."""
        context = {
            'user': sysadmin['name'],
            'ignore_auth': False
        }

        data_dict = {
            'query': 'SELECT * FROM non_existent_table',
        }

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('query_database', context, **data_dict)

    def test_dbquery_executed_list_not_authorized(self, normal_user):
        """Test that non-sysadmin users can't list executed queries."""
        context = {
            'user': normal_user['name'],
            'ignore_auth': False
        }

        # Ensure NotAuthorized is raised
        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action('dbquery_executed_list', context)

    def test_dbquery_executed_list_success(self, sysadmin, mock_executed_queries):
        """Test successful listing of executed queries."""
        context = {
            'user': sysadmin['name'],
            'ignore_auth': False
        }

        result = helpers.call_action('dbquery_executed_list', context)

        # Check result
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)
        assert all('query' in item for item in result)
        assert all('user_id' in item for item in result)
        assert all('timestamp' in item for item in result)

        # Check order (newest first)
        timestamps = [item['timestamp'] for item in result]
        assert timestamps[0] >= timestamps[1]


@pytest.mark.usefixtures("clean_db")
class TestQueryTransactions:
    @pytest.fixture
    def query_table(self):
        from sqlalchemy import text
        engine = helpers.model.meta.engine
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE dbquery_transaction_test (id INTEGER PRIMARY KEY)"))
        try:
            yield
        finally:
            with engine.begin() as connection:
                connection.execute(text("DROP TABLE dbquery_transaction_test"))

    def test_writes_commit_and_returning_rows_survive_connection_close(self, query_table, sysadmin):
        context = {'user': sysadmin['name'], 'ignore_auth': False}
        result = helpers.call_action('query_database', context,
                                     query='INSERT INTO dbquery_transaction_test VALUES (1)')
        assert result == {'rows': [], 'colnames': [], 'message': 'Query affected 1 rows'}
        result = helpers.call_action('query_database', context,
                                     query='INSERT INTO dbquery_transaction_test VALUES (2) RETURNING id')
        assert result['rows'] == [{'id': 2}]
        assert result['colnames'] == ['id']
        result = helpers.call_action('query_database', context,
                                     query='SELECT id FROM dbquery_transaction_test ORDER BY id')
        assert result['rows'] == [{'id': 1}, {'id': 2}]
        assert helpers.model.Session.query(DBQueryExecuted).count() == 3

    def test_failed_query_rolls_back_and_next_query_works(self, query_table, sysadmin):
        context = {'user': sysadmin['name'], 'ignore_auth': False}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('query_database', context, query=(
                'INSERT INTO dbquery_transaction_test VALUES (1); '
                'INSERT INTO dbquery_transaction_test VALUES (1)'
            ))
        result = helpers.call_action('query_database', context,
                                     query='SELECT id FROM dbquery_transaction_test')
        assert result['rows'] == []
        assert result['colnames'] == ['id']
        assert helpers.model.Session.query(DBQueryExecuted).count() == 1
