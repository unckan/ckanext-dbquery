import logging
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

    resp = {
        "rows": rows,
        "colnames": colnames,
        "result_obj": result,
        "message": message,
    }

    return resp
