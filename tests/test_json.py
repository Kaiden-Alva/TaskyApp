# File: tests/test_json.py
'''
This module provides utility functions for reading from and writing to JSON files.
It will make the temp test json file and then delete it after the tests are done.
Use the flag keep_file=True to keep the file after tests are done.
'''
import json
import os
import pytest

from backend.services.user_service import UserServiceJson
from backend.services.task_service import TaskServiceJson
from backend.models.user import UserCreate, UserRead
from backend.models.task import TaskCreate, TaskRead, TaskList


class JSONHandler:
    def __init__(self, file_path: list[str] = ['test_users.json', 'test_tasks.json'], keep_file: bool = False):
        self.file_path: list[str] = file_path
        self.keep_file: bool = keep_file

        self.build_files()
        # Don't delete files immediately - wait for cleanup

    def build_files(self) -> None:
        for path in self.file_path:
            with open(path, 'w') as f:
                json.dump([], f)

    def delete_files(self) -> None:
        if not self.keep_file:
            for path in self.file_path:
                print(f"Deleting file: {path}")
                if os.path.exists(path):
                    os.remove(path)

    def save_test_output(self, output_file: str = 'test_output.json') -> None:
        """Save current state of test files to output file for review"""
        output_data = {}
        for path in self.file_path:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    output_data[path] = json.load(f)
            else:
                output_data[path] = "File not found"
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Test output saved to {output_file}")


@pytest.fixture
def json_handler(request):
    handler = JSONHandler(keep_file=True) # Keep files during test execution
    yield handler
    
    # Save test output after each test
    test_name = request.node.name
    print(f"\n=== {test_name} ===")
    
    # Capture current state
    output_data = {}
    for path in handler.file_path:
        if os.path.exists(path):
            with open(path, 'r') as f:
                output_data[path] = json.load(f)
        else:
            output_data[path] = "File not found"
    
    # Append to test output file
    output_file = 'test_output.json'
    all_outputs = {}
    
    # Load existing outputs if file exists
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            all_outputs = json.load(f)
    
    # Add current test output
    all_outputs[test_name] = output_data
    
    # Save updated outputs
    with open(output_file, 'w') as f:
        json.dump(all_outputs, f, indent=2)
    
    print(f"Test output saved for {test_name}")

@pytest.fixture(scope="session", autouse=True)
def test_session_cleanup():
    """Session-scoped fixture that runs cleanup after all tests"""
    yield  # Run all tests first
    
    # After all tests complete, clean up test files
    print("\n=== Test Session Complete ===")
    
    # Clean up test files (but keep test_output.json)
    test_files = ['test_users.json', 'test_tasks.json']
    for path in test_files:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted {path}")
    print("Test files cleaned up. Check test_output.json for results.")


@pytest.fixture
def user_fixture(json_handler):
    """Fixture that creates a test user"""
    userService = UserServiceJson(json_handler.file_path[0])
    user: UserRead = userService.create_user(UserCreate(username="TestUser", password="testpass"))
    return user


@pytest.fixture
def task_fixture(json_handler, user_fixture):
    """Fixture that creates a test task"""
    taskService = TaskServiceJson(json_handler.file_path[1])
    task: TaskRead = taskService.create_task(
        TaskCreate(name="Test Task Fixture", owner_id=user_fixture.id))
    return task


def test_json_create_user(json_handler):
    """Test creating a user with JSON storage"""
    userService = UserServiceJson(json_handler.file_path[0])
    user: UserRead = userService.create_user(UserCreate(username="JohnDoe", password="secret123"))
    assert isinstance(user, UserRead)
    assert user.username == "JohnDoe"
    assert user.id is not None
    assert "password" not in user.model_dump()  # Ensure password is not returned


def test_json_create_task(json_handler, user_fixture):
    """Test creating a task with JSON storage"""
    taskService = TaskServiceJson(json_handler.file_path[1])
    task: TaskRead = taskService.create_task(
        TaskCreate(name="Test Task", owner_id=user_fixture.id))
    assert isinstance(task, TaskRead)
    assert task.name == "Test Task"
    assert task.id is not None
    assert task.owner_id == user_fixture.id

def test_json_list_tasks(json_handler, user_fixture, task_fixture):
    taskService = TaskServiceJson(json_handler.file_path[1])
    tasks: TaskList = taskService.list_tasks(user_fixture.id)
    print(tasks)
    assert isinstance(tasks, TaskList)
    assert len(tasks.tasks) > 0
    assert tasks.tasks[0].owner_id == user_fixture.id

def test_json_remove_task(json_handler, user_fixture):
    taskService = TaskServiceJson(json_handler.file_path[1])
    task: TaskRead = taskService.create_task(
        TaskCreate(name="Task to remove", owner_id=user_fixture.id)
    )
    assert isinstance(task, TaskRead)
    task_id = task.id

    fetched = taskService.get_task(user_fixture.id, task_id)
    assert fetched is not None
    all_tasks = taskService.list_tasks(user_fixture.id)
    assert any(t.id == task_id for t in all_tasks.tasks)

    # Remove the task
    removed = taskService.remove_task(user_fixture.id, task_id)
    assert removed is True

    # Now get_task should return None and list_tasks should not include it
    fetched_after = taskService.get_task(user_fixture.id, task_id)
    assert fetched_after is None
    all_tasks_after = taskService.list_tasks(user_fixture.id)
    assert not any(t.id == task_id for t in all_tasks_after.tasks)

    # Removing again should return False (task already gone)
    removed_again = taskService.remove_task(user_fixture.id, task_id)
    assert removed_again is False

