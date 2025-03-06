"""Integration tests for ckanext-dbquery."""

import pytest
from ckan.tests import factories, helpers


@pytest.mark.ckan_config("ckan.plugins", "dbquery")
@pytest.mark.usefixtures("clean_db", "with_plugins", "with_request_context")
class TestDbqueryIntegration:
    """Integration tests for the DBQuery extension."""
    
    def test_dbquery_index_accessible_to_sysadmin(self, app):
        """Test that the dbquery index page is accessible to sysadmins."""
        user = factories.Sysadmin()
        env = {"REMOTE_USER": user["name"]}
        
        response = app.get(
            url_for=("/ckan-admin/dbquery/index"),
            extra_environ=env,
            status=200
        )
        
        assert "CKAN DB Query" in response.body
        assert "Buscar texto" in response.body
    
    def test_dbquery_index_not_accessible_to_regular_users(self, app):
        """Test that the dbquery index page is not accessible to regular users."""
        user = factories.User()
        env = {"REMOTE_USER": user["name"]}
        
        app.get(
            url_for=("/ckan-admin/dbquery/index"),
            extra_environ=env,
            status=403
        )
    
    def test_custom_query_action_accessible_to_sysadmin(self, app):
        """Test that the custom_query action is accessible to sysadmins."""
        user = factories.Sysadmin()
        
        result = helpers.call_action(
            "custom_query",
            {"user": user["name"]},
            query="resource"
        )
        
        assert "tables" in result
        assert "columns" in result
        assert "rows" in result
    
    def test_custom_query_action_not_accessible_to_regular_users(self, app):
        """Test that the custom_query action is not accessible to regular users."""
        user = factories.User()
        
        with pytest.raises(helpers.NotAuthorized):
            helpers.call_action(
                "custom_query",
                {"user": user["name"]},
                query="resource"
            )
