from flask import Blueprint, request, flash
import ckan.plugins.toolkit as toolkit
from ckan.common import _

dbquery_bp = Blueprint('dbquery', __name__, url_prefix='/ckan-admin/dbquery')


@dbquery_bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Vista de administración para la extensión DBQuery.
    Permite al usuario ingresar un texto para buscar en la base de datos.
    """
    # Verificar que el usuario sea un administrador del sistema
    if not toolkit.c.userobj or not toolkit.c.userobj.sysadmin:
        return toolkit.abort(403, _("Necesita ser administrador del sistema para administrar DBQuery"))

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
            try:
                # Construye el contexto y data_dict para la acción
                context = {'user': toolkit.c.user, 'auth_user_obj': toolkit.c.userobj}
                data_dict = {'query': q}

                # Si se ha seleccionado un tipo de objeto, lo agregamos al data_dict
                if object_type:
                    data_dict['object_type'] = object_type

                # Llama a la acción custom_query
                results = toolkit.get_action('custom_query')(context, data_dict)

                if not results or (not results.get('tables') and not results.get('columns') and
                                   not results.get('rows') and not results.get('objects')):
                    flash(_(f"No se encontraron resultados para: {q}"), 'info')
                else:
                    flash(_("Consulta ejecutada con éxito"), 'success')

            except toolkit.ValidationError as ve:
                flash(_(f"Error de validación: {str(ve)}"), 'error')

            except toolkit.NotAuthorized:
                flash(_("No tiene permiso para ejecutar esta consulta."), 'error')

            except Exception as e:
                flash(_(f"Error al ejecutar la consulta: {str(e)}"), 'error')
        else:
            flash(_("Debe especificar una consulta válida."), 'error')

    # Renderiza la plantilla con los resultados (si existen)
    extra_vars = {
        'results': results,
        'object_types': available_object_types
    }
    return toolkit.render('dbquery/index.html', extra_vars=extra_vars)
