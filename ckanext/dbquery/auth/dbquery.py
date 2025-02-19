from ckan.logic import NotAuthorized


def dbquery_execute(context, data_dict):
    """
    Verifica si el usuario puede ejecutar consultas DBQuery.
    """
    user = context.get('user')
    if user == 'admin':  # Ejemplo simple
        return {'success': True}
    else:
        raise NotAuthorized("No tiene permiso para ejecutar esta acción.")
