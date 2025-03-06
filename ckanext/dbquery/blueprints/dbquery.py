from flask import Blueprint, request, flash
import ckan.plugins.toolkit as toolkit

dbquery_bp = Blueprint('dbquery', __name__, url_prefix='/ckan-admin/dbquery')


def _display_search_results(results, query):
    """Helper function to display flash messages with search results"""
    if not results or (not results.get('tables') and not results.get('columns') and
                       not results.get('rows') and not results.get('objects')):
        flash((f"No se encontraron resultados para: {query}"), 'info')
        return

    flash(("Consulta ejecutada con éxito"), 'success')

    # Mensajes más específicos sobre lo que se encontró
    if results.get('tables'):
        flash((f"Se encontraron {len(results['tables'])} tablas que coinciden con '{query}'"), 'info')

    if results.get('columns'):
        column_info = []
        for col in results['columns']:
            column_info.append(
                f"{col['column']} (en tabla {col['table']}, "
                f"tipo {col.get('data_type', 'desconocido')})"
            )
        flash((f"Se encontraron {len(results['columns'])} columnas relacionadas con '{query}': "
               f"{', '.join(column_info)}"), 'info')

    if results.get('rows'):
        tables_with_rows = [f"{row['table']}.{row['column']}" for row in results['rows']]
        flash((f"Se encontraron coincidencias en {len(results['rows'])} tablas/columnas: "
               f"{', '.join(tables_with_rows)}"), 'info')

    if results.get('objects'):
        object_types = set(obj['type'] for obj in results['objects'])
        flash((f"Se encontraron {len(results['objects'])} objetos de tipo: {', '.join(object_types)}"), 'info')


def _execute_search(query, object_type):
    """Helper function to execute the search query"""
    try:
        # Construye el contexto y data_dict para la acción
        context = {'user': toolkit.c.user, 'auth_user_obj': toolkit.c.userobj}
        data_dict = {'query': query}

        # Si se ha seleccionado un tipo de objeto, lo agregamos al data_dict
        if object_type:
            data_dict['object_type'] = object_type

        # Llama a la acción custom_query
        return toolkit.get_action('custom_query')(context, data_dict)
    except toolkit.ValidationError as ve:
        flash((f"Error de validación: {str(ve)}"), 'error')
    except toolkit.NotAuthorized:
        flash(("No tiene permiso para ejecutar esta consulta."), 'error')
    except Exception as e:
        flash((f"Error al ejecutar la consulta: {str(e)}"), 'error')

    return None


@dbquery_bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Vista de administración para la extensión DBQuery.
    Permite al usuario ingresar un texto para buscar en la base de datos.
    """
    # Verificar que el usuario sea un administrador del sistema
    if not toolkit.c.userobj or not toolkit.c.userobj.sysadmin:
        return toolkit.abort(403, ("Necesita ser administrador del sistema para administrar DBQuery"))

    results = None

    # Lista de tipos de objetos disponibles para la búsqueda
    available_object_types = [
        {'value': '', 'text': '-- Cualquier objeto --'},
        {'value': 'user', 'text': 'Usuario'},
        {'value': 'group', 'text': 'Grupo'},
        {'value': 'organization', 'text': 'Organización'},
        {'value': 'package', 'text': 'Conjunto de datos'},
        {'value': 'resource', 'text': 'Recurso'}
    ]

    if request.method == 'POST':
        # Obtén el valor ingresado por el usuario
        q = request.form.get('query', '').strip()
        object_type = request.form.get('object_type', '').strip()

        if q:
            results = _execute_search(q, object_type)
            if results:
                _display_search_results(results, q)
        else:
            flash(("Debe especificar una consulta válida."), 'error')

    # Renderiza la plantilla con los resultados (si existen)
    extra_vars = {
        'results': results,
        'object_types': available_object_types
    }
    return toolkit.render('dbquery/index.html', extra_vars=extra_vars)
