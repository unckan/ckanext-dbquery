import logging
import os
import psycopg2
from psycopg2 import sql
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.dbquery.blueprints.dbquery import dbquery_bp
from ckanext.dbquery.actions import dbquery as dbquery_actions
from ckanext.dbquery.auth import dbquery as dbquery_auth

log = logging.getLogger(__name__)


def query_database(query, params=None):
    """ Realiza una consulta a la base de datos y retorna los resultados """
    # Obtén los parámetros de conexión desde la configuración (puedes definirlos en ckan.ini)
    dbname = toolkit.config.get('dbquery.dbname', 'tu_base')
    user = toolkit.config.get('dbquery.user', 'tu_usuario')
    password = toolkit.config.get('dbquery.password', 'tu_password')
    host = toolkit.config.get('dbquery.host', 'localhost')
    port = toolkit.config.get('dbquery.port', '5432')

    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()

        # Ejecutar la consulta con parámetros seguros
        cur.execute(query, params or {})
        rows = cur.fetchall()

        # Obtener nombres de columnas
        colnames = [desc[0] for desc in cur.description]

        cur.close()
        conn.close()

    except Exception as e:
        log.error("Error al realizar la consulta a la base de datos: %s", e)
        raise

    return [dict(zip(colnames, row)) for row in rows]


class DbqueryPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        templates_path = os.path.join(os.path.dirname(__file__), 'templates')
        log.info("Registrando templates en: %s", templates_path)
        toolkit.add_template_directory(config_, templates_path)
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "dbquery")

    # IBlueprint: Registra el blueprint dbquery_bp
    def get_blueprint(self):
        return dbquery_bp

    # IActions
    def get_actions(self):
        return {
            "dbquery_execute": dbquery_actions.dbquery_execute,
            "custom_query": self.custom_query,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            "dbquery_execute": dbquery_auth.dbquery_execute,
            "dbquery_custom_query": dbquery_auth.dbquery_execute,
        }

    @staticmethod
    def custom_query(context, data_dict):
        """
        Realiza una consulta SQL basada en una query de búsqueda.
        
        Parámetros esperados en data_dict:
        - 'query': query de búsqueda (ej. "economía", "autos", "escuelas")
        - 'limit': número máximo de resultados (opcional, por defecto 10)
        
        Devuelve:
        - Lista de registros que coinciden con la query.
        """
        query = data_dict.get('query')
        limit = data_dict.get('limit', 10)  # Valor por defecto si no se especifica

        if not query:
            raise toolkit.ValidationError("Debe proporcionar un valor en 'query'.")

        query = """
            SELECT * FROM my_table
            WHERE query ILIKE %(query)s
            LIMIT %(limit)s
        """
        
        params = {
            "query": f"%{query}%",  # Búsqueda parcial
            "limit": limit
        }

        return query_database(query, params)
