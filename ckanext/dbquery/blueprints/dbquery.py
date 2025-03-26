from flask import Blueprint
from ckan.plugins import toolkit
from ckan import model
from ckanext.dbquery.model import DBQueryExecuted


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

    # Check if we're loading a query from history
    load_query_id = request.args.get('load_query')
    if load_query_id:
        # Find the query by ID
        saved_query = model.Session.query(DBQueryExecuted).filter(
            DBQueryExecuted.id == load_query_id
        ).first()

        if saved_query:
            # Pre-populate the query field
            query = saved_query.query

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

    queries = toolkit.get_action('dbquery_executed_list')({}, {})

    return toolkit.render('dbquery/history.html', extra_vars={'queries': queries})
