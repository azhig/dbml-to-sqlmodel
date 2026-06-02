"""Tests for utility modules."""

import shutil
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.constants import USER_FILE_MARKER
from dbml_to_sqlmodel.models.file_info import FileInfo, FileStatus
from dbml_to_sqlmodel.utils import diff as diff_module
from dbml_to_sqlmodel.utils.diff import (
    apply_diff_to_file,
    generate_diff,
    normalize_model_code,
)
from dbml_to_sqlmodel.utils.file_manager import (
    calculate_file_status,
    get_user_modified_files,
    is_user_modified,
    mark_as_user_modified,
)
from dbml_to_sqlmodel.utils.formatters import print_file_status_table
from dbml_to_sqlmodel.utils.type_mapping import (
    get_python_type,
    is_auto_increment_type,
)


class TestTypeMapping:
    """Tests for type_mapping module."""

    def test_get_python_type_known_types(self):
        """Test type mapping for known DBML types."""
        assert get_python_type("int") == "int"
        assert get_python_type("integer") == "int"
        assert get_python_type("serial") == "int"
        assert get_python_type("varchar") == "str"
        assert get_python_type("text") == "str"
        assert get_python_type("bool") == "bool"
        assert get_python_type("boolean") == "bool"
        assert get_python_type("float") == "float"
        assert get_python_type("json") == "dict"

    def test_get_python_type_case_insensitive(self):
        """Test that type mapping is case insensitive."""
        assert get_python_type("INT") == "int"
        assert get_python_type("Integer") == "int"
        assert get_python_type("VARCHAR") == "str"
        assert get_python_type("BOOLEAN") == "bool"

    def test_get_python_type_unknown_defaults_to_str(self):
        """Test that unknown types default to str."""
        assert get_python_type("unknown_type") == "str"
        assert get_python_type("custom") == "str"

    def test_is_auto_increment_type(self):
        """Test auto-increment type detection."""
        assert is_auto_increment_type("serial") is True
        assert is_auto_increment_type("serial4") is True
        assert is_auto_increment_type("serial8") is True
        assert is_auto_increment_type("bigserial") is True

    def test_is_auto_increment_type_case_insensitive(self):
        """Test auto-increment detection is case insensitive."""
        assert is_auto_increment_type("SERIAL") is True
        assert is_auto_increment_type("Serial4") is True

    def test_is_not_auto_increment_type(self):
        """Test non-auto-increment types."""
        assert is_auto_increment_type("int") is False
        assert is_auto_increment_type("integer") is False
        assert is_auto_increment_type("varchar") is False


class TestFileManager:
    """Tests for file_manager module."""

    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup temporary directory after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_is_user_modified_nonexistent_file(self):
        """Test user modified check on nonexistent file."""
        file_path = self.temp_dir / "nonexistent.py"
        assert is_user_modified(file_path) is False

    def test_is_user_modified_file_without_marker(self):
        """Test user modified check on file without marker."""
        file_path = self.temp_dir / "test.py"
        file_path.write_text("# Some code\nprint('hello')")
        assert is_user_modified(file_path) is False

    def test_is_user_modified_file_with_marker(self):
        """Test user modified check on file with marker."""
        file_path = self.temp_dir / "test.py"
        file_path.write_text(f"{USER_FILE_MARKER}\n# Some code\nprint('hello')")
        assert is_user_modified(file_path) is True

    def test_mark_as_user_modified_nonexistent_file(self):
        """Test marking nonexistent file as user modified."""
        file_path = self.temp_dir / "nonexistent.py"
        mark_as_user_modified(file_path)  # Should not raise error
        assert file_path.exists() is False

    def test_mark_as_user_modified_adds_marker(self):
        """Test marking file as user modified adds marker."""
        file_path = self.temp_dir / "test.py"
        original_content = "# Some code\nprint('hello')"
        file_path.write_text(original_content)

        mark_as_user_modified(file_path)

        content = file_path.read_text()
        assert USER_FILE_MARKER in content
        assert "Some code" in content

    def test_mark_as_user_modified_idempotent(self):
        """Test marking already marked file doesn't duplicate marker."""
        file_path = self.temp_dir / "test.py"
        file_path.write_text("# Some code")

        mark_as_user_modified(file_path)
        first_content = file_path.read_text()

        mark_as_user_modified(file_path)
        second_content = file_path.read_text()

        assert first_content == second_content

    def test_get_user_modified_files_empty_directory(self):
        """Test getting user modified files from empty directory."""
        assert get_user_modified_files(self.temp_dir) == []

    def test_get_user_modified_files_nonexistent_directory(self):
        """Test getting user modified files from nonexistent directory."""
        nonexistent = self.temp_dir / "nonexistent"
        assert get_user_modified_files(nonexistent) == []

    def test_get_user_modified_files(self):
        """Test getting user modified files."""
        # Create some files
        normal_file = self.temp_dir / "normal.py"
        normal_file.write_text("print('normal')")

        modified_file = self.temp_dir / "modified.py"
        modified_file.write_text(f"{USER_FILE_MARKER}\nprint('modified')")

        # Create subdirectory with modified file
        sub_dir = self.temp_dir / "sub"
        sub_dir.mkdir()
        sub_modified = sub_dir / "sub_modified.py"
        sub_modified.write_text(f"{USER_FILE_MARKER}\nprint('sub')")

        user_files = get_user_modified_files(self.temp_dir)

        assert len(user_files) == 2
        assert modified_file in user_files
        assert sub_modified in user_files
        assert normal_file not in user_files

    def test_calculate_file_status_new_file(self):
        """Test calculating status for new file."""
        generated = {"new.py": "print('hello')"}
        status = calculate_file_status(self.temp_dir, generated)

        assert status["new.py"] == ("created", False)

    def test_calculate_file_status_unchanged_file(self):
        """Test calculating status for unchanged file."""
        file_path = self.temp_dir / "test.py"
        content = "print('hello')"
        file_path.write_text(content)

        generated = {"test.py": content}
        status = calculate_file_status(self.temp_dir, generated)

        assert status["test.py"] == ("unchanged", False)

    def test_calculate_file_status_modified_file(self):
        """Test calculating status for modified file."""
        file_path = self.temp_dir / "test.py"
        file_path.write_text("print('old')")

        generated = {"test.py": "print('new')"}
        status = calculate_file_status(self.temp_dir, generated)

        assert status["test.py"] == ("modified", False)

    def test_calculate_file_status_protected_file(self):
        """Test calculating status for protected file."""
        file_path = self.temp_dir / "test.py"
        file_path.write_text(f"{USER_FILE_MARKER}\nprint('protected')")

        generated = {"test.py": "print('new')"}
        status = calculate_file_status(self.temp_dir, generated)

        assert status["test.py"] == ("protected", True)

    def test_calculate_file_status_with_normalizer(self):
        """Test calculating status with normalizer function."""
        file_path = self.temp_dir / "test.py"
        file_path.write_text("print('hello')  ")  # Extra spaces

        generated = {"test.py": "  print('hello')"}  # Different whitespace

        def normalizer(text):
            return text.strip()

        status = calculate_file_status(self.temp_dir, generated, normalizer)
        assert status["test.py"] == ("unchanged", False)


class TestDiff:
    """Tests for diff module."""

    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup temporary directory after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_normalize_model_code_valid_python(self):
        """Test normalizing valid Python code."""
        code = """
def hello():
    print('world')


class Test:
    pass
        """
        normalized = normalize_model_code(code)
        assert "def hello():" in normalized
        assert "class Test:" in normalized

    def test_normalize_model_code_invalid_syntax(self):
        """Test normalizing invalid Python falls back to simple normalization."""
        code = "def incomplete("
        normalized = normalize_model_code(code)
        assert "def incomplete(" in normalized

    def test_normalize_model_code_removes_blank_lines(self):
        """Test that fallback normalization removes blank lines."""
        code = "line1\n\nline2\n\n\nline3"
        normalized = normalize_model_code(code)
        assert normalized.count("\n") <= 2

    def test_generate_diff_identical_content(self):
        """Test generating diff for identical content."""
        original = "print('hello')"
        modified = "print('hello')"
        diff = generate_diff(original, modified, "test.py")
        assert diff == ""

    def test_generate_diff_different_content(self):
        """Test generating diff for different content."""
        original = "print('hello')"
        modified = "print('world')"
        diff = generate_diff(original, modified, "test.py")

        assert "test.py" in diff
        assert "-print('hello')" in diff
        assert "+print('world')" in diff

    def test_generate_diff_multiline(self):
        """Test generating diff for multiline content."""
        original = "line1\nline2\nline3"
        modified = "line1\nmodified line2\nline3"
        diff = generate_diff(original, modified, "test.py")

        assert "-line2" in diff
        assert "+modified line2" in diff

    def test_apply_diff_to_new_file(self):
        """Test applying diff to non-existent file creates it."""
        file_path = self.temp_dir / "new_file.py"
        content = "print('hello')"

        result = apply_diff_to_file(file_path, "", content)

        assert result is True
        assert file_path.exists()
        assert file_path.read_text() == content

    def test_apply_diff_to_identical_file(self):
        """Test applying diff to identical file returns False."""
        file_path = self.temp_dir / "test.py"
        content = "print('hello')"
        file_path.write_text(content)

        result = apply_diff_to_file(file_path, content, content)

        assert result is False

    def test_apply_diff_to_existing_file(self):
        """Test applying diff modifies existing file."""
        file_path = self.temp_dir / "test.py"
        original = "print('hello')"
        modified = "print('world')"
        file_path.write_text(original)

        result = apply_diff_to_file(file_path, original, modified)

        assert result is True
        assert "world" in file_path.read_text()


class TestFormatters:
    """Tests for formatters module."""

    def test_print_file_status_table_new_file(self):
        """Test printing status for new file."""
        files_status = {"new.py": ("created", False)}
        print_file_status_table(files_status)

    def test_print_file_status_table_modified_file(self):
        """Test printing status for modified file."""
        files_status = {"test.py": ("modified", False)}
        print_file_status_table(files_status)

    def test_print_file_status_table_unchanged_file(self):
        """Test printing status for unchanged file."""
        files_status = {"test.py": ("unchanged", False)}
        print_file_status_table(files_status)

    def test_print_file_status_table_protected_file(self):
        """Test printing status for protected file."""
        files_status = {"test.py": ("protected", True)}
        print_file_status_table(files_status)

    def test_print_file_status_table_multiple_files(self):
        """Test printing status for multiple files."""
        files_status = {
            "new.py": ("created", False),
            "modified.py": ("modified", False),
            "protected.py": ("protected", True),
            "unchanged.py": ("unchanged", False),
        }
        print_file_status_table(files_status)


def test_file_info_status_tuple():
    info_obj = FileInfo("a.py", FileStatus.CREATED, True)
    assert info_obj.status_tuple == ("created", True)


def test_diff_helpers(tmp_path, monkeypatch):
    diff_module.print_diff("", "file.txt")
    diff_module.print_diff("-a\n+b", "file.txt")

    file_path = tmp_path / "file.txt"
    assert diff_module.apply_diff_to_file(file_path, "old", "new") is True
    assert file_path.read_text(encoding="utf-8") == "new"

    assert diff_module.apply_diff_to_file(file_path, "new", "new") is False

    original_generate_diff = diff_module.generate_diff
    monkeypatch.setattr(diff_module, "generate_diff", lambda *_args, **_kwargs: "")
    file_path.write_text("old", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "old", "new") is False

    monkeypatch.setattr(diff_module, "generate_diff", original_generate_diff)

    file_path.write_text("a\nb\nc\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\nc\n", "a\nx\nc\n") is True

    file_path.write_text("z\nb\ny\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\nc\n", "a\nx\nc\n") is True

    file_path.write_text("a\nb\nz\nc\nd\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\nc\nd\n", "a\nx\ny\nd\n") is True

    file_path.write_text("q\nw\n", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "a\nb\n", "a\nx\n") is False

    file_path.write_text("", encoding="utf-8")
    assert diff_module.apply_diff_to_file(file_path, "", "a\n") is False

    class Boom(Exception):
        pass

    def raise_patch(_text):
        raise Boom("fail")

    monkeypatch.setattr(diff_module, "PatchSet", raise_patch)
    assert diff_module.apply_diff_to_file(file_path, "a\n", "b\n") is False
