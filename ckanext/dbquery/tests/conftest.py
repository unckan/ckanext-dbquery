import pytest
from ckan.tests import factories


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for('dbquery')


@pytest.fixture
def normal_user():
    user = factories.UserWithToken()
    return user


@pytest.fixture
def sysadmin():
    user = factories.SysadminWithToken()
    return user


@pytest.fixture
def mock_executed_queries(sysadmin):
    from ckanext.dbquery.model import DBQueryExecuted

    queries = [
        DBQueryExecuted(query="SELECT * FROM package", user_id=sysadmin['id']),
        DBQueryExecuted(query="SELECT * FROM user", user_id=sysadmin['id']),
    ]
    for q in queries:
        q.save()

    return queries
