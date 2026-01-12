import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel import parse_dbml


def test_parse_simple_table():
    """Test parsing a simple DBML table"""
    dbml = """
    Table users {
        id serial [pk]
        name text [not null]
        email text [unique]
    }
    """
    tables = parse_dbml(dbml)

    assert len(tables) == 1
    assert tables[0].name == "users"
    assert len(tables[0].columns) == 3

    # Check primary key
    pk_col = next(c for c in tables[0].columns if c.name == "id")
    assert pk_col.primary_key is True

    # Check not null
    name_col = next(c for c in tables[0].columns if c.name == "name")
    assert name_col.nullable is False

    # Check unique
    email_col = next(c for c in tables[0].columns if c.name == "email")
    assert email_col.unique is True


def test_parse_table_with_reference():
    """Test parsing tables with foreign key relationships"""
    dbml = """
    Table users {
        id serial [pk]
        name text
    }

    Table posts {
        id serial [pk]
        user_id integer [not null]
        title text
    }

    Ref: posts.user_id > users.id
    """
    tables = parse_dbml(dbml)

    assert len(tables) == 2

    posts_table = next(t for t in tables if t.name == "posts")
    user_id_col = next(c for c in posts_table.columns if c.name == "user_id")

    assert user_id_col.references is not None
    assert len(user_id_col.references) > 0
    assert user_id_col.references[0][0] == "users"
    assert user_id_col.references[0][1] == "id"


def test_parse_column_notes():
    """Test parsing column notes/descriptions"""
    dbml = """
    Table users {
        id serial [pk]
        name text [note: 'User full name']
        email text [note: 'User email address']
    }
    """
    tables = parse_dbml(dbml)

    name_col = next(c for c in tables[0].columns if c.name == "name")
    assert name_col.note == "User full name"

    email_col = next(c for c in tables[0].columns if c.name == "email")
    assert email_col.note == "User email address"


def test_parse_multiple_tables():
    """Test parsing multiple tables"""
    dbml = """
    Table users {
        id serial [pk]
        name text
    }

    Table posts {
        id serial [pk]
        title text
    }

    Table comments {
        id serial [pk]
        content text
    }
    """
    tables = parse_dbml(dbml)

    assert len(tables) == 3
    table_names = [t.name for t in tables]
    assert "users" in table_names
    assert "posts" in table_names
    assert "comments" in table_names
