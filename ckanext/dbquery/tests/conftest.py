import os
import pytest
import ckan.tests.factories as factories
import ckan.model as model
from ckan.tests.helpers import reset_db
from ckanext.dbquery.model import DBQueryExecuted


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for('dbquery')


@pytest.fixture(autouse=True)
def load_standard_plugins(with_plugins):
    """ Use 'with_plugins' fixture in ALL tests """
    pass


@pytest.fixture
def sysadmin_user():
    """Create a sysadmin user."""
    user = factories.Sysadmin()
    return user


@pytest.fixture
def normal_user():
    """Create a normal user."""
    user = factories.User()
    return user


@pytest.fixture
def mock_executed_queries():
    """Create some mock executed queries."""
    user = factories.User()
    
    queries = [
        DBQueryExecuted(
            query="SELECT * FROM package",
            user_id=user['id']
        ),
        DBQueryExecuted(
            query="SELECT * FROM user",
            user_id=user['id']
        ),
    ]
    
    for query in queries:
        query.save()
    
    return queries


@pytest.fixture
def app():
    """Return a WSGI application for use by tests."""
    from ckan.config.middleware import make_app
    from ckan.cli import load_config
    
    config = load_config('/path/to/test.ini')
    app = make_app(config)
    return app
