import logging
import datetime
from ckanext.dbquery.model import DBQueryExecuted
from sqlalchemy.sql.expression import text
from sqlalchemy import func
from ckan import model
from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def query_database(context, data_dict):
    """Execute a database query and return the results using CKAN's session."""
    toolkit.check_access('query_database', context, data_dict)

    query = data_dict.get('query')
    # Use CKAN's SQLAlchemy session
    engine = model.meta.engine

    try:
        text_sql = text(query)
        result = engine.execute(text_sql)
    except Exception as e:
        log.critical(f"Error executing query {query}: {e}")
        raise toolkit.ValidationError({"query": f"Invalid Query: {e}"})

    # Check if it's a SELECT query that returns rows
    has_results = result.returns_rows
    # Delete or update queries don't return results
    if has_results:
        rows = result.fetchall()
        colnames = result.keys()
        message = f"Query returned {len(rows)} rows"
    else:
        rows = []
        colnames = []
        message = f"Query affected {result.rowcount} rows"

    # Save executed query
    user_id = context['auth_user_obj']['id']
    executed = DBQueryExecuted(
        query=query,
        user_id=user_id
    )
    executed.save()

    resp = {
        "rows": [dict(zip(colnames, row)) for row in rows],
        "colnames": colnames,
        "message": message,
    }

    return resp


@toolkit.side_effect_free
def dbquery_executed_list(context, data_dict):
    """
    Return a list of all executed queries ordered by timestamp descending
    """
    # Check if user is authorized
    toolkit.check_access('query_database', context, data_dict)

    # Get filter parameters
    user_filter = data_dict.get('user')
    date_filter = data_dict.get('date')
    limit = int(data_dict.get('limit', 10))

    # Get all executed queries
    queries = model.Session.query(DBQueryExecuted)

    # Apply filters if provided
    if user_filter:
        queries = queries.filter(DBQueryExecuted.user_id == user_filter)

    if date_filter:
        # date_filter is a string in the format YYYY-MM-DD
        # we want queries from that exact date
        date_obj = datetime.datetime.strptime(date_filter, "%Y-%m-%d").date()
        # Use PostgreSQL's DATE function to extract just the date part
        queries = queries.filter(func.date(DBQueryExecuted.timestamp) == date_obj)

    queries = queries.order_by(DBQueryExecuted.timestamp.desc())
    if limit:
        queries = queries.limit(limit)  # Use SQLAlchemy's limit() method instead of Python slicing

    queries = queries.all()
    # Convert to dictionaries
    result = [query.dictize() for query in queries]

    return result


@toolkit.side_effect_free
def dbquery_executor_users_list(context, data_dict):
    """ Get a list of users that have executed queries """
    # Check if user is authorized
    toolkit.check_access('query_database', context, data_dict)

    # Get distinct users with names by joining with the user table
    query = model.Session.query(
        model.User.id.label('id'),
        model.User.name.label('name')
    ).join(
        DBQueryExecuted, DBQueryExecuted.user_id == model.User.id
    ).distinct()

    # Convert to list of user dictionaries
    result = [
        {'id': user.id, 'name': user.name}
        for user in query.all()
    ]

    return result
