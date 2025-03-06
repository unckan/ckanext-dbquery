"""Tests for the DbqueryPlugin class."""

import pytest
from unittest import mock
from ckanext.dbquery.plugin import DbqueryPlugin


class TestDbqueryPlugin:
    """Test the DbqueryPlugin class methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = DbqueryPlugin()
    
    def test_update_config(self):
        """Test the update_config method."""
        config_ = {}
        with mock.patch("ckan.plugins.toolkit.add_template_directory") as mock_add_template:
            with mock.patch("ckan.plugins.toolkit.add_public_directory") as mock_add_public:
                with mock.patch("ckan.plugins.toolkit.add_resource") as mock_add_resource:
                    self.plugin.update_config(config_)
                    mock_add_template.assert_called_once_with(config_, "templates")
                    mock_add_public.assert_called_once_with(config_, "public")
                    mock_add_resource.assert_called_once_with("assets", "dbquery")
    
    def test_get_blueprint(self):
        """Test the get_blueprint method."""
        from ckanext.dbquery.blueprints.dbquery import dbquery_bp
        assert self.plugin.get_blueprint() == dbquery_bp
    
    def test_get_actions(self):
        """Test the get_actions method."""
        actions = self.plugin.get_actions()
        assert "dbquery_execute" in actions
        assert "custom_query" in actions
        assert callable(actions["dbquery_execute"])
        assert callable(actions["custom_query"])
    
    def test_get_auth_functions(self):
        """Test the get_auth_functions method."""
        auth_functions = self.plugin.get_auth_functions()
        assert "dbquery_execute" in auth_functions
        assert "dbquery_custom_query" in auth_functions
        assert callable(auth_functions["dbquery_execute"])
        assert callable(auth_functions["dbquery_custom_query"])


class TestSearchMethods:
    """Test the search methods of the DbqueryPlugin."""
    
    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_search_tables(self, mock_query):
        """Test the _search_tables method."""
        mock_query.return_value = [{"table_name": "user"}, {"table_name": "resource"}]
        result = DbqueryPlugin._search_tables("user")
        assert result == ["user", "resource"]
    
    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_search_columns(self, mock_query):
        """Test the _search_columns method."""
        mock_query.return_value = [
            {
                "table_name": "resource_view", 
                "column_name": "resource_id",
                "data_type": "text",
                "character_maximum_length": None,
                "is_nullable": "YES",
                "is_key": True
            }
        ]
        result = DbqueryPlugin._search_columns("resource_id")
        assert len(result) == 1
        assert result[0]["table"] == "resource_view"
        assert result[0]["column"] == "resource_id"
        assert "display" in result[0]
    
    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_search_rows(self, mock_query):
        """Test the _search_rows method."""
        # First call returns column definitions
        # Second call returns row data
        mock_query.side_effect = [
            [{"table_name": "resource", "column_name": "name"}],
            [{"name": "Test Resource"}]
        ]
        result = DbqueryPlugin._search_rows("Test", 10)
        assert len(result) == 1
        assert result[0]["table"] == "resource"
        assert result[0]["column"] == "name"
        assert result[0]["matches"] == [{"name": "Test Resource"}]
    
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._execute_object_search")
    def test_search_specific_objects(self, mock_execute):
        """Test the _search_specific_objects method."""
        mock_execute.return_value = [
            {"id": "123", "type": "resource", "display_name": "Test Resource", "name": "test-resource"}
        ]
        result = DbqueryPlugin._search_specific_objects("resource", "test", 10)
        assert len(result) == 1
        assert result[0]["id"] == "123"
        assert result[0]["type"] == "resource"
    
    def test_search_specific_objects_invalid_type(self):
        """Test _search_specific_objects with invalid object type."""
        result = DbqueryPlugin._search_specific_objects("invalid_type", "test", 10)
        assert result == []


class TestCustomQuery:
    """Test the custom_query method."""
    
    @mock.patch("ckan.plugins.toolkit.check_access")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_tables")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_columns")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_rows")
    def test_custom_query(self, mock_rows, mock_columns, mock_tables, mock_check_access):
        """Test the custom_query method."""
        context = {"user": "test-user"}
        data_dict = {"query": "test"}
        
        mock_tables.return_value = ["user", "resource"]
        mock_columns.return_value = [{"table": "user", "column": "name"}]
        mock_rows.return_value = [{
            "table": "user", 
            "column": "name", 
            "matches": [{"name": "test"}]
        }]
        
        result = DbqueryPlugin.custom_query(context, data_dict)
        
        mock_check_access.assert_called_once_with('dbquery_custom_query', context, data_dict)
        assert "tables" in result
        assert "columns" in result
        assert "rows" in result
        assert "objects" not in result
    
    @mock.patch("ckan.plugins.toolkit.check_access")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_tables")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_columns")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_rows")
    @mock.patch("ckanext.dbquery.plugin.DbqueryPlugin._search_specific_objects")
    def test_custom_query_with_object_type(self, mock_objects, mock_rows, mock_columns, mock_tables, mock_check_access):
        """Test the custom_query method with object_type specified."""
        context = {"user": "test-user"}
        data_dict = {"query": "test", "object_type": "resource"}
        
        mock_tables.return_value = ["user", "resource"]
        mock_columns.return_value = [{"table": "user", "column": "name"}]
        mock_rows.return_value = [{
            "table": "user", 
            "column": "name", 
            "matches": [{"name": "test"}]
        }]
        mock_objects.return_value = [
            {"id": "123", "type": "resource", "display_name": "Test Resource"}
        ]
        
        result = DbqueryPlugin.custom_query(context, data_dict)
        
        mock_check_access.assert_called_once_with('dbquery_custom_query', context, data_dict)
        assert "objects" in result
        mock_objects.assert_called_once_with("resource", "test", 50)
