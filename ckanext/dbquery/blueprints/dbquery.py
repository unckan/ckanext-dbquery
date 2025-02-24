from flask import Blueprint, render_template, request, flash
from ckan.plugins import toolkit
from ckan.lib import base

dbquery_bp = Blueprint('dbquery', __name__, url_prefix='/ckan-admin/dbquery')


@dbquery_bp.route('/index', methods=['GET', 'POST'])
def index():
    """
    Vista de administración para la extensión DBQuery.
    Aquí puedes, por ejemplo, permitir que el usuario ingrese el nombre
    de una tabla para realizar la consulta.
    """
    if not toolkit.c.userobj or not toolkit.c.userobj.sysadmin:
        base.abort(403, ("Need to be system administrator to administer"))
    results = None
    if request.method == 'POST':
        # Obtén el valor ingresado por el usuario
        q = request.form.get('query', '').strip()

        if q:
            try:
                # Construye el contexto y data_dict para la acción
                context = {'user': toolkit.c.user}
                data_dict = {'query': q}

                # Llama a la acción custom_query
                results = toolkit.get_action('custom_query')(context, data_dict)

                if not results:
                    flash("No se encontraron resultados para la consulta.", 'info')

            except toolkit.ValidationError as ve:
                flash(f"Error de validación: {ve.error_summary}", 'error')

            except toolkit.NotAuthorized:
                flash("No tiene permiso para ejecutar esta consulta.", 'error')

            except Exception as e:
                flash(f"Error al ejecutar la consulta: {e}", 'error')

        else:
            flash("Debe especificar una consulta válida.", 'error')

    # Renderiza la plantilla con los resultados (si existen)
    return render_template('dbquery/index.html', results=results)