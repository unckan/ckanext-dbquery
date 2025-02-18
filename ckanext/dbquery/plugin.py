import logging
import psycopg2
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)


def query_database():
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
        cur.execute("SELECT * FROM tu_tabla LIMIT 10")
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        log.error("Error al realizar la consulta a la base de datos: %s", e)
        raise

    return [{"columna1": row[0], "columna2": row[1]} for row in rows]


class DbqueryPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "dbquery")

    # IActions: Registra la acción custom 'custom_query'
    def get_actions(self):
        return {
            "custom_query": DbqueryPlugin.custom_query
        }

    @staticmethod
    def custom_query(context, data_dict):
        """Realiza una consulta a la base de datos y retorna los resultados."""
        return query_database()
