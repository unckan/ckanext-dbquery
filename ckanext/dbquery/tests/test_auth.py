"""Tests for the authorization functions."""

import pytest
from unittest import mock
from ckanext.dbquery.auth.dbquery import dbquery_execute


class TestDbqueryExecuteAuth:
    """Tests for the dbquery_execute authorization function."""
    
    def test_dbquery_execute_sysadmin(self):
        """Test authorization for sysadmin users."""
        user_obj = mock.MagicMock(sysadmin=True)
        context = {"auth_user_obj": user_obj}
        data_dict = {}
        
        result = dbquery_execute(context, data_dict)
        
        assert result["success"] is True
    
    def test_dbquery_execute_regular_user(self):
        """Test authorization for non-sysadmin users."""
        user_obj = mock.MagicMock(sysadmin=False)
        context = {"auth_user_obj": user_obj}
        data_dict = {}
        
        result = dbquery_execute(context, data_dict)
        
        assert result["success"] is False
        assert "Necesita ser administrador" in result["msg"]
    
    def test_dbquery_execute_no_user(self):
        """Test authorization with no user object."""
        context = {}
        data_dict = {}
        
        result = dbquery_execute(context, data_dict)
        
        assert result["success"] is False
