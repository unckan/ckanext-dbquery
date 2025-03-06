"""Tests for the action functions."""

import pytest
from unittest import mock
from ckan.logic import NotAuthorized
from ckanext.dbquery.actions.dbquery import dbquery_execute


class TestDbqueryExecute:
    """Tests for the dbquery_execute action."""
    
    def test_dbquery_execute_unauthorized(self):
        """Test unauthorized access."""
        context = {"ignore_auth": False}
        data_dict = {"table": "user"}
        
        with pytest.raises(NotAuthorized):
            dbquery_execute(context, data_dict)
    
    def test_dbquery_execute_no_table(self):
        """Test validation error when no table is provided."""
        context = {"ignore_auth": True}
        data_dict = {}
        
        with pytest.raises(Exception) as e:
            dbquery_execute(context, data_dict)
        assert "Debe especificar una tabla" in str(e)
    
    @mock.patch("ckanext.dbquery.actions.dbquery.session")
    def test_dbquery_execute_success(self, mock_session):
        """Test successful execution."""
        context = {"ignore_auth": True, "session": mock_session}
        data_dict = {"table": "user"}
        
        mock_result = mock.MagicMock()
        mock_result.__iter__.return_value = [{"id": "1", "name": "test"}]
        mock_session.execute.return_value = mock_result
        
        result = dbquery_execute(context, data_dict)
        
        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["name"] == "test"
