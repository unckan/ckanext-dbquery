
from ckanext.dbquery.plugin import DbqueryPlugin


class TestDbqueryPlugin:

    def test_plugin_initialization(self):
        """Test that the plugin initializes correctly."""
        plugin = DbqueryPlugin()
        assert plugin is not None

    def test_update_config(self):
        """Test update_config method."""
        plugin = DbqueryPlugin()
        mock_config = {}
        plugin.update_config(mock_config)


    def test_get_blueprint(self):
        """Test that get_blueprint returns a blueprint."""
        plugin = DbqueryPlugin()
        blueprints = plugin.get_blueprint()

        assert blueprints is not None
        assert 'dbquery' in [b.name for b in blueprints]

    def test_get_actions(self):
        """Test that get_actions returns the expected actions."""
        plugin = DbqueryPlugin()
        actions = plugin.get_actions()

        assert 'query_database' in actions
        assert 'dbquery_executed_list' in actions
        assert callable(actions['query_database'])
        assert callable(actions['dbquery_executed_list'])

    def test_get_auth_functions(self):
        """Test that get_auth_functions returns the expected auth functions."""
        plugin = DbqueryPlugin()
        auth_functions = plugin.get_auth_functions()

        assert 'query_database' in auth_functions
        assert callable(auth_functions['query_database'])
