import pytest
from bs4 import BeautifulSoup


@pytest.mark.usefixtures("clean_db")
class TestDBQueryTemplates:

    def test_index_template(self, app, sysadmin):
        """Test index.html template renders correctly."""

        headers = {"Authorization": sysadmin['token']}
        response = app.get('/ckan-admin/db-query/', headers=headers)
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, 'html.parser')

        # Check for required elements
        assert soup.find('h1', text='CKAN DB Query') is not None
        assert soup.find('textarea', {'id': 'query', 'name': 'query'}) is not None
        assert soup.find('button', {'type': 'submit', 'class': 'btn btn-primary'}) is not None
        assert soup.find('button', {'id': 'reset-query-btn'}) is not None

        # Check for sidebar elements
        assert soup.find('h1', {'class': 'page-heading'}, text='DB Query Tools') is not None
        assert soup.find('a', string=lambda s: s and 'Show executed queries' in s) is not None

    def test_history_template(self, app, mock_executed_queries, sysadmin):
        """Test history.html template renders correctly."""

        headers = {"Authorization": sysadmin['token']}
        response = app.get('/ckan-admin/db-query/history', headers=headers)
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, 'html.parser')

        # Check for required elements
        assert soup.find('h1', text='Query Execution History') is not None
        assert soup.find('table', {'class': 'table'}) is not None

        # Check table headers
        headers = [th.text.strip() for th in soup.find('thead').find_all('th')]
        assert 'ID' in headers
        assert 'User' in headers
        assert 'Query' in headers
        assert 'Timestamp' in headers

        # Check query entries
        query_cells = soup.find_all('pre', {'class': 'query-preview'})
        assert len(query_cells) == 2
        query_texts = [cell.text.strip() for cell in query_cells]
        assert "SELECT * FROM package" in query_texts
        assert "SELECT * FROM user" in query_texts

    @pytest.mark.usefixtures("clean_db")
    def test_invalid_sql_query_shows_error_message(self, app, sysadmin):
        """
        Verifies that an invalid SQL query (such as a non-existent table)
        does not generate a 500 error and displays an error message to the user in the interface.
        """
        auth = {"Authorization": sysadmin['token']}

        response = app.post(
            '/ckan-admin/db-query/',
            params={'query': 'SELECT * FROM non_existent_table'},
            headers=auth,
            status=200
        )

        html = response.text

        assert "Invalid Query" in html
