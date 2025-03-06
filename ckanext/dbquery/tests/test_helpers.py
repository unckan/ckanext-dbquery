"""Tests for helper functions in the plugin.py file."""

from unittest import mock
from ckanext.dbquery.plugin import quote_identifier, column_exists, safe_query_logs


class TestQuoteIdentifier:
    """Tests for the quote_identifier function."""

    def test_reserved_word(self):
        """Test quoting of reserved words."""
        assert quote_identifier("user") == '"user"'
        assert quote_identifier("group") == '"group"'
        assert quote_identifier("order") == '"order"'

    def test_regular_word(self):
        """Test that regular words are not quoted."""
        assert quote_identifier("package") == "package"
        assert quote_identifier("resource") == "resource"


class TestColumnExists:
    """Tests for the column_exists function."""

    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_column_exists_true(self, mock_query):
        """Test when column exists."""
        mock_query.return_value = [{"column_name": "name"}]
        assert column_exists("user", "name") is True

    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_column_exists_false(self, mock_query):
        """Test when column doesn't exist."""
        mock_query.return_value = []
        assert column_exists("user", "non_existent_column") is False


class TestSafeQueryLogs:
    """Tests for the safe_query_logs function."""

    @mock.patch("ckanext.dbquery.plugin.column_exists")
    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_column_exists_successful_query(self, mock_query, mock_column_exists):
        """Test successful query when column exists."""
        mock_column_exists.return_value = True
        mock_query.return_value = [{"funcName": "test_func"}]
        result = safe_query_logs()
        assert result == [{"funcName": "test_func"}]

    @mock.patch("ckanext.dbquery.plugin.column_exists")
    def test_column_not_exists(self, mock_column_exists):
        """Test when column doesn't exist."""
        mock_column_exists.return_value = False
        result = safe_query_logs()
        assert result == []

    @mock.patch("ckanext.dbquery.plugin.column_exists")
    @mock.patch("ckanext.dbquery.plugin.query_database")
    def test_query_exception(self, mock_query, mock_column_exists):
        """Test handling of exceptions during query execution."""
        mock_column_exists.return_value = True
        mock_query.side_effect = Exception("Test exception")
        result = safe_query_logs()
        assert result == []
