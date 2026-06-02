"""Generator functions for creating FastAPI application files."""

from .core import generate_single_model, parse_dbml, parse_dbml_enums, to_class_name
from .models import TableInfo


def generate_crud_router(table: TableInfo) -> str:
    """Generate CRUD router for a single table."""
    model_name = to_class_name(table.name)
    router_name = f"{table.name}_router"

    return f"""from fastcrud import crud_router
from .model import {model_name}, {model_name}Create, {model_name}Update


def create_{table.name}_router(get_session_func):
    \"\"\"Create CRUD router with session dependency\"\"\"
    return crud_router(
        model={model_name},
        create_schema={model_name}Create,
        update_schema={model_name}Update,
        path='/{table.name}',
        tags=['{table.name}'],
        session=get_session_func
    )


# This will be initialized in main.py
{router_name} = None
"""


def generate_admin_views(tables: list[TableInfo], admin_auth_enabled: bool = False) -> str:
    """Generate SQLAdmin views for all tables."""
    imports = "\n".join(
        [f"from models.{table.name} import {to_class_name(table.name)}" for table in tables]
    )

    if admin_auth_enabled:
        admin_imports = """import os
import secrets

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware
"""
        auth_block = """class AdminAuth(AuthenticationBackend):
    async def login(self, request):
        form = await request.form()
        username = str(form.get("username") or "")
        password = str(form.get("password") or "")
        expected_user = os.getenv("ADMIN_USER") or ""
        expected_pass = os.getenv("ADMIN_PASS") or ""
        # Constant-time comparison to avoid leaking credentials via timing
        if secrets.compare_digest(username, expected_user) and secrets.compare_digest(
            password, expected_pass
        ):
            request.session.update({"admin": True})
            return True
        return False

    async def logout(self, request):
        request.session.clear()
        return True

    async def authenticate(self, request):
        return bool(request.session.get("admin"))

"""
        init_admin_header = """def init_admin(app, engine):
    app.add_middleware(SessionMiddleware, secret_key=os.getenv("ADMIN_SECRET", "change-me"))
    auth = AdminAuth(secret_key=os.getenv("ADMIN_SECRET", "change-me"))
    admin = Admin(app, engine, authentication_backend=auth)

"""
    else:
        admin_imports = "from sqladmin import Admin, ModelView\n"
        auth_block = ""
        init_admin_header = """def init_admin(app, engine):
    admin = Admin(app, engine)

"""

    code = f"""{admin_imports}

{imports}

# Default icons for different table types
DEFAULT_ICONS = {{
    'user': 'fa-solid fa-user',
    'product': 'fa-solid fa-box',
    'order': 'fa-solid fa-shopping-cart',
    'team': 'fa-solid fa-users',
    'skill': 'fa-solid fa-star',
    'scenario': 'fa-solid fa-diagram-project',
    'function': 'fa-solid fa-code',
    'status': 'fa-solid fa-circle-check',
    'stage': 'fa-solid fa-layer-group',
    'action': 'fa-solid fa-bolt',
    'default': 'fa-solid fa-table'
}}

def get_icon_for_table(table_name):
    \"\"\"Select icon based on table name\"\"\"
    name_lower = table_name.lower()
    for keyword, icon in DEFAULT_ICONS.items():
        if keyword in name_lower:
            return icon
    return DEFAULT_ICONS['default']

{auth_block}{init_admin_header}"""
    for table in tables:
        model_name = to_class_name(table.name)

        code += f"    class {model_name}Admin(ModelView, model={model_name}):\n"
        code += f"        name = '{model_name}'\n"
        code += f"        name_plural = '{model_name}'\n"
        code += f"        icon = get_icon_for_table('{table.name}')\n"
        code += f"        column_list = [c.name for c in {model_name}.__table__.columns]\n"

        # Add column_labels with descriptions from notes
        labels = {c.name: c.note for c in table.columns if c.note}
        if labels:
            code += "        column_labels = {\n"
            for col_name, note in labels.items():
                note_escaped = note.replace("'", "\\'")
                code += f"            '{col_name}': '{note_escaped}',\n"
            code += "        }\n"

        # Enable sorting for all columns
        sortable_columns = [c.name for c in table.columns]
        code += f"        column_sortable_list = {sortable_columns}\n"

        # Add search for text fields
        text_types = ["varchar", "text", "string", "str", "char"]
        searchable_columns = [
            c.name for c in table.columns if any(t in c.type.lower() for t in text_types)
        ]
        if searchable_columns:
            code += f"        column_searchable_list = {searchable_columns}\n"

        code += f"\n    admin.add_view({model_name}Admin)\n\n"

    code += "    return admin\n"
    return code


def generate_main_app(tables: list[TableInfo]) -> str:
    """Generate main FastAPI application file."""
    router_imports = "\n".join(
        [f"from models.{table.name} import create_{table.name}_router" for table in tables]
    )
    router_creates = "\n".join(
        [f"{table.name}_router = create_{table.name}_router(get_session)" for table in tables]
    )
    router_includes = "\n".join([f"app.include_router({table.name}_router)" for table in tables])

    return f"""import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from dotenv import load_dotenv


load_dotenv()


# Read the database URL from the environment (.env), with a sensible default.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

# Database engine with basic configuration suitable for development.
# For production deployments, consider tuning these parameters:
#   pool_size - number of connections to keep open (default: 5)
#   max_overflow - max connections beyond pool_size (default: 10)
#   pool_pre_ping - verify connections before using (recommended for production)
#   pool_recycle - recycle connections after N seconds (e.g., 3600)
#   echo - set to False in production to reduce logging
# Example for production:
#   engine = create_async_engine(
#       DATABASE_URL,
#       echo=False,
#       pool_size=20,
#       max_overflow=10,
#       pool_pre_ping=True,
#       pool_recycle=3600
#   )
engine = create_async_engine(DATABASE_URL, echo=False)


# Define dependency for session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


# Create database tables on startup using the modern lifespan API
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# Import router factories AFTER get_session is defined
{router_imports}
from admin import init_admin

app = FastAPI(lifespan=lifespan)

# Create CRUD routers with session dependency
{router_creates}

# Include all CRUD routers
{router_includes}

# Mount admin panel
init_admin(app, engine)


@app.get("/")
def read_root():
    return {{"message": "FastAPI app generated from DBML"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
"""


def generate_requirements() -> str:
    """Generate requirements.txt content."""
    return """fastapi[all]>=0.128.0
sqlmodel>=0.0.31
sqladmin>=0.22.0
fastcrud>=0.20.1
uvicorn[standard]>=0.30.0
aiosqlite>=0.20.0
python-dotenv>=1.0.0
greenlet>=3.0.0
"""


def generate_model_init(table: TableInfo) -> str:
    """Generate __init__.py for model directory."""
    model_name = to_class_name(table.name)
    return f"""from .model import {model_name}, {model_name}Create, {model_name}Update
from .crud import create_{table.name}_router

__all__ = [
    "{model_name}",
    "{model_name}Create",
    "{model_name}Update",
    "create_{table.name}_router",
]
"""


def generate_models_root_init(tables: list[TableInfo]) -> str:
    """Generate root __init__.py for models directory."""
    imports = []
    all_exports = []

    for table in tables:
        model_name = to_class_name(table.name)
        imports.append(
            f"from .{table.name} import {model_name}, {model_name}Create, {model_name}Update, create_{table.name}_router"
        )
        all_exports.extend(
            [
                f'    "{model_name}"',
                f'    "{model_name}Create"',
                f'    "{model_name}Update"',
                f'    "create_{table.name}_router"',
            ]
        )

    return "\n".join(imports) + "\n\n__all__ = [\n" + ",\n".join(all_exports) + "\n]\n"


def generate_enums_file(enums: dict[str, list[str]]) -> str:
    """Generate enums module from DBML enums."""
    lines = ["from enum import Enum", ""]
    for enum_name, values in enums.items():
        class_name = to_class_name(enum_name)
        lines.append(f"class {class_name}(str, Enum):")
        lines.append(f'    """DBML enum: {enum_name}"""')
        lines.append(f'    __dbml_name__ = "{enum_name}"')
        for value in values:
            key = "".join(ch if ch.isalnum() else "_" for ch in value).upper()
            if not key or key[0].isdigit():
                key = f"VALUE_{key}"
            lines.append(f'    {key} = "{value}"')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_all_files(dbml_content: str, admin_auth_enabled: bool = False) -> dict[str, str]:
    """
    Generate all application files from DBML content.

    Returns:
        Dict mapping relative file paths to their content
    """
    tables = parse_dbml(dbml_content)
    # parse_dbml_enums already parses enums from the raw text first, then falls
    # back to PyDBML, so no extra text-extraction pass is needed here.
    enums = parse_dbml_enums(dbml_content)
    if not tables:
        raise ValueError("No tables found in DBML file")

    files = {}

    # Generate each model in its own subdirectory
    for table in tables:
        model_dir = f"models/{table.name}"

        # Create model.py
        files[f"{model_dir}/model.py"] = generate_single_model(table, tables, enums=enums)

        # Create crud.py
        files[f"{model_dir}/crud.py"] = generate_crud_router(table)

        # Create __init__.py
        files[f"{model_dir}/__init__.py"] = generate_model_init(table)

    # Create root models __init__.py
    files["models/__init__.py"] = generate_models_root_init(tables)

    if enums:
        files["models/enums.py"] = generate_enums_file(enums)

    # Create admin.py
    files["admin.py"] = generate_admin_views(tables, admin_auth_enabled=admin_auth_enabled)

    # Create main.py
    files["main.py"] = generate_main_app(tables)

    # Create requirements.txt
    files["requirements.txt"] = generate_requirements()

    return files
