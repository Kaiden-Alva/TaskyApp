from fastapi.testclient import TestClient
import pytest
import re
from typing import Any, Dict, Optional

from backend.api.v1.task_api import get_task_service
from backend.main import app
from backend.services.task_service import TaskService
from backend.db.schema import Task, User
from backend.services.user_auth_service import get_current_active_user
from tests.test_db import TestingSessionLocal


client = TestClient(app)

# Cache the test user globally to avoid repeated DB lookups
_cached_test_user = None


def _override_get_task_service():
    session = TestingSessionLocal()
    yield TaskService(session=session)


def _override_get_current_active_user():
    """Override to return a test user without requiring authentication"""
    global _cached_test_user
    
    if _cached_test_user is not None:
        return _cached_test_user
    
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            user = User(username="testuser", email="test@example.com", hashed_password="test", full_name="Kaiden Alva")
            db.add(user)
            db.commit()
            db.refresh(user)
        _cached_test_user = user
        return user
    finally:
        db.close()


# Store original overrides to restore later if needed
_original_overrides = {}


@pytest.fixture(scope="module", autouse=True)
def setup_module_overrides():
    """Set up dependency overrides for this test module"""
    global _original_overrides
    # Save original overrides
    _original_overrides = dict(app.dependency_overrides)
    
    # Set our overrides
    app.dependency_overrides[get_task_service] = _override_get_task_service
    app.dependency_overrides[get_current_active_user] = _override_get_current_active_user
    
    yield
    
    # Restore original overrides after module tests complete
    app.dependency_overrides.clear()
    app.dependency_overrides.update(_original_overrides)

@pytest.fixture(autouse=True)
def clean_db():
    with TestingSessionLocal() as session:
        session.query(Task).delete()
        session.commit()


def _find_path(method: str, contains: str = "tasks", has_param: Optional[bool] = None) -> str:
    method = method.upper()
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        if not path or not methods:
            continue
        if method not in methods:
            continue
        if contains not in path:
            continue
        if has_param is True and "{" not in path:
            continue
        if has_param is False and "{" in path:
            continue
        return path
    raise RuntimeError(f"No route found for method={method} contains={contains} has_param={has_param}")


def _fill_path_with_id(path: str, id_value: Any) -> str:
    return re.sub(r"\{[^}]+\}", str(id_value), path)


def _extract_id_from_response(json_obj: Any) -> Any:
    if isinstance(json_obj, dict):
        for key in ("id", "task_id", "taskId", "taskID"):
            if key in json_obj:
                return json_obj[key]
        for v in json_obj.values():
            if isinstance(v, int):
                return v
    raise RuntimeError("Could not extract id from response JSON")


def _ensure_test_user():
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "test@example.com").first()
        if user:
            return user.id
        # create user record for tests
        user = User(username="testuser", email="test@example.com", hashed_password="test", full_name="Test Test")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()
    

def _create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "owner_id" not in payload:
        payload = dict(payload)  # avoid changing caller object
        payload["owner_id"] = _ensure_test_user()

    create_path = _find_path("POST", "tasks", has_param=False)
    res = client.post(create_path, json=payload)
    assert res.status_code in (200, 201), f"create failed: {res.status_code} {res.text}"
    return res.json()


def test_get_tasks_listing():
    t1 = _create_task({"name": "Test Task A", "description": "a", "dueDate": "2100-01-01T00:00:00Z"})
    t2 = _create_task({"name": "Test Task B", "description": "b", "dueDate": "2100-02-01T00:00:00Z"})

    list_path = _find_path("GET", "tasks", has_param=False)
    res = client.get(list_path)
    assert res.status_code == 200, f"list failed: {res.status_code} {res.text}"
    data = res.json()
    assert isinstance(data, (list, dict)), "unexpected list response shape"

    items = data if isinstance(data, list) else data.get("items", data.get("tasks", []))
    assert any(
        (item.get("name") == "Test Task A" or item.get("title") == "Test Task A") for item in items
    ), "created task A not found in listing"
    assert any(
        (item.get("name") == "Test Task B" or item.get("title") == "Test Task B") for item in items
    ), "created task B not found in listing"


def test_mark_task_complete():
    created = _create_task({"name": "Complete Me", "description": "", "dueDate": "2100-03-01T00:00:00Z"})
    task_id = _extract_id_from_response(created)

    try:
        complete_path = _find_path("POST", "complete", has_param=True)
    except RuntimeError:
        param_path = _find_path("POST", "tasks", has_param=True)
        complete_path = param_path.rstrip("/") + "/complete"

    complete_path_filled = _fill_path_with_id(complete_path, task_id)

    res = client.post(complete_path_filled)
    if res.status_code == 405:
        res = client.patch(complete_path_filled)
    assert res.status_code in (200, 204), f"mark complete failed: {res.status_code} {res.text}"

    param_get = _find_path("GET", "tasks", has_param=True)
    get_path = _fill_path_with_id(param_get, task_id)
    res2 = client.get(get_path)
    assert res2.status_code == 200, f"get task failed: {res2.status_code} {res2.text}"
    payload = res2.json()

    completed = payload.get("completed", payload.get("is_complete", payload.get("done")))
    assert completed in (True, 1), "task not marked complete"


def test_update_task():
    created = _create_task({"name": "Updatable Task", "description": "old", "dueDate": "2100-04-01T00:00:00Z"})
    task_id = _extract_id_from_response(created)

    # make sure that Patch, put, and post methods are considered
    try:
        param_update = _find_path("PATCH", "tasks", has_param=True)
        method_attempts = ("patch", "put", "post")
    except RuntimeError:
        try:
            param_update = _find_path("PUT", "tasks", has_param=True)
            method_attempts = ("put", "patch", "post")
        except RuntimeError:
            param_update = _find_path("POST", "tasks", has_param=True)
            method_attempts = ("post", "patch", "put")

    update_path = _fill_path_with_id(param_update, task_id)

    # try patch first, then try put or post
    res = None
    for m in method_attempts:
        if m == "patch":
            res = client.patch(update_path, json={"name": "Updated Task", "description": "new"})
        elif m == "put":
            res = client.put(update_path, json={"name": "Updated Task", "description": "new"})
        else:
            res = client.post(update_path, json={"name": "Updated Task", "description": "new"})
        if res.status_code not in (405, 404):
            break

    assert res is not None and res.status_code in (200, 204), f"update failed: {res.status_code} {res.text}"

    param_get = _find_path("GET", "tasks", has_param=True)
    get_path = _fill_path_with_id(param_get, task_id)
    res2 = client.get(get_path)
    assert res2.status_code == 200, f"get after update failed: {res2.status_code} {res2.text}"
    payload = res2.json()
    assert payload.get("name") == "Updated Task" or payload.get("title") == "Updated Task"


def test_remove_task():
    created = _create_task({"name": "Delete Me", "description": "tmp", "dueDate": "2100-05-01T00:00:00Z"})
    task_id = _extract_id_from_response(created)

    param_delete = _find_path("DELETE", "tasks", has_param=True)
    delete_path = _fill_path_with_id(param_delete, task_id)
    res = client.delete(delete_path)
    assert res.status_code in (200, 204), f"delete failed: {res.status_code} {res.text}"

    param_get = _find_path("GET", "tasks", has_param=True)
    get_path = _fill_path_with_id(param_get, task_id)
    res2 = client.get(get_path)
    assert res2.status_code in (404, 410), "deleted task still retrievable"


def test_admin_list_tasks():
    ta1 = _create_task({"name": "Test Task A", "description": "a", "dueDate": "2100-01-01T00:00:00Z"})
    ta2 = _create_task({"name": "Test Task B", "description": "b", "dueDate": "2100-02-01T00:00:00Z"})

    with TestingSessionLocal() as session:
        count = session.query(Task).count()
        assert count == 2
    
def test_admin_get_task():
    created = _create_task({"name": "Admin Get Me", "description": "admin", "dueDate": "2100-06-01T00:00:00Z"})
    task_id = _extract_id_from_response(created)

    with TestingSessionLocal() as session:
        service = TaskService(session=session)
        task = service.admin_get_task(task_id)
        assert task is not None, "admin_get_task returned None"
        assert task.id == task_id, "admin_get_task returned wrong task"
        assert task.name == "Admin Get Me"

def test_list_tasks():
    with TestingSessionLocal() as session:
        session.query(Task).delete()
        session.commit()

        service = TaskService(session=session)

        owner_id = 123
        task1 = Task(
            name="Task One",
            description="desc1",
            owner_id=owner_id,
            category="work",
            parameters="{}",   
        )
        task2 = Task(
            name="Task Two",
            description="desc2",
            owner_id=owner_id,
            category="personal",
            parameters="{}",
        )

        session.add_all([task1, task2])
        session.commit()

        tasks = service.list_tasks(owner_id)
        assert len(tasks) == 2, f"Expected 2 tasks, got {len(tasks)}"
        names = {task.name for task in tasks}
        assert "Task One" in names and "Task Two" in names

def test_get_task():
    with TestingSessionLocal() as session:
        session.query(Task).delete()
        session.commit()

        service = TaskService(session=session)

        owner_id = 456
        task = Task(
            name="Unique Task",
            description="unique desc",
            owner_id=owner_id,
            category="work",
            parameters="{}",
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        fetched_task = service.get_task(owner_id, task.id)
        assert fetched_task is not None, "get_task returned None"
        assert fetched_task.id == task.id, "get_task returned wrong task"
        assert fetched_task.name == "Unique Task"

    
