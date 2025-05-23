import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.dbquery.blueprints.dbquery import dbquery_bp
from ckanext.dbquery import actions, auth

log = logging.getLogger(__name__)


class DbqueryPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "dbquery")

    # IBlueprint: Registra el blueprint dbquery_bp
    def get_blueprint(self):
        return [dbquery_bp]

    # IActions
    def get_actions(self):
        return {
            "query_database": actions.query_database,
            "dbquery_executed_list": actions.dbquery_executed_list,
            "dbquery_executor_users_list": actions.dbquery_executor_users_list,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            "query_database": auth.dbquery_query_database,
            "dbquery_executed_list": auth.dbquery_executed_list_auth,
        }
