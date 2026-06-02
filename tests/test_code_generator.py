"""Tests for code generator module."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.core.code_generator import (
    _format_default_value,
    generate_single_model,
    to_class_name,
)
from dbml_to_sqlmodel.models.schema import ColumnInfo, TableInfo


class TestCodeGenerator:
    """Tests for code_generator module."""

    def test_to_class_name_simple(self):
        """Test converting simple snake_case to PascalCase."""
        assert to_class_name("users") == "Users"
        assert to_class_name("user") == "User"
        assert to_class_name("user_posts") == "UserPosts"

    def test_to_class_name_empty(self):
        """Test converting empty string."""
        assert to_class_name("") == ""

    def test_to_class_name_already_pascal(self):
        """Test converting already PascalCase name."""
        assert to_class_name("Users") == "Users"

    def test_to_class_name_multiple_underscores(self):
        """Test converting name with multiple underscores."""
        assert to_class_name("user_profile_data") == "UserProfileData"

    def test_to_class_name_with_numbers(self):
        """Test converting name with numbers."""
        assert to_class_name("user_2fa") == "User2fa"

    def test_format_default_value_bool(self):
        """Test formatting boolean default values."""
        assert _format_default_value(True) == "True"
        assert _format_default_value(False) == "False"

    def test_format_default_value_string(self):
        """Test formatting string default values."""
        assert _format_default_value("hello") == "'hello'"
        assert _format_default_value("test's") == '"test\'s"'

    def test_format_default_value_number(self):
        """Test formatting number default values."""
        assert _format_default_value(42) == "42"
        assert _format_default_value(3.14) == "3.14"

    def test_generate_single_model_simple_table(self):
        """Test generating model for simple table."""
        table = TableInfo(
            name="users",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="name", type="text", primary_key=False, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="email", type="text", primary_key=False, unique=True, nullable=False
                ),
            ],
        )

        code = generate_single_model(table, [table])

        assert "class Users" in code
        assert "from sqlmodel import" in code

    def test_generate_single_model_with_nullable_column(self):
        """Test generating model with nullable column."""
        table = TableInfo(
            name="posts",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="title", type="text", primary_key=False, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="content", type="text", primary_key=False, unique=False, nullable=True
                ),
            ],
        )

        code = generate_single_model(table, [table])

        assert "Optional[str]" in code

    def test_generate_single_model_with_note(self):
        """Test generating model with field notes."""
        table = TableInfo(
            name="users",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="email",
                    type="text",
                    primary_key=False,
                    unique=False,
                    nullable=False,
                    note="User email address",
                ),
            ],
        )

        code = generate_single_model(table, [table])

        assert "DESCRIPTIONS" in code
        assert "User email address" in code

    def test_generate_single_model_with_relationship(self):
        """Test generating model with foreign key relationship."""
        users_table = TableInfo(
            name="users",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="name", type="text", primary_key=False, unique=False, nullable=False
                ),
            ],
        )

        posts_table = TableInfo(
            name="posts",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="user_id",
                    type="integer",
                    primary_key=False,
                    unique=False,
                    nullable=False,
                    references=[("users", "id")],
                ),
            ],
        )

        code = generate_single_model(posts_table, [users_table, posts_table])

        assert "Relationship" in code
        assert "TYPE_CHECKING" in code

    def test_generate_single_model_with_uuid_pk(self):
        """Test generating model with UUID primary key."""
        table = TableInfo(
            name="users",
            columns=[
                ColumnInfo(name="id", type="text", primary_key=True, unique=False, nullable=False),
                ColumnInfo(
                    name="name", type="text", primary_key=False, unique=False, nullable=False
                ),
            ],
        )

        code = generate_single_model(table, [table])

        assert "import uuid" in code

    def test_generate_single_model_with_enums(self):
        """Test generating model with enum types."""
        table = TableInfo(
            name="users",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="status",
                    type="user_status",
                    primary_key=False,
                    unique=False,
                    nullable=False,
                ),
            ],
        )

        enums = {"user_status": ["active", "inactive"]}
        code = generate_single_model(table, [table], enums=enums)

        assert "from ..enums import" in code
        assert "UserStatus" in code

    def test_generate_single_model_with_default_value(self):
        """Test generating model with default value."""
        table = TableInfo(
            name="users",
            columns=[
                ColumnInfo(
                    name="id", type="serial", primary_key=True, unique=False, nullable=False
                ),
                ColumnInfo(
                    name="active",
                    type="boolean",
                    primary_key=False,
                    unique=False,
                    nullable=False,
                    default=True,
                ),
            ],
        )

        code = generate_single_model(table, [table])

        assert "active" in code
        assert "bool" in code


def test_generate_single_model_edge_cases():
    enum_table = TableInfo(
        name="widgets",
        columns=[
            ColumnInfo(
                name="id",
                type="bool",
                primary_key=True,
                unique=False,
                nullable=False,
                note="id note",
            ),
            ColumnInfo(
                name="status",
                type="status",
                primary_key=True,
                unique=False,
                nullable=False,
            ),
        ],
        note='note """ triple',
    )
    rel_table = TableInfo(
        name="posts",
        columns=[
            ColumnInfo(
                name="user_id",
                type="integer",
                primary_key=False,
                unique=False,
                nullable=False,
                references=[("users", "id")],
            ),
        ],
    )
    nopk_table = TableInfo(
        name="logs",
        columns=[
            ColumnInfo(
                name="message",
                type="text",
                primary_key=False,
                unique=False,
                nullable=True,
            ),
        ],
    )
    all_tables = [enum_table, rel_table, nopk_table]
    enums = {"status": ["active"]}

    enum_code = generate_single_model(enum_table, all_tables, enums=enums)
    assert '"""note \\"\\"\\" triple"""' in enum_code
    assert "DESCRIPTIONS" in enum_code
    assert 'description=DESCRIPTIONS["id"]' in enum_code
    assert "status: Status" in enum_code

    rel_code = generate_single_model(rel_table, all_tables, enums=enums)
    assert "Relationship()" in rel_code

    nopk_code = generate_single_model(nopk_table, all_tables, enums=enums)
    assert "class Logs(LogsBase, table=True):\n    pass" in nopk_code


def test_singularize_branches():
    """Every branch of the relationship-name singularizer is exercised."""
    from dbml_to_sqlmodel.core.code_generator import _singularize

    # "ies" -> "y"
    assert _singularize("categories") == "category"
    # short "ies" word is left untouched (len <= 3 guard)
    assert _singularize("ies") == "ie"
    # "ses"/"xes"/"ches"/"shes"/"zes" -> drop the trailing "es"
    assert _singularize("statuses") == "status"
    assert _singularize("boxes") == "box"
    assert _singularize("batches") == "batch"
    # plain trailing "s" -> drop it
    assert _singularize("posts") == "post"
    # singular nouns ending in ss/us/is are preserved (fallback branch)
    assert _singularize("status") == "status"
    assert _singularize("address") == "address"
    assert _singularize("analysis") == "analysis"
    assert _singularize("user") == "user"
