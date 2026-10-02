import sqlite3
from unittest.mock import Mock

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
class TestSeparateQueryConnection:
    @pytest.fixture
    def reader(self, tmp_path, monkeypatch):
        database = tmp_path / "queries.db"
        with sqlite3.connect(str(database)) as connection:
            connection.execute("CREATE TABLE reader_data (value TEXT)")
            connection.execute("INSERT INTO reader_data VALUES ('separate database')")
        url = f"sqlite:///file:{database}?mode=ro&uri=true"
        monkeypatch.setitem(toolkit.config, 'ckanext.dbquery.sqlalchemy.url', url)
        return database

    def test_separate_connection_and_ckan_history(self, reader, sysadmin):
        query = 'SELECT value FROM reader_data'
        result = helpers.call_action('query_database',
                                     {'user': sysadmin['name'], 'ignore_auth': False},
                                     query=query)
        assert result['rows'] == [{'value': 'separate database'}]
        assert result['colnames'] == ['value']
        assert result['message'] == 'Query returned 1 rows'
        saved = helpers.model.Session.query(DBQueryExecuted).one()
        assert saved.query == query
        assert saved.user_id == sysadmin['id']

    @pytest.mark.parametrize('query', [
        'DELETE FROM reader_data',
        'DROP TABLE reader_data',
    ])
    def test_readonly_database_rejects_writes(self, reader, sysadmin, query):
        context = {'user': sysadmin['name'], 'ignore_auth': False}
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('query_database', context, query=query)
        result = helpers.call_action('query_database', context,
                                     query='SELECT value FROM reader_data')
        assert result['rows'] == [{'value': 'separate database'}]
        assert helpers.model.Session.query(DBQueryExecuted).count() == 1

    @pytest.mark.parametrize('url', [
        'invalid-url-with-secret',
        'sqlite:////nonexistent-dbquery-directory/database.db',
    ])
    def test_configured_failure_never_falls_back(self, monkeypatch, sysadmin, url):
        monkeypatch.setitem(toolkit.config, 'ckanext.dbquery.sqlalchemy.url', url)
        engine = Mock()
        monkeypatch.setattr(helpers.model.meta, 'engine', engine)
        with pytest.raises(toolkit.ValidationError) as error:
            helpers.call_action('query_database',
                                {'user': sysadmin['name'], 'ignore_auth': False},
                                query='SELECT 1')
        engine.execute.assert_not_called()
        assert url not in str(error.value)

    def test_empty_url_uses_ckan(self, monkeypatch, sysadmin):
        monkeypatch.setitem(toolkit.config, 'ckanext.dbquery.sqlalchemy.url', '')
        result = helpers.call_action('query_database',
                                     {'user': sysadmin['name'], 'ignore_auth': False},
                                     query='SELECT id FROM package LIMIT 1')
        assert result['colnames'] == ['id']
