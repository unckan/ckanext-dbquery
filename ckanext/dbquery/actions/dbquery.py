
import ckan.plugins.toolkit as toolkit
from ckan.logic import NotAuthorized


def dbquery_execute(context, data_dict):
    """
    Ejecuta una consulta básica en la tabla especificada.
    """
    session = context['session']

    # Verificar permisos
    if not context.get('ignore_auth'):
        raise NotAuthorized("No tiene permiso para ejecutar esta consulta.")

    table_name = data_dict.get('table')
    if not table_name:
        raise toolkit.ValidationError("Debe especificar una tabla.")

    # Ejecutar consulta simple
    query = f"SELECT * FROM {table_name} LIMIT 10;"
    result = session.execute(query)
    return [dict(row) for row in result]
