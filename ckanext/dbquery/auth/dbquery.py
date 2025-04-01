from ckan.plugins import toolkit
import logging

log = logging.getLogger(__name__)


def dbquery_query_database(context, data_dict):
    log.warning(">>> ENTRANDO a dbquery_query_database <<<")
    user = context.get('auth_user_obj')
    if user and user.get('sysadmin'):
        return {'success': True}
    else:
        raise toolkit.NotAuthorized("Only sysadmins can run queries")


def dbquery_executed_list_auth(context, data_dict):
    log.warning(">>> ENTRANDO a dbquery_executed_list_auth <<<")
    user = context.get('auth_user_obj')
    if user and user.get('sysadmin'):
        return {'success': True}
    else:
        raise toolkit.NotAuthorized("Only sysadmins can list executed queries")
