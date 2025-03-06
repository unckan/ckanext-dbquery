"""Tests for the blueprint routes."""

import pytest
from unittest import mock
from flask import url_for
from ckan.tests import helpers
from ckanext.dbquery.blueprints.dbquery import _display_search_results, _execute_search


class TestDisplaySearchResults:
    """Tests for the _display_search_results function."""
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.flash")
    def test_display_empty_results(self, mock_flash):
        """Test displaying empty results."""
        _display_search_results({}, "test")
        mock_flash.assert_called_once()
        assert "No se encontraron resultados" in mock_flash.call_args_list[0][0][0]
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.flash")
    def test_display_with_tables(self, mock_flash):
        """Test displaying results with tables."""
        results = {"tables": ["table1", "table2"]}
        _display_search_results(results, "test")
        assert mock_flash.call_count >= 2
        assert any("Consulta ejecutada con éxito" in call[0][0] for call in mock_flash.call_args_list)
        assert any("Se encontraron 2 tablas" in call[0][0] for call in mock_flash.call_args_list)
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.flash")
    def test_display_with_columns(self, mock_flash):
        """Test displaying results with columns."""
        results = {
            "columns": [
                {"table": "table1", "column": "col1", "data_type": "text"},
                {"table": "table2", "column": "col2", "data_type": "int"}
            ]
        }
        _display_search_results(results, "test")
        assert mock_flash.call_count >= 2
        assert any("Se encontraron 2 columnas" in call[0][0] for call in mock_flash.call_args_list)


class TestExecuteSearch:
    """Tests for the _execute_search function."""
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.get_action")
    @mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c", spec=True)
    def test_execute_search(self, mock_c, mock_get_action):
        """Test executing a search query."""
        mock_action = mock.MagicMock()
        mock_get_action.return_value = mock_action
        mock_action.return_value = {"tables": ["table1"]}
        
        mock_c.user = "test-user"
        mock_c.userobj = "test-userobj"
        
        result = _execute_search("test", "")
        
        mock_get_action.assert_called_once_with("custom_query")
        mock_action.assert_called_once()
        assert result == {"tables": ["table1"]}
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.get_action")
    @mock.patch("ckanext.dbquery.blueprints.dbquery.flash")
    @mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c", spec=True)
    def test_execute_search_with_validation_error(self, mock_c, mock_flash, mock_get_action):
        """Test handling validation errors."""
        from ckan.plugins.toolkit import ValidationError
        
        mock_action = mock.MagicMock()
        mock_get_action.return_value = mock_action
        mock_action.side_effect = ValidationError({"error": "Test error"})
        
        mock_c.user = "test-user"
        mock_c.userobj = "test-userobj"
        
        result = _execute_search("test", "")
        
        assert result is None
        mock_flash.assert_called_once()
        assert "Error de validación" in mock_flash.call_args[0][0]


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestDbqueryBlueprintRoutes:
    """Test the blueprint routes."""
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.render")
    def test_index_route_unauthorized(self, mock_render, app):
        """Test accessing the index route as an unauthorized user."""
        with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
            mock_c.userobj = None
            
            response = app.get(
                url_for("dbquery.index"),
                status=403
            )
            
            assert response.status_code == 403
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.render")
    def test_index_route_sysadmin(self, mock_render, app):
        """Test accessing the index route as a sysadmin."""
        with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
            mock_c.userobj = mock.MagicMock(sysadmin=True)
            
            response = app.get(
                url_for("dbquery.index"),
                status=200
            )
            
            mock_render.assert_called_once_with(
                "dbquery/index.html",
                mock.ANY
            )
    
    @mock.patch("ckanext.dbquery.blueprints.dbquery._execute_search")
    @mock.patch("ckanext.dbquery.blueprints.dbquery._display_search_results")
    def test_index_post_with_query(self, mock_display, mock_execute, app):
        """Test posting a query to the index route."""
        mock_execute.return_value = {"tables": ["test_table"]}
        
        with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
            mock_c.userobj = mock.MagicMock(sysadmin=True)
            
            response = app.post(
                url_for("dbquery.index"),
                data={"query": "test", "object_type": ""},
                status=200
            )
            
            mock_execute.assert_called_once_with("test", "")
            mock_display.assert_called_once_with({"tables": ["test_table"]}, "test")
