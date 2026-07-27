import sqlite3
import csv
import os
import re
from datetime import datetime

# keep the db and exports next to the script, not wherever it's launched from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "todo.db")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")


class Database:
    def __init__(self, db_name=DEFAULT_DB_PATH):
        self.db_name = db_name
        self.connection = sqlite3.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
        """
        self.connection.execute(query)
        self.connection.commit()

    def execute(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def fetch_all(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def close(self):
        self.connection.close()


class Task:
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"

    def __init__(self, id, title, description, status, created_at):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def is_done(self):
        return self.status == self.STATUS_DONE

    def __str__(self):
        status_icon = "[x]" if self.is_done() else "[ ]"
        desc = self.description if self.description else "-"
        return f"{status_icon} #{self.id:<3} {self.title:<25} | {desc:<30} | created: {self.created_at}"


class TaskManager:
    def __init__(self, database: Database):
        self.db = database

    def add_task(self, title, description=""):
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty.")

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO tasks (title, description, status, created_at)
            VALUES (?, ?, ?, ?)
        """
        cursor = self.db.execute(
            query, (title.strip(), description.strip(), Task.STATUS_PENDING, created_at)
        )
        return cursor.lastrowid

    def get_all_tasks(self):
        rows = self.db.fetch_all("SELECT * FROM tasks ORDER BY id")
        return [Task.from_row(row) for row in rows]

    def get_tasks_by_status(self, status):
        rows = self.db.fetch_all(
            "SELECT * FROM tasks WHERE status = ? ORDER BY id", (status,)
        )
        return [Task.from_row(row) for row in rows]

    def get_task_by_id(self, task_id):
        row = self.db.fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return Task.from_row(row) if row else None

    def mark_as_done(self, task_id):
        task = self.get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Task with id {task_id} not found.")

        self.db.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (Task.STATUS_DONE, task_id),
        )

    def delete_task(self, task_id):
        task = self.get_task_by_id(task_id)
        if task is None:
            raise ValueError(f"Task with id {task_id} not found.")

        self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_statistics(self):
        all_tasks = self.get_all_tasks()
        total = len(all_tasks)
        done = len([t for t in all_tasks if t.is_done()])
        pending = total - done
        return {"total": total, "done": done, "pending": pending}

    @staticmethod
    def sanitize_export_filename(filename):
        # only keep the file name itself, no "../" tricks, force a .csv extension
        if not filename or not filename.strip():
            filename = "tasks_export.csv"

        filename = os.path.basename(filename.strip())
        filename = re.sub(r"[^A-Za-z0-9_.\-]", "_", filename)

        if not filename or filename in (".", ".."):
            filename = "tasks_export.csv"

        if not filename.lower().endswith(".csv"):
            filename += ".csv"

        return filename

    def export_to_csv(self, filename="tasks_export.csv"):
        safe_name = self.sanitize_export_filename(filename)
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        full_path = os.path.join(EXPORTS_DIR, safe_name)

        tasks = self.get_all_tasks()

        with open(full_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["id", "title", "description", "status", "created_at"])
            for task in tasks:
                writer.writerow(
                    [task.id, task.title, task.description, task.status, task.created_at]
                )

        return len(tasks), full_path


def print_header(title):
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)


def print_menu():
    print_header("TO-DO LIST MANAGER")
    print("1. Add a new task")
    print("2. View all tasks")
    print("3. View tasks by status")
    print("4. Mark a task as done")
    print("5. Delete a task")
    print("6. Show statistics")
    print("7. Export tasks to CSV")
    print("0. Exit")
    print("-" * 70)


def print_tasks_table(tasks):
    if not tasks:
        print("\nNo tasks to display.\n")
        return

    print(f"\n{'ID':<5}{'Status':<10}{'Title':<25}{'Description':<30}{'Created At':<20}")
    print("-" * 90)
    for task in tasks:
        status = "Done" if task.is_done() else "Pending"
        description = task.description if task.description else "-"
        print(
            f"{task.id:<5}{status:<10}{task.title[:23]:<25}{description[:28]:<30}{task.created_at:<20}"
        )
    print("-" * 90)


def input_int(prompt):
    value = input(prompt).strip()
    if not value.isdigit():
        raise ValueError("Please enter a valid positive number.")
    return int(value)


def input_yes_no(prompt):
    value = input(prompt).strip().lower()
    return value in ("y", "yes", "yep", "yeah")


def handle_add_task(manager: TaskManager):
    print_header("ADD NEW TASK")
    title = input("Enter task title: ").strip()
    description = input("Enter task description (optional): ").strip()

    try:
        task_id = manager.add_task(title, description)
        print(f"\nTask added successfully with ID {task_id}.")
    except ValueError as e:
        print(f"\nError: {e}")


def handle_view_all(manager: TaskManager):
    print_header("ALL TASKS")
    tasks = manager.get_all_tasks()
    print_tasks_table(tasks)


def handle_view_by_status(manager: TaskManager):
    print_header("VIEW TASKS BY STATUS")
    print("1. Pending tasks")
    print("2. Done tasks")
    choice = input("Choose an option: ").strip()

    if choice == "1":
        tasks = manager.get_tasks_by_status(Task.STATUS_PENDING)
        print_header("PENDING TASKS")
    elif choice == "2":
        tasks = manager.get_tasks_by_status(Task.STATUS_DONE)
        print_header("DONE TASKS")
    else:
        print("\nInvalid option.")
        return

    print_tasks_table(tasks)


def handle_mark_done(manager: TaskManager):
    print_header("MARK TASK AS DONE")
    try:
        task_id = input_int("Enter task ID: ")
        manager.mark_as_done(task_id)
        print(f"\nTask {task_id} marked as done.")
    except ValueError as e:
        print(f"\nError: {e}")


def handle_delete_task(manager: TaskManager):
    print_header("DELETE TASK")
    try:
        task_id = input_int("Enter task ID: ")
        if input_yes_no(f"Are you sure you want to delete task {task_id}? (y/n): "):
            manager.delete_task(task_id)
            print(f"\nTask {task_id} deleted.")
        else:
            print("\nDeletion cancelled.")
    except ValueError as e:
        print(f"\nError: {e}")


def handle_statistics(manager: TaskManager):
    print_header("STATISTICS")
    stats = manager.get_statistics()
    print(f"Total tasks:   {stats['total']}")
    print(f"Done tasks:    {stats['done']}")
    print(f"Pending tasks: {stats['pending']}")


def handle_export_csv(manager: TaskManager):
    print_header("EXPORT TASKS TO CSV")
    filename = input("Enter filename (default: tasks_export.csv): ").strip()

    try:
        count, full_path = manager.export_to_csv(filename)
        print(f"\nExported {count} task(s) to '{full_path}'.")
    except OSError as e:
        print(f"\nError writing file: {e}")


def main():
    db = Database()
    manager = TaskManager(db)

    actions = {
        "1": handle_add_task,
        "2": handle_view_all,
        "3": handle_view_by_status,
        "4": handle_mark_done,
        "5": handle_delete_task,
        "6": handle_statistics,
        "7": handle_export_csv,
    }

    try:
        while True:
            print_menu()
            choice = input("Choose an option (0-7): ").strip()

            if choice == "0":
                print("\nGoodbye!")
                break

            action = actions.get(choice)
            if action:
                try:
                    action(manager)
                except Exception as e:
                    print(f"\nUnexpected error: {e}")
            else:
                print("\nInvalid option. Please choose a number between 0 and 7.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
