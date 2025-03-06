import logging
import sqlalchemy

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.model import Session
from ckanext.dbquery.blueprints.dbquery import dbquery_bp
from ckanext.dbquery.actions import dbquery as dbquery_actions
from ckanext.dbquery.auth import dbquery as dbquery_auth

log = logging.getLogger(__name__)

# Lista de palabras reservadas en PostgreSQL
RESERVED_WORDS = {"group", "user", "order", "select", "table"}


def quote_identifier(identifier):
    """ Agrega comillas dobles si el nombre de la tabla o columna es una palabra reservada. """
    if identifier.lower() in RESERVED_WORDS:
        return f'"{identifier}"'
    return identifier


def query_database(query, params=None):
    """ Realiza una consulta a la base de datos y retorna los resultados usando la sesión de CKAN"""
    try:
        # Usar la sesión SQLAlchemy de CKAN en lugar de crear una nueva conexión
        engine = Session.get_bind()
        conn = engine.connect()

        # Ejecutar la consulta de forma segura
        log.info("Ejecutando consulta: %s", query)
        result = conn.execute(sqlalchemy.text(query), params or {})

        # Obtener nombres de columnas y resultados
        rows = result.fetchall()
        colnames = result.keys()

        # Construir lista de diccionarios con los resultados
        results = [dict(zip(colnames, row)) for row in rows]

        conn.close()
        return results

    except Exception as e:
        log.error("Error al realizar la consulta a la base de datos: %s", e)
        raise


def column_exists(table_name, column_name):
    """ Verifica si una columna existe en una tabla de la base de datos """
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = :table_name
        AND LOWER(column_name) = LOWER(:column_name)
    """
    result = query_database(query, {"table_name": table_name, "column_name": column_name})
    return bool(result)


def safe_query_logs():
    """ Intenta ejecutar una consulta en la tabla logs de manera segura """
    table_name = "logs"
    column_name = "funcName"

    # Verifica si la columna existe antes de hacer la consulta
    if column_exists(table_name, column_name):
        column_name_quoted = quote_identifier(column_name)  # Usa comillas dobles si es sensible a mayúsculas
        query = f'SELECT {column_name_quoted} FROM {table_name} LIMIT 10'

        try:
            results = query_database(query)
            return results
        except Exception as e:
            log.warning(f"Error al consultar {table_name}.{column_name}: {e}")
            return []
    else:
        log.warning(f"La columna {column_name} no existe en {table_name}. Omitiendo consulta.")
        return []


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
        - "limit_rows": límite de filas a mostrar por tabla-columna (opcional, default=50)

        Retorna un diccionario con:
        {
            "tables": [...],
            "columns": [...],
            "rows": [...]
        }
        """
        # Verificar autorización
        toolkit.check_access('dbquery_custom_query', context, data_dict)

        query = data_dict.get('query')
        if not query:
            raise toolkit.ValidationError({"query": "Debe proporcionar un texto de búsqueda."})

        limit_rows = data_dict.get('limit_rows', 50)

        # 1) Buscar tablas que coincidan con el texto
        query_tables = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name ILIKE :query
        """
        tables_found = query_database(query_tables, {"query": f"%{query}%"})

        # 2) Buscar columnas que coincidan con el texto
        query_columns = """
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND column_name ILIKE :query
        """
        columns_found = query_database(query_columns, {"query": f"%{query}%"})

        # 3) Buscar filas que coincidan en cualquier tabla/columna de tipo texto
        query_text_columns = """
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND data_type IN ('character varying', 'text')
        """
        text_columns = query_database(query_text_columns)

        row_matches = []
        for tc in text_columns:
            table_name = quote_identifier(tc["table_name"])
            column_name = quote_identifier(tc["column_name"])

            query_sql = f"""
                SELECT {column_name} FROM {table_name}
                WHERE {column_name} ILIKE :query
                LIMIT :limit_rows
            """

            try:
                rows = query_database(query_sql, {"query": f"%{query}%", "limit_rows": limit_rows})
            except Exception as e:
                log.warning(f"Error al consultar {table_name}.{column_name}: {e}")
                rows = []

            if rows:
                row_matches.append({
                    "table": tc["table_name"],
                    "column": tc["column_name"],
                    "matches": rows
                })

        return {
            "tables": [t["table_name"] for t in tables_found],
            "columns": [{"table": c["table_name"], "column": c["column_name"]} for c in columns_found],
            "rows": row_matches
        }
