import os
import pytest

from main import Database, Task, TaskManager


@pytest.fixture
def manager():
    db = Database(":memory:")
    tm = TaskManager(db)
    yield tm
    db.close()


def test_add_task_success(manager):
    task_id = manager.add_task("Buy milk", "From the shop")
    task = manager.get_task_by_id(task_id)

    assert task is not None
    assert task.title == "Buy milk"
    assert task.description == "From the shop"
    assert task.status == Task.STATUS_PENDING


def test_add_task_strips_whitespace(manager):
    task_id = manager.add_task("  Buy milk  ", "  desc  ")
    task = manager.get_task_by_id(task_id)

    assert task.title == "Buy milk"
    assert task.description == "desc"


@pytest.mark.parametrize("bad_title", ["", "   ", None])
def test_add_task_rejects_empty_title(manager, bad_title):
    with pytest.raises(ValueError):
        manager.add_task(bad_title)


def test_get_all_tasks_returns_all(manager):
    manager.add_task("Task 1")
    manager.add_task("Task 2")

    tasks = manager.get_all_tasks()
    assert len(tasks) == 2
    assert [t.title for t in tasks] == ["Task 1", "Task 2"]


def test_get_tasks_by_status(manager):
    id1 = manager.add_task("Task 1")
    manager.add_task("Task 2")
    manager.mark_as_done(id1)

    pending = manager.get_tasks_by_status(Task.STATUS_PENDING)
    done = manager.get_tasks_by_status(Task.STATUS_DONE)

    assert len(pending) == 1
    assert len(done) == 1
    assert pending[0].title == "Task 2"
    assert done[0].title == "Task 1"


def test_mark_as_done_success(manager):
    task_id = manager.add_task("Task 1")
    manager.mark_as_done(task_id)

    task = manager.get_task_by_id(task_id)
    assert task.is_done() is True


def test_mark_as_done_nonexistent_raises(manager):
    with pytest.raises(ValueError):
        manager.mark_as_done(999)


def test_delete_task_success(manager):
    task_id = manager.add_task("Task 1")
    manager.delete_task(task_id)

    assert manager.get_task_by_id(task_id) is None


def test_delete_task_nonexistent_raises(manager):
    with pytest.raises(ValueError):
        manager.delete_task(999)


def test_statistics(manager):
    id1 = manager.add_task("Task 1")
    manager.add_task("Task 2")
    manager.add_task("Task 3")
    manager.mark_as_done(id1)

    stats = manager.get_statistics()
    assert stats == {"total": 3, "done": 1, "pending": 2}


def test_statistics_empty(manager):
    stats = manager.get_statistics()
    assert stats == {"total": 0, "done": 0, "pending": 0}


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("report.csv", "report.csv"),
        ("report", "report.csv"),
        ("", "tasks_export.csv"),
        ("   ", "tasks_export.csv"),
        ("../../etc/passwd", "passwd.csv"),
        ("/etc/passwd", "passwd.csv"),
        ("weird name!.csv", "weird_name_.csv"),
    ],
)
def test_sanitize_export_filename(raw, expected):
    assert TaskManager.sanitize_export_filename(raw) == expected


def test_export_to_csv_creates_file_in_exports_dir(manager, tmp_path, monkeypatch):
    import main as main_module

    monkeypatch.setattr(main_module, "EXPORTS_DIR", str(tmp_path))

    manager.add_task("Task 1")
    manager.add_task("Task 2")

    count, full_path = manager.export_to_csv("../../evil.csv")

    assert count == 2
    assert os.path.dirname(full_path) == str(tmp_path)
    assert os.path.basename(full_path) == "evil.csv"
    assert os.path.isfile(full_path)


def test_task_is_done():
    pending = Task(1, "Title", "Desc", Task.STATUS_PENDING, "2026-01-01 10:00:00")
    done = Task(2, "Title", "Desc", Task.STATUS_DONE, "2026-01-01 10:00:00")

    assert pending.is_done() is False
    assert done.is_done() is True


def test_task_str_contains_title():
    task = Task(1, "Buy milk", "From shop", Task.STATUS_PENDING, "2026-01-01 10:00:00")
    assert "Buy milk" in str(task)
