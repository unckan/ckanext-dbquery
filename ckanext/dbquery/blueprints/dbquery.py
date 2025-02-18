from flask import Blueprint, render_template, request, flash
from ckan.plugins import toolkit

dbquery_bp = Blueprint('dbquery', __name__, url_prefix='/admin/dbquery')

@dbquery_bp.route('/index', methods=['GET', 'POST'], endpoint='index')
def index():
    """
    Vista de administración para la extensión DBQuery.
    Aquí puedes, por ejemplo, permitir que el usuario ingrese el nombre
    de una tabla para realizar la consulta.
    """
    results = None
    if request.method == 'POST':
        table = request.form.get('table')
        if table:
            try:
                # Llama a la acción custom_query para obtener los datos
                context = {'model': toolkit.get_action('get_site_user')(None, {})['name']}
                # Nota: ajusta el contexto según sea necesario.
                results = toolkit.get_action('custom_query')(context, {'table': table})
            except Exception as e:
                flash("Error en la consulta: %s" % e, 'error')
        else:
            flash("Debe especificar el nombre de la tabla", 'error')
    return render_template('dbquery/index.html', results=results)
