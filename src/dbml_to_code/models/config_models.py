"""Configuration models."""

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration."""

    schema_file: str = Field(default="examples/schema.dbml", description="Default DBML schema file path")
    output_dir: str = Field(default="output", description="Default output directory")
    show_all_files: bool = Field(default=False, description="Show all files in preview by default")
    show_new_content: bool = Field(default=False, description="Show content of new files in preview by default")
    force_overwrite: bool = Field(default=False, description="Force overwrite protected files by default")
    admin_auth_enabled: bool = Field(default=False, description="Require login for SQLAdmin panel")
