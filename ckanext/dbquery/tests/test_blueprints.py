import pytest
from bs4 import BeautifulSoup


@pytest.mark.usefixtures("clean_db")
@pytest.mark.ckan_config("ckan.plugins", "dbquery")
@pytest.mark.usefixtures("with_plugins")
class TestDBQueryBlueprints:

    def test_index_not_authorized(self, app, normal_user):
        """Test that non-sysadmin users can't access the index page."""
        auth = {"Authorization": normal_user['token']}
        response = app.get('/ckan-admin/db-query/', headers=auth)
        assert response.status_code == 403

    def test_index_authorized(self, app, sysadmin):
        """Test that sysadmin users can access the index page."""
        # Create a sysadmin user
        auth = {"Authorization": sysadmin['token']}
        response = app.get('/ckan-admin/db-query/', headers=auth)
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, 'html.parser')
        assert soup.find('h1', text='CKAN DB Query') is not None
        assert soup.find('textarea', id='query') is not None
        assert soup.find('button', type='submit', text='Run query') is not None

    def test_index_query_submission(self, app, sysadmin):
        """Test query submission through the form."""
        headers = {"Authorization": sysadmin['token']}
        response = app.post('/ckan-admin/db-query/', headers=headers, data={
            'query': 'SELECT id FROM package LIMIT 5'
        })
        assert response.status_code == 200

        # Check for result display
        soup = BeautifulSoup(response.data, 'html.parser')
        assert soup.find('div', class_='results-section') is not None
        assert soup.find('table', class_='table') is not None
        assert soup.find('th', text='id') is not None

    def test_history_not_authorized(self, app, normal_user):
        """Test that non-sysadmin users can't access the history page."""
        # Try to access the history page
        auth = {"Authorization": normal_user['token']}
        response = app.get('/ckan-admin/db-query/history', headers=auth)
        assert response.status_code == 403

    def test_history_authorized(self, app, mock_executed_queries, sysadmin):
        """Test that sysadmin users can access the history page."""

        headers = {"Authorization": sysadmin['token']}
        response = app.get('/ckan-admin/db-query/history', headers=headers)
        assert response.status_code == 200

        # Check content
        soup = BeautifulSoup(response.data, 'html.parser')

        # Check for important elements
        assert soup.find('h1', text='Query Execution History') is not None
        assert soup.find('table', class_='table') is not None

        # Check for query rows
        rows = soup.find_all('tr')
        assert len(rows) > 2  # Header + at least two query rows
