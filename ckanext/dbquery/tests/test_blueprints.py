"""Tests for the blueprint routes."""

from unittest import mock
from flask import Flask
from ckan.plugins.toolkit import ValidationError
from ckanext.dbquery.blueprints.dbquery import _display_search_results, _execute_search, index


class TestDbqueryBlueprint:
    """Tests for the dbquery blueprint functions."""

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

    def test_execute_search(self):
        """Test executing a search query."""
        app = Flask(__name__)

        # Create a test Flask application context
        with app.app_context(), app.test_request_context():
            with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.get_action") as mock_get_action:
                mock_action = mock.MagicMock()
                mock_get_action.return_value = mock_action
                mock_action.return_value = {"tables": ["table1"]}

                with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
                    mock_c.user = "test-user"
                    mock_c.userobj = "test-userobj"

                    result = _execute_search("test", "")

                    mock_get_action.assert_called_once_with("custom_query")
                    mock_action.assert_called_once()
                    assert result == {"tables": ["table1"]}

    def test_execute_search_with_validation_error(self):
        """Test handling validation errors."""
        app = Flask(__name__)

        # Create a test Flask application context
        with app.app_context(), app.test_request_context():
            with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.get_action") as mock_get_action:
                with mock.patch("ckanext.dbquery.blueprints.dbquery.flash") as mock_flash:
                    with mock.patch("ckanext.dbquery.blueprints.dbquery._") as mock_translate:
                        # Set up mocks
                        mock_action = mock.MagicMock()
                        mock_get_action.return_value = mock_action
                        mock_action.side_effect = ValidationError({"error": "Test error"})

                        # Mock translate function to return original string
                        mock_translate.side_effect = lambda x: x

                        with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
                            mock_c.user = "test-user"
                            mock_c.userobj = "test-userobj"

                            result = _execute_search("test", "")
                            assert result is None
                            mock_flash.assert_called_once()
                            # Check that flash is called with a string containing these words
                            flash_message = mock_flash.call_args[0][0]
                            assert "Error" in flash_message

    def test_index_route_unauthorized(self):
        """Test accessing the index route as an unauthorized user."""
        app = Flask(__name__)
        with app.app_context(), app.test_request_context():
            with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.abort") as mock_abort:
                with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
                    # Configuramos un usuario NO sysadmin
                    mock_c.userobj = mock.MagicMock(sysadmin=False)
                    index()
                    # Verificamos que se haya llamado a abort con status 403
                    mock_abort.assert_called_once_with(403, mock.ANY)

    def test_index_route_sysadmin(self):
        """Test accessing the index route as a sysadmin."""
        app = Flask(__name__)
        with app.app_context(), app.test_request_context():
            with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.render") as mock_render:
                with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
                    # Configuramos un usuario sysadmin
                    mock_c.userobj = mock.MagicMock(sysadmin=True)
                    index()
                    # Verificamos que se llame a render con la plantilla correcta y extra_vars
                    mock_render.assert_called_once()
                    args, kwargs = mock_render.call_args
                    assert args[0] == "dbquery/index.html"
                    assert "extra_vars" in kwargs

    def test_index_post_with_query(self):
        """Test posting a query to the index route."""
        app = Flask(__name__)
        with app.app_context(), app.test_request_context(method='POST', data={
                'query': 'test',
                'object_type': ''}):
            with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
                with mock.patch("ckanext.dbquery.blueprints.dbquery._execute_search") as mock_execute:
                    with mock.patch("ckanext.dbquery.blueprints.dbquery._display_search_results") as mock_display:
                        # Configuramos un usuario sysadmin
                        mock_c.userobj = mock.MagicMock(sysadmin=True)
                        # Simulamos el retorno de la acción custom_query
                        mock_execute.return_value = {"tables": ["test_table"]}
                        index()
                        mock_execute.assert_called_once_with("test", "")
                        mock_display.assert_called_once_with({"tables": ["test_table"]}, "test")
