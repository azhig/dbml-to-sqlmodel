# CLI Examples

Comprehensive examples for using the DBML to CRUD Generator CLI.

## Basic Commands

### Show Help

```bash
# Main help
uv run dbml-crud --help

# Command-specific help
uv run dbml-crud generate --help
uv run dbml-crud preview --help
uv run dbml-crud info --help
```

### Version Information

```bash
uv run dbml-crud version
```

## Generate Command

### Basic Generation

```bash
# Generate with default output directory (output/)
uv run dbml-crud generate schemas/schema.dbml

# Generate to custom directory
uv run dbml-crud generate schemas/schema.dbml -o my_app

# Shorter form
uv run dbml-crud generate schemas/schema.dbml -o my_app
```

### Advanced Generation

```bash
# Force overwrite protected files
uv run dbml-crud generate schemas/schema.dbml --force
```

### Using Make Shortcuts

```bash
# Generate using default schema (schemas/schema.dbml -> output/)
make generate

# Preview changes
make preview

# Show schema info
make info
```

## Preview Command

### Basic Preview

```bash
# Show diff for modified files
uv run dbml-crud preview schemas/schema.dbml

# Preview with custom output directory
uv run dbml-crud preview schemas/schema.dbml -o my_app
```

### Advanced Preview

```bash
# Show all files including unchanged
uv run dbml-crud preview schemas/schema.dbml --all

# Show content of new files
uv run dbml-crud preview schemas/schema.dbml --new

# Combine options
uv run dbml-crud preview schemas/schema.dbml --all --new
```

### Preview Output Example

```
╭──────────────────────────────────────────────────────────────────╮
│ Preview Mode - Showing Diffs                                     │
│ Schema: schemas/schema.dbml                                      │
│ Output: output                                                   │
╰──────────────────────────────────────────────────────────────────╯

                        File Status
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ File                   ┃ Status      ┃ Action      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ models/user/model.py   │ 📝 Changed  │ Will update │
│ models/post/model.py   │ 🔒 Protected│ Skipped     │
│ models/team/model.py   │ ✓ Unchanged │ No action   │
└────────────────────────┴─────────────┴─────────────┘

╭────────────────── models/user/model.py ──────────────────╮
│ --- a/models/user/model.py                              │
│ +++ b/models/user/model.py                              │
│ @@ -10,3 +10,4 @@                                   │
│  app = FastAPI()                                    │
│ +# New route                                        │
╰─────────────────────────────────────────────────────╯
```

## Report Command

### Basic Report

```bash
# Show generated file list and mismatches
uv run dbml-crud info schemas/schema.dbml

# With custom output directory
uv run dbml-crud info schemas/schema.dbml -o my_app
```

### Report Output Example

#### Example Output

```
╭──────────────────────────────────────────────────────────────────╮
│ Report                                                            │
│ Schema: schemas/schema.dbml                                       │
│ Output: output                                                    │
╰──────────────────────────────────────────────────────────────────╯

                         File Status
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ File                  ┃ Status      ┃ Action      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ models/user/model.py  │ 📝 Changed  │ Will update │
│ models/post/model.py  │ ✓ Unchanged │ No action   │
│ models/team/model.py  │ 🔒 Protected│ Skipped     │
└───────────────────────┴─────────────┴─────────────┘

╭────────────────── models/user/model.py ──────────────────╮
│ --- a/models/user/model.py                              │
│ +++ b/models/user/model.py                              │
│ @@ -10,3 +10,4 @@                                       │
│  class User(SQLModel, table=True):                       │
│ +    nickname: str | None = Field(default=None)          │
╰──────────────────────────────────────────────────────────╯
```

## Working with Protected Files

### Marking Files as Protected

```bash
# Edit a generated file
vim output/models/users/model.py

# Add at the very top:
# USER_MODIFIED
# This file has custom changes

# Save and exit
```

### Testing Protection

```bash
# Preview - will show file as protected
uv run dbml-crud preview schemas/schema.dbml

# Generate - will skip protected file
uv run dbml-crud generate schemas/schema.dbml

# Force overwrite (bypasses protection)
uv run dbml-crud generate schemas/schema.dbml --force
```

### Protection Example Output

```
╭────────────── models/users/model.py ──────────────╮
│ 🔒 Protected file (USER_MODIFIED)                 │
│ This file will be skipped during generation       │
│ unless --force is used                            │
╰───────────────────────────────────────────────────╯
```

## Complete Workflows

### Workflow 1: New Project

```bash
# 1. Create DBML schema
vim schemas/blog.dbml

# 2. Inspect schema
uv run dbml-crud info schemas/blog.dbml -v

# 3. Preview generation
uv run dbml-crud preview schemas/blog.dbml -o blog_app

# 4. Generate app
uv run dbml-crud generate schemas/blog.dbml -o blog_app

# 5. Run app
cd blog_app
uv run uvicorn main:app --reload --port 8001

# 6. Open browser
# http://localhost:8001/admin
```

### Workflow 2: Update Existing Project

```bash
# 1. Edit DBML schema
vim schemas/blog.dbml
# (add new table or modify existing)

# 2. Preview changes
uv run dbml-crud preview schemas/blog.dbml -o blog_app
# Review diff output

# 3. Apply changes
uv run dbml-crud generate schemas/blog.dbml -o blog_app
# Protected files are automatically skipped

# 4. Restart app
cd blog_app
uv run uvicorn main:app --reload --port 8001
```

### Workflow 3: Protect Custom Code

```bash
# 1. Generate initial app
uv run dbml-crud generate schemas/blog.dbml -o blog_app

# 2. Customize a file
vim blog_app/models/users/model.py
# Add custom methods, properties, etc.

# 3. Mark as protected
# Add "# USER_MODIFIED" at top of file

# 4. Update schema
vim schemas/blog.dbml
# Make changes

# 5. Preview
uv run dbml-crud preview schemas/blog.dbml -o blog_app
# Your file shows as 🔒 Protected

# 6. Generate safely
uv run dbml-crud generate schemas/blog.dbml -o blog_app
# Your custom code is preserved!
```

### Workflow 4: Multiple Projects

```bash
# Generate different apps from different schemas
uv run dbml-crud generate schemas/blog.dbml -o projects/blog
uv run dbml-crud generate schemas/ecommerce.dbml -o projects/shop
uv run dbml-crud generate schemas/crm.dbml -o projects/crm

# Preview all
uv run dbml-crud preview schemas/blog.dbml -o projects/blog
uv run dbml-crud preview schemas/ecommerce.dbml -o projects/shop
uv run dbml-crud preview schemas/crm.dbml -o projects/crm
```

## Integration with Make

### Quick Commands

```bash
# Default workflow (uses schemas/schema.dbml)
make info          # Inspect schema
make preview       # Show diff
make generate      # Generate app
make dev           # Run with hot-reload

# Cleanup
make clean         # Remove output/
make db-reset      # Delete database
make fresh         # Clean + regenerate
make full-reset    # Complete reset

# Code quality
make format        # Format with ruff
make lint          # Lint with ruff
```

### Custom Schema with Make

```bash
# Edit Makefile to use different schema
vim Makefile

# Change:
# generate: ## Generate FastAPI application
#     uv run dbml-crud generate schemas/schema.dbml -o output

# To:
# generate: ## Generate FastAPI application
#     uv run dbml-crud generate schemas/my_schema.dbml -o my_app
```

## Advanced Usage

### Shell Completion

```bash
# Install shell completion
uv run dbml-crud --install-completion

# Show completion script
uv run dbml-crud --show-completion
```

### Piping and Scripting

```bash
# Count files to be generated
uv run dbml-crud info schemas/schema.dbml | grep "Tables:" | awk '{print $2}'

# Check if any files are protected
uv run dbml-crud preview schemas/schema.dbml | grep "Protected"

# Generate with logging
uv run dbml-crud generate schemas/schema.dbml 2>&1 | tee generation.log

# Conditional generation
if uv run dbml-crud preview schemas/schema.dbml | grep -q "Protected"; then
    echo "Protected files detected - review before generating"
else
    uv run dbml-crud generate schemas/schema.dbml
fi
```

### CI/CD Integration

```yaml
# .github/workflows/generate.yml
name: Generate App

on:
  push:
    paths:
      - 'schemas/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Preview changes
        run: uv run dbml-crud preview schemas/schema.dbml -o output

      - name: Generate app
        run: uv run dbml-crud generate schemas/schema.dbml -o output

      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add output/
          git commit -m "Auto-generate from schema" || exit 0
          git push
```

## Troubleshooting Examples

### Error: File Not Found

```bash
# Problem
uv run dbml-crud generate schemas/missing.dbml
# Error: Path does not exist: schemas/missing.dbml

# Solution
ls schemas/  # Check available schemas
uv run dbml-crud generate schemas/schema.dbml  # Use correct file
```

### Error: Import Module

```bash
# Problem
uv run dbml-crud generate schemas/schema.dbml
# ModuleNotFoundError: No module named 'dbml_to_crud'

# Solution
uv sync  # Reinstall dependencies
```

### Protected File Override

```bash
# View protected files
uv run dbml-crud preview schemas/schema.dbml | grep Protected

# Option 1: Remove marker
vim output/models/users/model.py
# Delete "# USER_MODIFIED" line

# Option 2: Force overwrite
uv run dbml-crud generate schemas/schema.dbml --force
```

## Tips and Best Practices

### 1. Always Preview First

```bash
# Good practice
uv run dbml-crud preview schemas/schema.dbml
uv run dbml-crud generate schemas/schema.dbml

# Skip preview only for new projects
```

### 2. Use Report for File Validation

```bash
# Check schema before generating
uv run dbml-crud info schemas/schema.dbml -v
# Verify tables, columns, relationships
```

### 3. Protect Custom Code Immediately

```bash
# Right after customizing
vim output/models/users/model.py
# Add USER_MODIFIED marker
```

### 4. Use Make for Common Tasks

```bash
# Instead of long commands
make preview   # vs uv run dbml-crud preview schemas/schema.dbml -o output
make generate  # vs uv run dbml-crud generate schemas/schema.dbml -o output
```

### 5. Version Control Your Schemas

```bash
git add schemas/
git commit -m "Update database schema"

# Keep output/ in .gitignore
echo "output/" >> .gitignore
```

## See Also

- [README.md](README.md) - Main documentation
- [CLAUDE.md](CLAUDE.md) - Developer guide for Claude Code
- [Makefile](Makefile) - Available make commands
