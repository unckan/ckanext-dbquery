"""Integration tests for ckanext-dbquery."""

import pytest
from unittest import mock
from flask import Flask
from ckan.tests import helpers


@pytest.mark.ckan_config("ckan.plugins", "dbquery")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestDbqueryIntegration:
    """Integration tests for the DBQuery extension."""
    def test_dbquery_index_accessible_to_sysadmin(self):
        """Test that the dbquery index page is accessible to sysadmins."""
        from ckanext.dbquery.blueprints.dbquery import index

        # Create a Flask app for testing
        app = Flask(__name__)

        # Create a test context
        with app.app_context(), app.test_request_context():
            with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.c") as mock_c:
                with mock.patch("ckanext.dbquery.blueprints.dbquery.toolkit.render") as mock_render:
                    # Create a mock sysadmin user
                    sysadmin = mock.MagicMock(sysadmin=True)
                    mock_c.userobj = sysadmin

                    # Call the index view function directly
                    index()

                    # Check that render was called with the right template
                    mock_render.assert_called_once()
                    assert mock_render.call_args[0][0] == 'dbquery/index.html'

    def test_custom_query_action_accessible_to_sysadmin(self):
        """Test that the custom_query action is accessible to sysadmins."""
        # Create a sysadmin user with all required fields
        sysadmin = helpers.call_action(
            "user_create",
            name="sysadmin2",
            email="sysadmin2@example.com",
            password="password123"
        )

        # Make user a sysadmin
        helpers.call_action(
            "user_update",
            id=sysadmin["id"],
            name=sysadmin["name"],
            email=sysadmin["email"],
            sysadmin=True
        )

        # Run the action with proper context
        result = helpers.call_action(
            "custom_query",
            {"user": sysadmin["name"]},
            query="resource"
        )

        # Just verify basic structure of result
        assert "tables" in result
        assert "columns" in result
