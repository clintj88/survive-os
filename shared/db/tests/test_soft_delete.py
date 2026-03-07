"""Tests for soft delete helpers."""

from shared.db.soft_delete import filter_deleted, soft_delete_sql


def test_soft_delete_sql():
    sql = soft_delete_sql("items")
    assert "UPDATE items SET deleted_at" in sql
    assert "WHERE id = ?" in sql


def test_soft_delete_sql_custom_id():
    sql = soft_delete_sql("items", id_column="item_id")
    assert "WHERE item_id = ?" in sql


def test_filter_deleted_no_where():
    result = filter_deleted("SELECT * FROM items")
    assert result == "SELECT * FROM items WHERE deleted_at IS NULL"


def test_filter_deleted_with_where():
    result = filter_deleted("SELECT * FROM items WHERE name = 'x'")
    assert result == "SELECT * FROM items WHERE name = 'x' AND deleted_at IS NULL"


def test_filter_deleted_include_deleted():
    base = "SELECT * FROM items"
    result = filter_deleted(base, include_deleted=True)
    assert result == base
