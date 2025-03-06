"""Integration tests for ckanext-dbquery."""

import pytest
from flask import url_for
from ckan.tests import helpers


@pytest.mark.ckan_config("ckan.plugins", "dbquery")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestDbqueryIntegration:
    """Integration tests for the DBQuery extension."""

    def test_dbquery_index_accessible_to_sysadmin(self, app):
        """Test that the dbquery index page is accessible to sysadmins."""
        user = helpers.call_action("user_create", name="test_sysadmin", email="test@example.com", password="password")
        helpers.call_action("user_update", id=user["id"], sysadmin=True)

        env = {"REMOTE_USER": user["name"]}

        # Use Flask route helpers instead of URL for string
        with app.flask_app.test_request_context():
            url = url_for("dbquery.index")

        response = app.get(url, extra_environ=env)
        assert "CKAN DB Query" in response.body.decode('utf-8')

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
