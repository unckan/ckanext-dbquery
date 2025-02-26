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
    dbname = toolkit.config.get('dbquery.dbname', 'ckan_test')
    user = toolkit.config.get('dbquery.user', 'ckan_default')
    password = toolkit.config.get('dbquery.password', 'pass')
    host = toolkit.config.get('dbquery.host', 'postgresql_uni')
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
        log.info("Ejecutando consulta: %s", query)

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
        Realiza una búsqueda en la base de datos:
        1) Tablas cuyo nombre coincida con el texto.
        2) Columnas cuyo nombre coincida con el texto.
        3) Filas de cualquier tabla y columna (de tipo texto) que coincida con el texto.

        data_dict:
        - "query": texto de búsqueda (obligatorio)
        - "limit_rows": límite de filas a mostrar por tabla-columna (opcional, default=5)

        Retorna un diccionario con:
        {
            "tables": [...],
            "columns": [...],
            "rows": [
            {
                "table": "nombre_tabla",
                "column": "nombre_columna",
                "matches": [ ... filas encontradas ... ]
            },
            ...
            ]
        }
        """
        query = data_dict.get('query')
        if not query:
            raise toolkit.ValidationError("Debe proporcionar 'query' en data_dict.")

        limit_rows = data_dict.get('limit_rows', 50)

        # 1) Buscar tablas que coincidan con el texto
        query_tables = sql.SQL("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name ILIKE %s
        """)
        tables_found = query_database(query_tables, (f"%{query}%", ))

        # 2) Buscar columnas que coincidan con el texto
        query_columns = sql.SQL("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND column_name ILIKE %s
        """)
        columns_found = query_database(query_columns, (f"%{query}%", ))

        # 3) Buscar filas que coincidan en cualquier tabla/columna de tipo texto
        #    3.1) Primero obtener todas las columnas de tipo texto
        query_text_columns = sql.SQL("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND data_type IN ('character varying', 'text')
        """)
        text_columns = query_database(query_text_columns)

        row_matches = []
        for tc in text_columns:
            table_name = tc["table_name"]
            column_name = tc["column_name"]

            # Construir consulta dinámica
            query_sql = sql.SQL("""
                SELECT *
                FROM {table}
                WHERE {column} ILIKE %s
                LIMIT %s
            """).format(
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name)
            )
            try:
                rows = query_database(query_sql, (f"%{query}%", limit_rows))
            except Exception as e:
                # Es posible que algunas tablas no tengan permisos o existan restricciones
                log.warning(f"Error consultando {table_name}.{column_name}: {e}")
                rows = []

            if rows:
                row_matches.append({
                    "table": table_name,
                    "column": column_name,
                    "matches": rows
                })

            return {
                "tables": tables_found,
                "columns": columns_found,
                "rows": row_matches
            }
