from fastapi.testclient import TestClient
from datetime import datetime
import pytest

from backend.api.v1.task_api import get_task_service
from backend.api.v1.user import get_user_service, get_userAuth_service
from backend.main import app
from backend.services.task_service import TaskService
from backend.services.user_service import UserService
from backend.services.user_auth_service import userAuthService, get_current_active_user
from backend.models.user import UserRead
from tests.test_db import TestingSessionLocal

# Setup the TestClient
client = TestClient(app)

# Test user for authentication - use a dict to store per-session data
_test_user_data = {"current_user": None, "counter": 0}


def override_get_task_service():
    session = TestingSessionLocal()
    yield TaskService(session=session)


def override_get_user_service():
    session = TestingSessionLocal()
    yield UserService(session=session)


def override_get_userAuth_service():
    session = TestingSessionLocal()
    yield userAuthService(session=session)


def override_get_current_active_user():
    """Mock the current user for tests"""
    if _test_user_data["current_user"] is None:
        raise Exception("Test user not initialized")
    return _test_user_data["current_user"]


# Store original overrides to restore later if needed
_original_overrides = {}


@pytest.fixture(scope="module", autouse=True)
def setup_module_overrides():
    """Set up dependency overrides for this test module"""
    global _original_overrides
    # Save original overrides
    _original_overrides = dict(app.dependency_overrides)
    
    # Set our overrides
    app.dependency_overrides[get_task_service] = override_get_task_service
    app.dependency_overrides[get_user_service] = override_get_user_service
    app.dependency_overrides[get_userAuth_service] = override_get_userAuth_service
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    yield
    
    # Restore original overrides after module tests complete
    app.dependency_overrides.clear()
    app.dependency_overrides.update(_original_overrides)


@pytest.fixture(autouse=True)
def reset_test_user():
    """Reset the test user before each test to avoid cross-test contamination"""
    _test_user_data["current_user"] = None
    yield
    # Cleanup after test if needed


def setup_test_user():
    """Create a test user and set it globally for authentication"""
    _test_user_data["counter"] += 1
    # Create a new user with unique username for each test
    response = client.post("/api/v1/register/", json={
        "username": f"taskuser{_test_user_data['counter']}",
        "email": f"taskuser{_test_user_data['counter']}@example.com",
        "password": "taskPass123",
        "full_name": f"Task User {_test_user_data['counter']}"
    })
    assert response.status_code == 200, f"Failed to create user: {response.json()}"
    user_data = response.json()
    user = UserRead(**user_data)
    _test_user_data["current_user"] = user
    return user


def test_create_task():
    """Test creating a new task"""
    user = setup_test_user()
    
    task_data = {
        "owner_id": user.id,
        "name": "Test Task",
        "description": "This is a test task",
        "category": "Work",
        "parameters": {"key": "value"},
        "completed": False,
        "tags": ["urgent", "important"],
        "priority": 2
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 201
    created_task = response.json()
    
    assert created_task["name"] == "Test Task"
    assert created_task["description"] == "This is a test task"
    assert created_task["category"] == "Work"
    assert created_task["owner_id"] == user.id
    assert created_task["completed"] is False
    assert created_task["tags"] == ["urgent", "important"]
    assert created_task["priority"] == 2
    assert "id" in created_task


def test_create_task_with_defaults():
    """Test creating a task with minimal data (using defaults)"""
    user = setup_test_user()
    
    task_data = {
        "owner_id": user.id,
        "name": "Minimal Task"
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 201
    created_task = response.json()
    
    assert created_task["name"] == "Minimal Task"
    assert created_task["description"] == ""
    assert created_task["category"] == "General"
    assert created_task["completed"] is False
    assert created_task["priority"] == 0


def test_get_task():
    """Test retrieving a specific task"""
    user = setup_test_user()
    
    # First create a task
    task_data = {
        "owner_id": user.id,
        "name": "Task to Retrieve",
        "description": "Retrieve me",
        "category": "Personal"
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    assert create_response.status_code == 201
    created_task = create_response.json()
    
    # Now retrieve it
    get_response = client.get(f"/api/v1/tasks/{created_task['id']}")
    assert get_response.status_code == 200
    fetched_task = get_response.json()
    
    assert fetched_task["id"] == created_task["id"]
    assert fetched_task["name"] == "Task to Retrieve"
    assert fetched_task["description"] == "Retrieve me"


def test_get_nonexistent_task():
    """Test retrieving a task that doesn't exist"""
    setup_test_user()
    
    response = client.get("/api/v1/tasks/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_tasks():
    """Test listing all tasks for a user"""
    user = setup_test_user()
    
    # Create multiple tasks
    tasks_to_create = [
        {"owner_id": user.id, "name": "Task 1", "category": "Work"},
        {"owner_id": user.id, "name": "Task 2", "category": "Personal"},
        {"owner_id": user.id, "name": "Task 3", "category": "Work"}
    ]
    
    for task in tasks_to_create:
        response = client.post("/api/v1/tasks", json=task)
        assert response.status_code == 201
    
    # List all tasks
    list_response = client.get("/api/v1/tasks")
    assert list_response.status_code == 200
    tasks = list_response.json()
    
    assert len(tasks) >= 3
    task_names = [t["name"] for t in tasks]
    assert "Task 1" in task_names
    assert "Task 2" in task_names
    assert "Task 3" in task_names


def test_update_task():
    """Test updating a task"""
    user = setup_test_user()
    
    # Create a task
    task_data = {
        "owner_id": user.id,
        "name": "Original Task",
        "description": "Original description",
        "category": "Work",
        "priority": 1
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    assert create_response.status_code == 201
    created_task = create_response.json()
    
    # Update the task
    update_data = {
        "name": "Updated Task",
        "description": "Updated description",
        "category": "Personal",
        "priority": 3
    }
    update_response = client.put(f"/api/v1/tasks/{created_task['id']}", json=update_data)
    assert update_response.status_code == 200
    updated_task = update_response.json()
    
    assert updated_task["name"] == "Updated Task"
    assert updated_task["description"] == "Updated description"
    assert updated_task["category"] == "Personal"
    assert updated_task["priority"] == 3
    assert updated_task["id"] == created_task["id"]


def test_update_task_partial():
    """Test partially updating a task (only some fields)"""
    user = setup_test_user()
    
    # Create a task
    task_data = {
        "owner_id": user.id,
        "name": "Task for Partial Update",
        "description": "Original description",
        "category": "Work"
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    created_task = create_response.json()
    
    # Update only the name
    update_data = {"name": "Partially Updated Task"}
    update_response = client.put(f"/api/v1/tasks/{created_task['id']}", json=update_data)
    assert update_response.status_code == 200
    updated_task = update_response.json()
    
    assert updated_task["name"] == "Partially Updated Task"
    assert updated_task["description"] == "Original description"
    assert updated_task["category"] == "Work"


def test_update_task_with_tags():
    """Test updating task tags"""
    user = setup_test_user()
    
    # Create a task with tags
    task_data = {
        "owner_id": user.id,
        "name": "Task with Tags",
        "tags": ["tag1", "tag2"]
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    created_task = create_response.json()
    
    # Update tags
    update_data = {"tags": ["newtag1", "newtag2", "newtag3"]}
    update_response = client.put(f"/api/v1/tasks/{created_task['id']}", json=update_data)
    assert update_response.status_code == 200
    updated_task = update_response.json()
    
    assert updated_task["tags"] == ["newtag1", "newtag2", "newtag3"]


def test_mark_task_complete():
    """Test marking a task as complete"""
    user = setup_test_user()
    
    # Create a task
    task_data = {
        "owner_id": user.id,
        "name": "Task to Complete",
        "completed": False
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    created_task = create_response.json()
    assert created_task["completed"] is False
    
    # Mark as complete
    complete_response = client.post(f"/api/v1/tasks/{created_task['id']}/complete")
    assert complete_response.status_code == 200
    completed_task = complete_response.json()
    
    assert completed_task["completed"] is True
    assert completed_task["id"] == created_task["id"]


def test_delete_task():
    """Test deleting a task"""
    user = setup_test_user()
    
    # Create a task
    task_data = {
        "owner_id": user.id,
        "name": "Task to Delete"
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    created_task = create_response.json()
    
    # Delete the task
    delete_response = client.delete(f"/api/v1/tasks/{created_task['id']}")
    assert delete_response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(f"/api/v1/tasks/{created_task['id']}")
    assert get_response.status_code == 404


def test_delete_nonexistent_task():
    """Test deleting a task that doesn't exist"""
    setup_test_user()
    
    response = client.delete("/api/v1/tasks/99999")
    assert response.status_code == 404


def test_get_categories():
    """Test getting unique categories for a user"""
    user = setup_test_user()
    
    # Create tasks with different categories
    categories = ["Work", "Personal", "Work", "Shopping", "Personal"]
    for i, category in enumerate(categories):
        task_data = {
            "owner_id": user.id,
            "name": f"Task {i}",
            "category": category
        }
        client.post("/api/v1/tasks", json=task_data)
    
    # Get categories
    response = client.get("/api/v1/tasks/categories")
    assert response.status_code == 200
    returned_categories = response.json()
    
    # Should have unique categories only
    assert "Work" in returned_categories
    assert "Personal" in returned_categories
    assert "Shopping" in returned_categories
    assert len(returned_categories) == 3


def test_create_task_with_due_date():
    """Test creating a task with a due date"""
    user = setup_test_user()
    
    due_date = "2025-12-31T23:59:59"
    task_data = {
        "owner_id": user.id,
        "name": "Task with Due Date",
        "dueDate": due_date
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 201
    created_task = response.json()
    
    assert created_task["dueDate"] is not None
    assert due_date in created_task["dueDate"]


def test_create_task_with_parameters():
    """Test creating a task with custom parameters"""
    user = setup_test_user()
    
    task_data = {
        "owner_id": user.id,
        "name": "Task with Parameters",
        "parameters": {
            "location": "Office",
            "duration": 60,
            "attendees": ["Alice", "Bob"]
        }
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 201
    created_task = response.json()
    
    assert created_task["parameters"]["location"] == "Office"
    assert created_task["parameters"]["duration"] == 60
    assert created_task["parameters"]["attendees"] == ["Alice", "Bob"]


def test_update_task_completed_status():
    """Test updating task completion status via update endpoint"""
    user = setup_test_user()
    
    # Create a task
    task_data = {
        "owner_id": user.id,
        "name": "Task Status Test",
        "completed": False
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    created_task = create_response.json()
    
    # Update completed status
    update_data = {"completed": True}
    update_response = client.put(f"/api/v1/tasks/{created_task['id']}", json=update_data)
    assert update_response.status_code == 200
    updated_task = update_response.json()
    
    assert updated_task["completed"] is True


def test_task_priority_validation():
    """Test creating tasks with different priority levels"""
    user = setup_test_user()
    
    # Test valid priorities (0-3)
    for priority in [0, 1, 2, 3]:
        task_data = {
            "owner_id": user.id,
            "name": f"Priority {priority} Task",
            "priority": priority
        }
        response = client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 201
        assert response.json()["priority"] == priority

