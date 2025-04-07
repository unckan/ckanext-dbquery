import logging
import datetime
from ckanext.dbquery.model import DBQueryExecuted
from sqlalchemy.sql.expression import text
from sqlalchemy import func
from ckan import model
from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def query_database(context, data_dict):
    """ Realiza una consulta a la base de datos y retorna los resultados usando la sesión de CKAN"""

    toolkit.check_access('query_database', context, data_dict)

    query = data_dict.get('query')
    # Usar la sesión SQLAlchemy de CKAN en lugar de crear una nueva conexión
    engine = model.meta.engine

    try:
        text_sql = text(query)
        result = engine.execute(text_sql)
    except Exception as e:
        log.critical(f"Error al ejecutar la consulta {query}: {e}")
        raise toolkit.ValidationError({"query": f"Invalid Query {e}"})

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
    user = context['auth_user_obj']
    executed = DBQueryExecuted(
        query=query,
        user_id=user.id
    )
    executed.save()

    resp = {
        "rows": rows,
        "colnames": colnames,
        "result_obj": result,
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
