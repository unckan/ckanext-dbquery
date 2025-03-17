import logging
import datetime
from ckanext.dbquery.model import DBQueryExecuted
from sqlalchemy.sql.expression import text
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
    if context.get('user'):
        executed = DBQueryExecuted(
            query=query,
            user_id=context.get('user')
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
    limit = data_dict.get('limit')

    # Get all executed queries
    queries = DBQueryExecuted.get_all_ordered_by_timestamp_desc()

    # Apply filters if provided
    if user_filter:
        queries = [q for q in queries if user_filter.lower() in q.user_id.lower()]

    if date_filter:
        date_obj = datetime.datetime.strptime(date_filter, '%Y-%m-%d').date()
        queries = [q for q in queries if q.timestamp.date() == date_obj]

    # Apply limit if provided
    if limit and isinstance(limit, int):
        queries = queries[:limit]

    # Convert to dictionaries
    result = [query.dictize() for query in queries]

    return result
