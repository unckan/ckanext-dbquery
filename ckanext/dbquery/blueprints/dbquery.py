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
        table = request.form.get('table')
        if table:
            try:
                # Ejecuta la acción 'dbquery_execute'
                context = {'user': toolkit.c.user}
                data_dict = {'table': table}

                # Llama a la acción custom_query para obtener los datos
                results = toolkit.get_action('custom_query')(context, data_dict)
            except Exception as e:
                flash("Error en la consulta: %s" % e, 'error')
        else:
            flash("Debe especificar el nombre de la tabla", 'error')
    return render_template('dbquery/index.html', results=results)
