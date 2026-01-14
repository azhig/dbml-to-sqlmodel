import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.core.parser import parse_dbml


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


def test_parse_column_with_default():
    """Test parsing column with default value"""
    dbml = """
    Table users {
        id serial [pk]
        active boolean [default: true]
        count integer [default: 0]
    }
    """
    tables = parse_dbml(dbml)

    active_col = next(c for c in tables[0].columns if c.name == "active")
    assert active_col.default is True

    count_col = next(c for c in tables[0].columns if c.name == "count")
    assert count_col.default == 0


def test_parse_multiple_references():
    """Test parsing table with multiple foreign keys"""
    dbml = """
    Table users {
        id serial [pk]
    }

    Table posts {
        id serial [pk]
        user_id integer
        editor_id integer
    }

    Ref: posts.user_id > users.id
    Ref: posts.editor_id > users.id
    """
    tables = parse_dbml(dbml)

    posts_table = next(t for t in tables if t.name == "posts")

    user_id_col = next(c for c in posts_table.columns if c.name == "user_id")
    assert user_id_col.references is not None
    assert len(user_id_col.references) > 0

    editor_id_col = next(c for c in posts_table.columns if c.name == "editor_id")
    assert editor_id_col.references is not None
    assert len(editor_id_col.references) > 0


def test_parse_table_with_indexes():
    """Test parsing table with indexes"""
    dbml = """
    Table users {
        id serial [pk]
        email text [unique]
        name text

        indexes {
            email [unique]
            name
        }
    }
    """
    tables = parse_dbml(dbml)

    assert len(tables) == 1
    assert tables[0].name == "users"


def test_parse_empty_dbml():
    """Test parsing empty DBML"""
    dbml = ""
    tables = parse_dbml(dbml)

    assert tables == []


def test_parse_table_with_various_types():
    """Test parsing table with various column types"""
    dbml = """
    Table test {
        id serial [pk]
        name varchar(255)
        age integer
        active boolean
        created_at timestamp
        data json
        price decimal
    }
    """
    tables = parse_dbml(dbml)

    assert len(tables) == 1
    assert len(tables[0].columns) == 7

    # Verify different types are parsed
    col_types = {col.name: col.type for col in tables[0].columns}
    assert "serial" in col_types.values()
    assert any(t.startswith("varchar") or t == "text" for t in col_types.values())
    assert "integer" in col_types.values()
    assert "boolean" in col_types.values()


def test_parse_table_with_composite_pk():
    """Test parsing table with composite primary key"""
    dbml = """
    Table user_roles {
        user_id integer [pk]
        role_id integer [pk]
    }
    """
    tables = parse_dbml(dbml)

    assert len(tables) == 1
    pk_columns = [col for col in tables[0].columns if col.primary_key]
    assert len(pk_columns) >= 1


def test_parse_bidirectional_relationship():
    """Test parsing bidirectional relationships"""
    dbml = """
    Table users {
        id serial [pk]
    }

    Table posts {
        id serial [pk]
        author_id integer
        editor_id integer
    }

    Ref: posts.author_id > users.id
    Ref: posts.editor_id > users.id
    """
    tables = parse_dbml(dbml)

    posts = next(t for t in tables if t.name == "posts")
    author_refs = [c for c in posts.columns if c.name == "author_id" and c.references]
    editor_refs = [c for c in posts.columns if c.name == "editor_id" and c.references]

    assert len(author_refs) > 0
    assert len(editor_refs) > 0
