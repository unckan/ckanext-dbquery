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
    result = None
    request = toolkit.request

    # Process form submission
    if request.method == 'POST':
        form = request.form
        query = form.get('query')
        if query:
            data_dict = {'query': query}
            result = toolkit.get_action('query_database')(None, data_dict)

    # Get recent queries for sidebar
    queries = toolkit.get_action('dbquery_executed_list')({}, {})

    # Display results if any
    extra_vars = {
        'result': result,
        'query': query,
        'queries': queries
    }

    return toolkit.render('dbquery/index.html', extra_vars=extra_vars)


@dbquery_bp.route('/history', methods=['GET'])
def history():
    """
    Show executed queries
    """
    # Verificar que el usuario sea un administrador del sistema
    if not toolkit.c.userobj or not toolkit.c.userobj.sysadmin:
        return toolkit.abort(403)

    # Get filter parameters
    user_filter = toolkit.request.args.get('user', '')
    date_filter = toolkit.request.args.get('date', '')

    filters = {}
    if user_filter:
        filters['user'] = user_filter
    if date_filter:
        filters['date'] = date_filter

    queries = toolkit.get_action('dbquery_executed_list')({}, filters)

    return toolkit.render('dbquery/history.html', extra_vars={'queries': queries})
