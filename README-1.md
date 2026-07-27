# To-Do List (Python + SQLite3)

Консольний To-Do List на Python з SQLite3. Проєкт для портфоліо.

## Що вміє

- додавати завдання
- показувати всі завдання / тільки виконані / тільки невиконані
- позначати завдання виконаним
- видаляти завдання
- показувати статистику (всього / виконано / в очікуванні)
- експортувати завдання в CSV

## Структура

- `Database` — робота з SQLite3
- `Task` — одне завдання
- `TaskManager` — вся логіка (додати, видалити, позначити, статистика, експорт)
- решта — консольне меню

`todo.db` створюється автоматично поруч зі скриптом при першому запуску.

## Запуск

```bash
python3 main.py
```

Меню:

```
1. Add a new task
2. View all tasks
3. View tasks by status
4. Mark a task as done
5. Delete a task
6. Show statistics
7. Export tasks to CSV
0. Exit
```

## Тести

```bash
pip install pytest
pytest test_main.py -v
```

## Що можна додати далі

- редагування завдання
- дедлайни / пріоритети
- пошук
- веб-версія на Flask
