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
    if (column_exists(table_name, column_name)):
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
    def _search_tables(query):
        """Buscar tablas que coincidan con el texto"""
        query_tables = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name ILIKE :query
        """
        tables_found = query_database(query_tables, {"query": f"%{query}%"})
        return [t["table_name"] for t in tables_found]

    @staticmethod
    def _search_columns(query):
        """Buscar columnas que coincidan con el texto y obtener metadatos adicionales"""
        query_columns = """
            SELECT c.table_name,
                   c.column_name,
                   c.data_type,
                   c.character_maximum_length,
                   c.is_nullable,
                   (SELECT count(*) FROM information_schema.key_column_usage k
                    WHERE k.table_name = c.table_name
                    AND k.column_name = c.column_name) > 0 as is_key
            FROM information_schema.columns c
            WHERE c.table_schema = 'public' AND c.column_name ILIKE :query
            ORDER BY c.table_name, c.column_name
        """
        columns_found = query_database(query_columns, {"query": f"%{query}%"})
        result = []
        for c in columns_found:
            # Crear un texto descriptivo basado en los metadatos obtenidos
            tipo = f"{c['data_type']}"
            if c['character_maximum_length']:
                tipo += f"({c['character_maximum_length']})"

            atributos = []
            if c.get('is_key'):
                atributos.append("clave")
            if c.get('is_nullable') == 'NO':
                atributos.append("obligatorio")

            atributos_text = f" [{', '.join(atributos)}]" if atributos else ""

            result.append({
                "table": c["table_name"],
                "column": c["column_name"],
                "data_type": tipo,
                "display": f"{c['table_name']}.{c['column_name']} ({tipo}{atributos_text})"
            })
        return result

    @staticmethod
    def _search_rows(query, limit_rows):
        """Buscar filas que coincidan en cualquier tabla/columna de tipo texto"""
        # Obtener todas las columnas de tipo texto
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
                if rows:
                    row_matches.append({
                        "table": tc["table_name"],
                        "column": tc["column_name"],
                        "display_path": f"{tc['table_name']}.{tc['column_name']}",  # Path for display
                        "matches": rows
                    })
            except Exception as e:
                log.warning(f"Error al consultar {table_name}.{column_name}: {e}")

        return row_matches

    @staticmethod
    def _search_specific_objects(object_type, query, limit_rows):
        """Buscar objetos específicos según su tipo"""
        # Mapa de tipos de objetos a sus tablas y columnas principales
        object_type_map = {
            "user": {
                "table": "user",
                "id_column": "id",
                "name_columns": ["name", "fullname", "email"],
                "display": "name"
            },
            "group": {
                "table": "group",
                "id_column": "id",
                "name_columns": ["name", "title", "description"],
                "display": "title"
            },
            "organization": {
                "table": "group",
                "id_column": "id",
                "name_columns": ["name", "title", "description"],
                "display": "title",
                "filter": {"is_organization": True}
            },
            "package": {
                "table": "package",
                "id_column": "id",
                "name_columns": ["id", "name", "title", "notes"],  # Agregado "id" para buscar por ID del paquete
                "display": "title"
            },
            "resource": {
                "table": "resource",
                "id_column": "id",
                "name_columns": ["id", "name", "description", "url"],  # Agregado "id" para consistencia
                "display": "name"
            }
        }

        # Si el tipo de objeto no está en nuestro mapa
        if object_type not in object_type_map:
            log.warning(f"Tipo de objeto no reconocido: {object_type}")
            return []

        # Obtener la configuración para este tipo de objeto
        obj_config = object_type_map[object_type]

        # Ejecutar la búsqueda con la configuración
        return DbqueryPlugin._execute_object_search(obj_config, object_type, query, limit_rows)

    @staticmethod
    def _execute_object_search(obj_config, object_type, query, limit_rows):
        """Ejecuta la búsqueda de objetos según la configuración proporcionada"""
        objects_results = []
        table = obj_config["table"]
        id_column = obj_config["id_column"]
        name_columns = obj_config["name_columns"]
        display_column = obj_config["display"]

        # Construir la condición WHERE para los nombres de columnas
        where_conditions = []
        for col in name_columns:
            where_conditions.append(f"{quote_identifier(col)} ILIKE :query")

        where_clause = " OR ".join(where_conditions)

        # Agregar filtros adicionales si existen
        additional_filters = ""
        filter_params = {"query": f"%{query}%"}

        if "filter" in obj_config:
            for key, value in obj_config["filter"].items():
                additional_filters += f" AND {quote_identifier(key)} = :filter_{key}"
                filter_params[f"filter_{key}"] = value

        # Construir la consulta SQL
        query_sql = f"""
            SELECT {quote_identifier(id_column)}, {', '.join(quote_identifier(col) for col in name_columns)}
            FROM {quote_identifier(table)}
            WHERE ({where_clause}) {additional_filters}
            AND state = 'active'
            LIMIT :limit
        """

        try:
            # Ejecutar la consulta
            filter_params["limit"] = limit_rows
            objects_found = query_database(query_sql, filter_params)

            # Formatear los resultados para mostrar
            for obj in objects_found:
                obj_display = {
                    "id": obj[id_column],
                    "type": object_type,
                    "display_name": obj[display_column]
                }
                # Agregar todas las columnas encontradas
                for col in name_columns:
                    if col in obj and obj[col]:
                        obj_display[col] = obj[col]

                objects_results.append(obj_display)

        except Exception as e:
            log.warning(f"Error al buscar objetos de tipo {object_type}: {e}")

        return objects_results

    @staticmethod
    def custom_query(context, data_dict):
        """
        Realiza una búsqueda en la base de datos:
        1) Tablas cuyo nombre coincida con el texto.
        2) Columnas cuyo nombre coincida con el texto.
        3) Filas de cualquier tabla y columna (de tipo texto) que coincida con el texto.
        4) Objetos específicos por tipo (opcional)
        """
        # Verificar autorización
        toolkit.check_access('dbquery_custom_query', context, data_dict)

        query = data_dict.get('query')
        if not query:
            raise toolkit.ValidationError({"query": "Debe proporcionar un texto de búsqueda."})

        limit_rows = data_dict.get('limit_rows', 50)
        object_type = data_dict.get('object_type')

        # Inicializar el diccionario de resultados
        results = {
            "tables": DbqueryPlugin._search_tables(query),
            "columns": DbqueryPlugin._search_columns(query),
            "rows": DbqueryPlugin._search_rows(query, limit_rows)
        }

        # Si se especificó un tipo de objeto, realizar búsqueda específica
        if object_type:
            results["objects"] = DbqueryPlugin._search_specific_objects(object_type, query, limit_rows)

        return results
