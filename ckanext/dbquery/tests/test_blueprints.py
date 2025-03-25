import pytest
import ckan.tests.helpers as helpers
from bs4 import BeautifulSoup


@pytest.mark.usefixtures("clean_db")
@pytest.mark.ckan_config("ckan.plugins", "dbquery")
@pytest.mark.usefixtures("with_plugins")
class TestDBQueryBlueprints:

    def test_index_not_authorized(self, app, normal_user):
        """Test that non-sysadmin users can't access the index page."""
        helpers.call_action('user_create', name=normal_user['name'],
                            email=normal_user['email'], password='password')

        with app.flask_app.test_client() as client:
            # Login as normal user
            client.post('/user/login', data={'login': normal_user['name'], 'password': 'password'})

            # Try to access the DB query page
            response = client.get('/ckan-admin/db-query/')
            assert response.status_code == 403

    def test_index_authorized(self, app, sysadmin):
        """Test that sysadmin users can access the index page."""

        with app.flask_app.test_client() as client:
            # Login as sysadmin
            client.post('/user/login', data={'login': sysadmin['name'], 'password': 'password'})

            # Access the DB query page
            response = client.get('/ckan-admin/db-query/')
            assert response.status_code == 200

            # Check content
            soup = BeautifulSoup(response.data, 'html.parser')

            # Check for important elements
            assert soup.find('h1', text='CKAN DB Query') is not None
            assert soup.find('textarea', id='query') is not None
            assert soup.find('button', type='submit', text='Run query') is not None

    def test_index_query_submission(self, app, sysadmin):
        """Test query submission through the form."""

        with app.flask_app.test_client() as client:
            # Login as sysadmin
            client.post('/user/login', data={'login': sysadmin['name'], 'password': 'password'})

            # Submit a query
            response = client.post('/ckan-admin/db-query/', data={
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
        helpers.call_action('user_create', name=normal_user['name'],
                            email=normal_user['email'], password='password')

        with app.flask_app.test_client() as client:
            # Login as normal user
            client.post('/user/login', data={'login': normal_user['name'], 'password': 'password'})

            # Try to access the history page
            response = client.get('/ckan-admin/db-query/history')
            assert response.status_code == 403

    def test_history_authorized(self, app, sysadmin, mock_executed_queries):
        """Test that sysadmin users can access the history page."""

        with app.flask_app.test_client() as client:
            # Login as sysadmin
            client.post('/user/login', data={'login': sysadmin['name'], 'password': 'password'})

            # Access the history page
            response = client.get('/ckan-admin/db-query/history')
            assert response.status_code == 200

            # Check content
            soup = BeautifulSoup(response.data, 'html.parser')

            # Check for important elements
            assert soup.find('h1', text='Query Execution History') is not None
            assert soup.find('table', class_='table') is not None

            # Check for query rows
            rows = soup.find_all('tr')
            assert len(rows) > 2  # Header + at least two query rows
