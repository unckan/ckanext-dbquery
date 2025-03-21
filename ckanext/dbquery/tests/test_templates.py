import pytest
from bs4 import BeautifulSoup
import ckan.tests.helpers as helpers


@pytest.mark.usefixtures("clean_db")
class TestDBQueryTemplates:

    def test_index_template(self, app, sysadmin_user):
        """Test index.html template renders correctly."""
        helpers.call_action('user_create', name=sysadmin_user['name'],
                            email=sysadmin_user['email'], password='password', sysadmin=True)

        with app.flask_app.test_client() as client:
            # Login as sysadmin
            client.post('/user/login', data={'login': sysadmin_user['name'], 'password': 'password'})

            # Render the template
            response = client.get('/ckan-admin/db-query/')
            assert response.status_code == 200

            soup = BeautifulSoup(response.data, 'html.parser')

            # Check for required elements
            assert soup.find('h1', text='CKAN DB Query') is not None
            assert soup.find('textarea', {'id': 'query', 'name': 'query'}) is not None
            assert soup.find('button', {'type': 'submit', 'class': 'btn btn-primary'}) is not None
            assert soup.find('button', {'id': 'reset-query-btn'}) is not None

            # Check for sidebar elements
            assert soup.find('h1', {'class': 'page-heading'}, text='DB Query Tools') is not None
            assert soup.find('a', text='Show executed queries') is not None

    def test_history_template(self, app, sysadmin_user, mock_executed_queries):
        """Test history.html template renders correctly."""
        helpers.call_action('user_create', name=sysadmin_user['name'],
                            email=sysadmin_user['email'], password='password', sysadmin=True)

        with app.flask_app.test_client() as client:
            # Login as sysadmin
            client.post('/user/login', data={'login': sysadmin_user['name'], 'password': 'password'})

            # Render the template
            response = client.get('/ckan-admin/db-query/history')
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

    def test_queries_template(self, app, sysadmin_user, mock_executed_queries):
        """Test queries.html template renders correctly."""
        helpers.call_action('user_create', name=sysadmin_user['name'],
                            email=sysadmin_user['email'], password='password', sysadmin=True)

        with app.flask_app.test_client() as client:
            # Login as sysadmin
            client.post('/user/login', data={'login': sysadmin_user['name'], 'password': 'password'})

            from ckan.common import c
            # Prepare context
            queries = [q.dictize() for q in mock_executed_queries]

            # Set up test app context
            with app.flask_app.test_request_context():
                # Set up context
                c.userobj = sysadmin_user

                # Render template
                from ckan.lib.base import render
                html = render('dbquery/queries.html', extra_vars={'queries': queries})

                soup = BeautifulSoup(html, 'html.parser')

                # Check for required elements
                assert soup.find('h1', {'class': 'page-heading'}, text='Executed Queries') is not None
                assert soup.find('table', {'class': 'table'}) is not None

                # Check table headers
                headers = [th.text.strip() for th in soup.find('thead').find_all('th')]
                assert 'ID' in headers
                assert 'User' in headers
                assert 'Query' in headers
                assert 'Timestamp' in headers

                # Check query entries - should have at least 2 rows in tbody
                rows = soup.find('tbody').find_all('tr')
                assert len(rows) == 2
