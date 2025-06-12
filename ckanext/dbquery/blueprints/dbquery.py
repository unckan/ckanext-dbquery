from flask import Blueprint
from ckan.plugins import toolkit
from ckan.plugins.toolkit import ValidationError


dbquery_bp = Blueprint('dbquery', __name__, url_prefix='/ckan-admin/db-query')


@dbquery_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Run a custom query on the database
    """
    # Check that the user is a system administrator
    if not toolkit.c.userobj or not toolkit.c.userobj.sysadmin:
        return toolkit.abort(403)

    query = None
    result = None
    error_message = None
    request = toolkit.request

    # Process form submission
    if request.method == 'POST':
        form = request.form
        query = form.get('query')
        if query:
            data_dict = {'query': query}
            try:
                result = toolkit.get_action('query_database')(None, data_dict)
            except ValidationError as e:
                # Extract the error message to display to the user
                error_message = e.error_dict.get('query') if hasattr(e, 'error_dict') else str(e)

    # Display results if any
    extra_vars = {
        'result': result,
        'query': query,
        'error_message': error_message,
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
    # We need a list of user id + names that ran queiries in the past
    user_filter = toolkit.get_action('dbquery_executor_users_list')({}, {})
    f_user = toolkit.request.args.get('user', '')
    f_date_filter = toolkit.request.args.get('date', '')

    filters = {}
    if f_user:
        filters['user'] = f_user
    if f_date_filter:
        filters['date'] = f_date_filter

    queries = toolkit.get_action('dbquery_executed_list')({}, filters)

    vars = {
        'queries': queries,
        'user_filter': f_user,
        'date_filter': f_date_filter,
        'users': user_filter,
    }
    return toolkit.render('dbquery/history.html', extra_vars=vars)
