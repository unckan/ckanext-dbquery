from flask import Blueprint
from ckan.plugins import toolkit


dbquery_bp = Blueprint('dbquery', __name__, url_prefix='/ckan-admin/db-query')


@dbquery_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Run a custom query on the database
    """
    # Verificar que el usuario sea un administrador del sistema
    if not toolkit.c.userobj or not toolkit.c.userobj.sysadmin:
        return toolkit.abort(403)

    query = None
    results = None
    request = toolkit.request

    if request.method == 'POST':
        form = request.form
        query = form.get('query')
        if query:
            data_dict = {'query': query}
            results = toolkit.get_action('custom_query')(None, data_dict)

    # Display results if any
    extra_vars = {
        'results': results,
        'query': query,
    }

    return toolkit.render('dbquery/index.html', extra_vars=extra_vars)
