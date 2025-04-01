import pytest
from ckan import model
from ckan.tests import factories


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for('dbquery')

    # Forzar creación de tabla del modelo si no hay migraciones
    from ckanext.dbquery.model import DBQueryExecuted
    DBQueryExecuted.__table__.create(model.meta.engine, checkfirst=True)


@pytest.fixture
def normal_user():
    user = factories.User()
    return user


@pytest.fixture
def mock_executed_queries(clean_db, sysadmin):
    from ckanext.dbquery.model import DBQueryExecuted

    queries = [
        DBQueryExecuted(query="SELECT * FROM package", user_id=sysadmin['id']),
        DBQueryExecuted(query="SELECT * FROM user", user_id=sysadmin['id']),
    ]
    for q in queries:
        q.save()

    return queries
