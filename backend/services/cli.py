'''
This file holds the functions for CLI commands.
'''
from backend.models.task import TaskCreate
from backend.models.user import User
from backend.services.orchestrator import Orchestrator


class CLI:
    '''
    This class handels the CLI user input commands.
    '''

    # CLI Inputs
    addTaskKey = '1'
    removeTaskKey = '2'
    addCategoryKey = '3'
    removeCategoryKey = '4'
    escapeKey = 'e'

    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self.user: User | None = None

    def run_console_cycle(self):
        '''
        this function will prompt the user for input & call cli funcitons 
        '''

        # user login ---------
        name = input("Enter your name: ")
        self.user = self.orchestrator.login(name)
        print(f"Welcome, {self.user.name}!")

        consoleInput = ''
        while consoleInput != CLI.escapeKey:

            # display todo list
            taskList = self.orchestrator.get_tasks(owner_id=self.user.id)
            self._display_todo_list(taskList.tasks)
            # display user options (ex. add task (1))
            self._display_input_options()

            # get user input
            consoleInput = input("Enter your choice: ")

            # handle user input
            if consoleInput == CLI.addTaskKey:
                self._prompt_add_task()
            elif consoleInput == CLI.removeTaskKey:
                self._prompt_remove_task()
            elif consoleInput == CLI.addCategoryKey:
                pass
            elif consoleInput == CLI.removeCategoryKey:
                pass
            else:
                print("Invalid input, please try again.")
                continue

    def _prompt_add_task(self):
        '''
        This function adds a task to the task list.
        '''
        name = input("Enter task name: ")
        description = input("Enter task description: ")
        parameters = {}

        category = self._prompt_choose_category()

        # input validation
        task_data = TaskCreate(
            owner_id=self.user.id,
            name=name,
            description=description,
            category=category,
            parameters=parameters
        )

        created_task = self.orchestrator.create_task(task_data)
        print(f"Task '{created_task.name}' added successfully!")

    def _prompt_choose_category(self) -> str:
        '''
        this function adds new categories
        '''
        # show users categories
        categories = self.orchestrator.get_existing_categories(
            owner_id=self.user.id)

        if categories:
            print("\nExisting categories:")
            for category in categories:
                print(f"  - {category}")

        category = input("\nCreate or enter in a category: ")
        return category or 'General'

    def _display_input_options(self):
        '''
        this function displays the user options
        '''

        print("Input options:")
        print(f"'{CLI.addTaskKey}'. Add task")
        print(f"'{CLI.removeTaskKey}'. Remove task")
        print(f"'{CLI.addCategoryKey}'. Add category")
        print(f"'{CLI.removeCategoryKey}'. Remove category")
        print(f"Press '{CLI.escapeKey}' to exit.")

    def _display_todo_list(self, tasks):
        '''
        this function displays the todo list
        '''
        print(f"{self.user.name}'s Todo List:")
        print("-------------------------------------------------------")
        print("All Tasks: \n")

        # display tasks under their categories instead of listing categories per task

        # temporary display function
        currentTask = dict()
        for i in range(len(tasks)):
            currentTask = tasks[i]
            print(f"Task: {currentTask.name} \nDescription: {currentTask.description} \nCategory: {currentTask.category}\n")

        '''
        Current Display ************** (this is what the display currently looks like)
        
        Name's Todo List:
        -------------------------------------------------------
        All Tasks: 
        
        Task: 
        Description: 
        Category: 
        
        Task: 
        Description: 
        Category:

        etc..


        
        Display Goal *************************** (this is what we want the display to look like)

        Name's Todo List:
        -------------------------------------------------------
        All Tasks: 

        Category 1
        Task: 
        Description:

        Task: 
        Description:

        Category 2
        Task: 
        Description:

        Task: 
        Description:
        '''

        ''' Task dictionary key value format
        "task_id": 4252,
        "owner_id": 1,
        "name": "task02",
        "description": "does my id save?",
        "parameters": {}
        "categories": "school"
        '''
    
    def _prompt_remove_task(self):
        """
        Prompt user to remove a task by id. Shows user's tasks and asks for id.
        """
        tasks = self.orchestrator.get_tasks(owner_id=self.user.id).tasks
        if not tasks:
            print("You have no tasks to remove.")
            return
        
        print("\nYour tasks:")
        for i, t in enumerate(tasks, start=1):
            # TaskRead fields: id, name, description, category
            print(f"{i}) id={t.id} | {t.name} -- {t.description or ''} (Category: {t.category})")

        # Ask the user for the task id to delete (prefer id)
        raw = input("\nEnter the id of the task to remove (or press Enter to cancel): ").strip()
        if not raw:
            print("Canceling.")
            return

        # Validate
        try:
            task_id = int(raw)
        except ValueError:
            print("Invalid id. Please enter a numeric task id.")
            return

        # Call orchestrator's remove method if it exists, otherwise call task_service directly
        if hasattr(self.orchestrator, 'remove_task'):
            success = self.orchestrator.remove_task(owner_id=self.user.id, task_id=task_id)
        else:
            # Fallback: call task_service directly (works if orchestrator exposes task_service)
            success = self.orchestrator.task_service.remove_task(self.user.id, task_id)

        if success:
            print(f"Task {task_id} removed successfully.")
        else:
            print(f"Task {task_id} not found or you don't have permission to remove it.")
