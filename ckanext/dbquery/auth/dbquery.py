import ckan.plugins.toolkit as toolkit


def dbquery_execute(context, data_dict):
    """
    Verifica si el usuario puede ejecutar consultas DBQuery.
    Solo sysadmins pueden ejecutar consultas.
    """
    # Check if user is a sysadmin
    user_obj = context.get('auth_user_obj')

    if user_obj and user_obj.sysadmin:
        return {'success': True}
    else:
        return {'success': False, 'msg': toolkit._('Necesita ser administrador del sistema para ejecutar consultas.')}
