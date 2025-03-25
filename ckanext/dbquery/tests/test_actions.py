import pytest
from ckan.tests import helpers
from ckan.plugins import toolkit
from ckanext.dbquery.model import DBQueryExecuted


@pytest.mark.ckan_config("ckan.plugins", "dbquery")
@pytest.mark.usefixtures("with_plugins")
class TestQueryDatabaseAction:

    def test_query_database_not_authorized(self, clean_db, normal_user):
        """Test that non-sysadmin users can't run queries."""
        context = {
            'user': normal_user['name'],
            'auth_user_obj': normal_user,
        }

        data_dict = {
            'query': 'SELECT * FROM package LIMIT 5'
        }

        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action('query_database', context, **data_dict)

    def test_query_database_success(self, clean_db, sysadmin):
        """Test successful query execution."""
        context = {
            'user': sysadmin['name'],
            'auth_user_obj': sysadmin,
        }

        data_dict = {
            'query': 'SELECT id FROM package LIMIT 5'
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
        assert saved_query.user_id == sysadmin['id']

    def test_query_database_invalid_query(self, clean_db, sysadmin):
        """Test handling of invalid SQL queries."""
        context = {
            'user': sysadmin['name'],
            'auth_user_obj': sysadmin,
        }

        data_dict = {
            'query': 'SELECT * FROM non_existent_table'
        }

        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('query_database', context, **data_dict)


class TestDBQueryExecutedListAction:

    def test_dbquery_executed_list_not_authorized(self, clean_db, normal_user):
        """Test that non-sysadmin users can't list executed queries."""
        context = {
            'user': normal_user['name'],
            'auth_user_obj': normal_user,
        }

        with pytest.raises(toolkit.NotAuthorized):
            helpers.call_action('dbquery_executed_list', context)

    def test_dbquery_executed_list_success(self, clean_db, sysadmin, mock_executed_queries):
        """Test successful listing of executed queries."""
        context = {
            'user': sysadmin['name'],
            'auth_user_obj': sysadmin,
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
