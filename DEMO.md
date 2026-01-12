# 🎬 Демонстрация интерактивного CLI

## Запуск

```bash
$ uv run dbml-crud
```

## Экран 1: Приветствие

```
╭──────────────────────────────────────────────────────────────╮
│ Welcome                                                      │
│ 🚀 DBML to CRUD Generator                                    │
│                                                              │
│ Modern FastAPI + SQLModel + FastCRUD generator from DBML     │
│ schemas                                                      │
╰──────────────────────────────────────────────────────────────╯

? Что вы хотите сделать?
  ⚙️  Настройки
  🎯 DBML → Code
  🔁 Code → DBML
❯ 📊 Report
  ❌ Выход
```

*Используйте ↑↓ для навигации, Enter для выбора*

## Экран 2: DBML → Code - Использование настроек

```
Используются настройки из .dbml_to_crud
```

## Экран 3: Автоматический Preview (если директория существует)

```
╭─────────────────────────────────────────────────────────────╮
│ ⚠️  Внимание                                                 │
│ Директория вывода уже существует.                           │
│ Сначала показываем предпросмотр изменений...                │
╰─────────────────────────────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────╮
│ Preview Mode - Showing Diffs                                 │
│ Schema: schemas/schema.dbml                                  │
│ Output: output                                               │
╰───────────────────────────────────────────────────────────────╯

                        File Status
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ File                   ┃ Status      ┃ Action      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ models/user/model.py   │ 📝 Changed  │ Will update │
│ models/post/model.py   │ ✓ Unchanged │ No action   │
│ models/team/model.py   │ 🔒 Protected│ Skipped     │
└────────────────────────┴─────────────┴─────────────┘

╭────────────────── models/user/model.py ──────────────────╮
│ --- a/models/user/model.py                              │
│ +++ b/models/user/model.py                              │
│ @@ -10,3 +10,4 @@                                       │
│  class User(SQLModel, table=True):                       │
│ +    nickname: str | None = Field(default=None)          │
╰──────────────────────────────────────────────────────────╯

Summary:
  New files: 1
  Modified files: 2
  Unchanged files: 5
  Protected files: 1
```

## Экран 5: Подтверждение применения изменений

```
? Применить изменения? (y/N)
```

*Нажмите Y и Enter для применения*

## Экран 6: Опции генерации

```
```

*Нажмите N (или просто Enter)*

```
? Перезаписать защищенные файлы (USER_MODIFIED)? (y/N)
```

*Нажмите N (или просто Enter)*

## Экран 7: Процесс генерации

```
╭───────────────────────────────────────────────────────────────╮
│ Generation Mode                                              │
│ Schema: schemas/schema.dbml                                  │
│ Output: output                                               │
╰───────────────────────────────────────────────────────────────╯

⠹ Parsing DBML schema...

⠹ Generating files...

                        File Status
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ File                   ┃ Status      ┃ Action      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ main.py                │ 📝 Changed  │ ✓ Updated   │
│ admin.py               │ ✓ Unchanged │ ⊘ Skipped   │
│ models/user/model.py   │ 🔒 Protected│ ⊘ Skipped   │
│ models/post/model.py   │ 📝 Changed  │ ✓ Updated   │
│ models/comment/...     │ 🆕 New      │ ✓ Created   │
└────────────────────────┴─────────────┴─────────────┘

╭───────────────────── Summary ─────────────────────╮
│ ✓ Files written: 3                                │
│ ⊘ Files skipped: 2 (1 protected, 1 unchanged)    │
│ 🆕 New files: 1                                   │
╰───────────────────────────────────────────────────╯

✓ Generation complete!
```

## Экран 8: Возврат в меню

```
CLI возвращается в главное меню
```

---

## Другие команды

### 📊 Report

```
? Что вы хотите сделать?
❯ 📊 Report

Используются настройки из .dbml_to_crud

╭───────────────────────────────────────────────────────╮
│ Report                                                │
│ Schema: schemas/schema.dbml                           │
│ Output: output                                        │
╰───────────────────────────────────────────────────────╯

                        File Status
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ File                  ┃ Status      ┃ Action      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ main.py               │ 📝 Changed  │ Will update │
│ admin.py              │ ✓ Unchanged │ No action   │
│ models/user/model.py  │ 🔒 Protected│ Skipped     │
└───────────────────────┴─────────────┴─────────────┘

╭────────────────────── main.py ──────────────────────╮
│ --- a/main.py                                       │
│ +++ b/main.py                                       │
│ @@ -10,3 +10,4 @@                                   │
│  app = FastAPI()                                    │
│ +# New route                                        │
╰─────────────────────────────────────────────────────╯
```

---

## Горячие клавиши

- **↑↓** - Навигация
- **Enter** - Выбрать
- **Y/N** - Ответить
- **Ctrl+C** - Отменить операцию
- **Ctrl+D** - Выход

## Следующие шаги

После генерации запустите приложение:

```bash
cd output
uv run uvicorn main:app --reload --port 8001
```

Откройте браузер:
- API Docs: http://localhost:8001/docs
- Admin Panel: http://localhost:8001/admin

## Дополнительная информация

- [README.md](README.md) - Полная документация
- [INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md) - Подробное руководство
- [EXAMPLES.md](EXAMPLES.md) - Примеры использования
