'''
This is the orchestrator file for the backend that will run the correct functions based on the user's input.
'''
from sqlalchemy.orm import Session
from typing import Optional, Any, Dict, List, Set
import random
import json

from backend.models.user import UserCreate, UserRead
from backend.models.task import TaskCreate, TaskRead, TaskList
from backend.models.app_models import Command
from backend.services.user_service import UserService, UserServiceJson
from backend.services.task_service import TaskService, TaskServiceJson

class Orchestrator:
    '''
    This class will run the correct functions based on the user's input.
    '''

    def __init__(self, db_session: Optional[Session] = None, config=None):
        if config is None:
            from backend.core.config import Config
            config = Config()
        self._config = config

        # Initialize services
        if self._config.use_db and db_session:
            self.user_service = UserService(db_session)
            self.task_service = TaskService(db_session)
        else:
            self.user_service = UserServiceJson('tempUsers.json')
            self.task_service = TaskServiceJson('tempStore.json')

    def login(self, name: str) -> UserRead:
        '''This function will look up the user in the database and return the users object (information).
        If the user does not exist, it will create a new user and return the new user's object.'''
        user = self.user_service.get_user_by_username(name)
        if user:
            return user
        return self.user_service.create_user(UserCreate(name=name))

    def create_task(self, task_data: TaskCreate) -> TaskRead:
        '''
        This function will create a new task.

        Args:
            task_data: TaskCreate
                - owner_id (int): The user's ID
                - name (str): Task name
                - description (str): Task description
                - category (str, optional): Task category, defaults to 'General'
                - parameters (dict, optional): Additional parameters

        Returns:
            Task: The created task object
        '''
        return self.task_service.create_task(task_data)

    def get_tasks(self, owner_id: int) -> TaskList:
        '''
        This function retrieves tasks for a specific user.

        Args:
            args: Dictionary containing:
                - owner_id (int): The user's ID to filter tasks

        Returns:
            List of task dictionaries for the specified user
        '''
        return self.task_service.list_tasks(owner_id)

    def get_task(self, owner_id: int, task_id: int) -> TaskRead | None:
        return self.task_service.get_task(owner_id, task_id)

    def get_existing_categories(self, owner_id: int) -> List[str]:
        return self.task_service.get_categories(owner_id)

    def remove_task(self, owner_id: int, task_id: int) -> bool:
        return self.task_service.remove_task(owner_id, task_id)
