"""Tests for configuration management."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dbml_to_sqlmodel.core.config import ConfigManager
from dbml_to_sqlmodel.models.config_models import AppConfig


class TestConfigManager:
    """Tests for ConfigManager class."""

    def setup_method(self):
        """Setup temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / ".test_config"

    def teardown_method(self):
        """Cleanup temporary directory after each test."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_init_default_path(self):
        """Test ConfigManager initialization with default path."""
        manager = ConfigManager()
        assert manager.config_path.name == ".dbml_to_sqlmodel"

    def test_init_custom_path(self):
        """Test ConfigManager initialization with custom path."""
        manager = ConfigManager(self.config_path)
        assert manager.config_path == self.config_path

    def test_is_first_run_no_config(self):
        """Test is_first_run returns True when config doesn't exist."""
        manager = ConfigManager(self.config_path)
        assert manager.is_first_run() is True

    def test_is_first_run_with_config(self):
        """Test is_first_run returns False when config exists."""
        self.config_path.write_text("{}")
        manager = ConfigManager(self.config_path)
        assert manager.is_first_run() is False

    def test_load_creates_default_config(self):
        """Test load creates default config on first run."""
        manager = ConfigManager(self.config_path)
        config = manager.load()

        assert isinstance(config, AppConfig)
        assert self.config_path.exists()

    def test_load_reads_existing_config(self):
        """Test load reads existing config file."""
        config_data = {
            "schema_file": "custom_schema.dbml",
            "output_dir": "custom_output",
            "show_all_files": True,
            "show_new_content": True,
            "force_overwrite": True,
            "admin_auth_enabled": True,
        }
        self.config_path.write_text(json.dumps(config_data))

        manager = ConfigManager(self.config_path)
        config = manager.load()

        assert config.schema_file == "custom_schema.dbml"
        assert config.output_dir == "custom_output"
        assert config.show_all_files is True
        assert config.admin_auth_enabled is True

    def test_load_handles_corrupted_config(self):
        """Test load creates new config when existing is corrupted."""
        self.config_path.write_text("invalid json{")

        manager = ConfigManager(self.config_path)
        config = manager.load()

        assert isinstance(config, AppConfig)
        # Should have created new default config
        assert config.schema_file == "examples/schema.dbml"

    def test_config_property_loads_if_needed(self):
        """Test config property loads config if not loaded."""
        manager = ConfigManager(self.config_path)
        assert manager._config is None

        config = manager.config

        assert config is not None
        assert isinstance(config, AppConfig)

    def test_save_creates_config_file(self):
        """Test save creates config file."""
        manager = ConfigManager(self.config_path)
        manager._config = AppConfig()
        manager.save()

        assert self.config_path.exists()
        data = json.loads(self.config_path.read_text())
        assert "schema_file" in data
        assert "output_dir" in data

    def test_save_without_config_creates_default(self):
        """Test save without config creates default."""
        manager = ConfigManager(self.config_path)
        manager.save()

        assert self.config_path.exists()
        data = json.loads(self.config_path.read_text())
        assert data["schema_file"] == "examples/schema.dbml"

    def test_update_changes_config(self):
        """Test update changes config values."""
        manager = ConfigManager(self.config_path)
        manager.load()

        manager.update(schema_file="new_schema.dbml", output_dir="new_output")

        assert manager.config.schema_file == "new_schema.dbml"
        assert manager.config.output_dir == "new_output"

        # Check that it was saved
        data = json.loads(self.config_path.read_text())
        assert data["schema_file"] == "new_schema.dbml"

    def test_update_loads_config_if_needed(self):
        """Test update loads config if not loaded."""
        manager = ConfigManager(self.config_path)
        assert manager._config is None

        manager.update(schema_file="test.dbml")

        assert manager._config is not None
        assert manager.config.schema_file == "test.dbml"

    def test_update_ignores_unknown_fields(self):
        """Test update ignores unknown fields."""
        manager = ConfigManager(self.config_path)
        manager.load()

        # Should not raise error
        manager.update(unknown_field="value", schema_file="test.dbml")

        assert manager.config.schema_file == "test.dbml"

    def test_reset_restores_defaults(self):
        """Test reset restores default config."""
        manager = ConfigManager(self.config_path)
        manager.load()
        manager.update(schema_file="custom.dbml")

        manager.reset()

        assert manager.config.schema_file == "examples/schema.dbml"
        assert manager.config.output_dir == "output"

        # Check that it was saved
        data = json.loads(self.config_path.read_text())
        assert data["schema_file"] == "examples/schema.dbml"
