from sqlalchemy.orm import Session
from typing import Dict, List, Set, Optional
import json
from pathlib import Path
from contextlib import contextmanager

from backend.db.schema import Task, User
from backend.models.task import TaskCreate, TaskRead, TaskList

class TaskService:
    # Class for database functionality
    def __init__(self, session: Session):
        self._db = session

    def admin_list_tasks(self) -> List[TaskRead] | List:
        return self._db.query(Task).all()

    def admin_get_task(self, task_id: int) -> TaskRead | None:
        return self._db.query(Task).filter(Task.id == task_id).first()

    def list_tasks(self, owner_id: int) -> List[TaskRead] | List:
        if owner_id:
            return self._db.query(Task).filter(Task.owner_id == owner_id).all()
        return []

    def get_task(self, owner_id: int, task_id: int) -> TaskRead | None:
        return self._db.query(Task).filter(Task.id == task_id, Task.owner_id == owner_id).first()

    def create_task(self, task_data: TaskCreate) -> TaskRead:
        try:
            # Pydantic model already handles validation and defaults
            # task = Task(**task_data.model_dump())
            task = Task(
                owner_id=task_data.owner_id,
                name=task_data.name,
                description=task_data.description,
                category=task_data.category,
                dueDate=task_data.dueDate,
                parameters=task_data.parameters,
                completed=task_data.completed,
                tags=task_data.tags,
                priority=task_data.priority
            )
            self._db.add(task)
            self._db.commit()
            self._db.refresh(task)
            return task
        except Exception as e:
            self._db.rollback()
            raise e

    def update_task(self, owner_id: int, task_id: int, task_data: Dict) -> TaskRead | None:
        try:
            task = self._db.query(Task).filter(Task.id == task_id, Task.owner_id == owner_id).first()
            if not task:
                return None
            
            # Update task fields
            for field, value in task_data.items():
                if hasattr(task, field):
                    setattr(task, field, value)
                        
            self._db.add(task)
            self._db.commit()
            self._db.refresh(task)
            return task
        except Exception as e:
            self._db.rollback()
            raise e

    def remove_task(self, owner_id: int, task_id: int) -> bool:
        task = self._db.query(Task).filter(Task.id == task_id, Task.owner_id == owner_id).first()
        if not task:
            return False
        self._db.delete(task)
        self._db.commit()
        return True

    def get_categories(self, owner_id: int) -> List[str]: #TODO: move to User_Service & change its implementation
        query = self._db.query(Task).filter(Task.owner_id == owner_id).distinct(Task.category).all()
        categories = set(task.category for task in query)
        return sorted(categories)
    
    def mark_task_complete(self, owner_id: int, task_id: int) -> bool:
        try:
            task = self._db.query(Task).filter(Task.id == task_id, Task.owner_id == owner_id).first()
            if not task:
                return False
            if getattr(task, 'completed', False):
                return True
            task.completed = True
            self._db.add(task)
            self._db.commit()
            self._db.refresh(task)
            return True
        except Exception as e:
            self._db.rollback()
            raise e


class TaskServiceJson:
    def __init__(self, filepath: str = 'tempStore.json'):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            self.filepath.write_text('[]')  # Initialize with empty list

    def admin_list_tasks(self) -> TaskList:
        tasks = json.loads(self.filepath.read_text())
        return TaskList(tasks=[TaskRead(**task) for task in tasks])

    def admin_get_task(self, task_id: int) -> TaskRead | None:
        tasks = json.loads(self.filepath.read_text())
        for task in tasks:
            if task['id'] == task_id:
                return TaskRead(**task)
        return None

    def list_tasks(self, owner_id: int) -> TaskList:
        if not owner_id:
            return TaskList(tasks=[])
        tasks = json.loads(self.filepath.read_text())
        user_tasks = [TaskRead(**task)
                      for task in tasks if task.get('owner_id') == owner_id]
        return TaskList(tasks=user_tasks)

    def get_task(self, owner_id: int, task_id: int) -> TaskRead | None:
        tasks = json.loads(self.filepath.read_text())
        for task in tasks:
            if task.get('id') == task_id and task.get('owner_id') == owner_id:
                return TaskRead(**task)
        return None

    def create_task(self, task_create: TaskCreate) -> TaskRead:
        tasks = json.loads(self.filepath.read_text())
        new_id = max((task.get('id', 0) for task in tasks), default=0) + 1
        task_data = task_create.model_dump()
        # Ensure required fields have defaults if None
        if task_data.get('description') is None:
            task_data['description'] = ''
        if task_data.get('parameters') is None:
            task_data['parameters'] = {}

        new_task = TaskRead(id=new_id, **task_data)
        tasks.append(new_task.model_dump())
        self.filepath.write_text(json.dumps(tasks, indent=4))
        return new_task

    def get_categories(self, owner_id: int) -> List[str]:
        tasks = json.loads(self.filepath.read_text())
        if owner_id:
            tasks = [t for t in tasks if t.get('owner_id') == owner_id]
        categories = set(t.get('category', 'General') for t in tasks)
        return list(categories)

    def remove_task(self, owner_id: int, task_id: int) -> bool:
        tasks = json.loads(self.filepath.read_text())
        def matches(rem_t: dict) -> bool:
            stored_id = rem_t.get('id') if rem_t.get('id') is not None else rem_t.get('task_id')
            return (stored_id == task_id) and (rem_t.get('owner_id') == owner_id)

        new_tasks = [t for t in tasks if not matches(t)]
        
        if len(new_tasks) == len(tasks):
            return False

        tmp_path = self.filepath.with_suffix(self.filepath.suffix + '.tmp')
        tmp_path.write_text(json.dumps(new_tasks, indent=4))
        tmp_path.replace(self.filepath)
        return True 