"""
Locust load testing file for SmartTaskManager API
Tests authentication, task CRUD operations, and user endpoints
with a ramp-up strategy that starts small and grows over time.
"""
import random
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events, LoadTestShape


class TaskManagerUser(HttpUser):
    """
    Simulates a user interacting with the TaskManager API.
    Users authenticate, create tasks, view tasks, update tasks, and delete tasks.
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts - authenticate and get user info"""
        self.token = None
        self.user_id = None
        self.username = None
        self.created_task_ids = []
        
        # Try to login with a test user, or register a new one
        self.authenticate()
    
    def authenticate(self):
        """Authenticate user - try login first, then register if needed"""
        # Generate a unique username for this user
        self.username = f"loadtest_user_{random.randint(1000, 9999)}_{random.randint(1000, 9999)}"
        password = "testpassword123"
        email = f"{self.username}@loadtest.com"
        
        # Try to register first (idempotent - will fail if user exists, but that's ok)
        register_data = {
            "username": self.username,
            "email": email,
            "password": password,
            "full_name": f"Load Test User {self.username}"
        }
        
        with self.client.post(
            "/api/v1/register",
            json=register_data,
            catch_response=True,
            name="Register User"
        ) as response:
            if response.status_code in [200, 201, 400]:  # 400 means user already exists
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")
        
        # Now login
        login_data = {
            "username": self.username,
            "password": password
        }
        
        with self.client.post(
            "/api/v1/token",
            data=login_data,  # OAuth2PasswordRequestForm expects form data
            catch_response=True,
            name="Login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    response.success()
                    # Get user info to extract user_id
                    self.get_current_user()
                else:
                    response.failure("No token in response")
            else:
                response.failure(f"Login failed: {response.status_code}")
    
    def get_current_user(self):
        """Get current user information"""
        if not self.token:
            return
        
        with self.client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="Get Current User"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("id")
                response.success()
            else:
                response.failure(f"Failed to get user: {response.status_code}")
    
    def get_headers(self):
        """Get headers with authentication token"""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def get_tasks(self):
        """Get all tasks for the user - most common operation"""
        with self.client.get(
            "/api/v1/tasks",
            headers=self.get_headers(),
            catch_response=True,
            name="Get All Tasks"
        ) as response:
            if response.status_code == 200:
                tasks = response.json()
                # Store task IDs for later operations
                if tasks and len(self.created_task_ids) < 10:
                    for task in tasks[:5]:  # Store up to 5 task IDs
                        task_id = task.get("id")
                        if task_id and task_id not in self.created_task_ids:
                            self.created_task_ids.append(task_id)
                response.success()
            elif response.status_code == 401:
                # Token expired, re-authenticate
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to get tasks: {response.status_code}")
    
    @task(5)
    def create_task(self):
        """Create a new task"""
        if not self.user_id:
            return
        
        # Generate random task data
        task_names = [
            "Complete project documentation",
            "Review code changes",
            "Update dependencies",
            "Write unit tests",
            "Fix bug in authentication",
            "Optimize database queries",
            "Deploy to staging",
            "Update API documentation",
            "Refactor service layer",
            "Add error handling"
        ]
        
        categories = ["Work", "Personal", "Urgent", "General", "Development"]
        priorities = [0, 1, 2, 3]
        
        # Random due date (0-30 days from now)
        due_date = datetime.now() + timedelta(days=random.randint(0, 30))
        
        task_data = {
            "owner_id": self.user_id,
            "name": random.choice(task_names),
            "description": f"Task description for load testing - {random.randint(1, 1000)}",
            "category": random.choice(categories),
            "dueDate": due_date.isoformat(),
            "priority": random.choice(priorities),
            "tags": random.sample(["urgent", "important", "review", "bug", "feature"], k=random.randint(0, 3)),
            "completed": False
        }
        
        with self.client.post(
            "/api/v1/tasks",
            json=task_data,
            headers=self.get_headers(),
            catch_response=True,
            name="Create Task"
        ) as response:
            if response.status_code in [200, 201]:
                data = response.json()
                task_id = data.get("id")
                if task_id:
                    self.created_task_ids.append(task_id)
                    # Keep only last 10 task IDs
                    if len(self.created_task_ids) > 10:
                        self.created_task_ids.pop(0)
                response.success()
            elif response.status_code == 401:
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to create task: {response.status_code}")
    
    @task(3)
    def get_task_by_id(self):
        """Get a specific task by ID"""
        if not self.created_task_ids:
            return
        
        task_id = random.choice(self.created_task_ids)
        
        with self.client.get(
            f"/api/v1/tasks/{task_id}",
            headers=self.get_headers(),
            catch_response=True,
            name="Get Task By ID"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Task might have been deleted, remove from list
                if task_id in self.created_task_ids:
                    self.created_task_ids.remove(task_id)
                response.success()  # Not a failure for load testing
            elif response.status_code == 401:
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to get task: {response.status_code}")
    
    @task(2)
    def update_task(self):
        """Update an existing task"""
        if not self.created_task_ids:
            return
        
        task_id = random.choice(self.created_task_ids)
        
        update_data = {
            "name": f"Updated task {random.randint(1, 1000)}",
            "description": f"Updated description - {datetime.now().isoformat()}",
            "priority": random.randint(0, 3)
        }
        
        # Randomly complete the task
        if random.random() < 0.3:  # 30% chance
            update_data["completed"] = True
        
        with self.client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=self.get_headers(),
            catch_response=True,
            name="Update Task"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                if task_id in self.created_task_ids:
                    self.created_task_ids.remove(task_id)
                response.success()
            elif response.status_code == 401:
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to update task: {response.status_code}")
    
    @task(1)
    def complete_task(self):
        """Mark a task as complete"""
        if not self.created_task_ids:
            return
        
        task_id = random.choice(self.created_task_ids)
        
        with self.client.post(
            f"/api/v1/tasks/{task_id}/complete",
            headers=self.get_headers(),
            catch_response=True,
            name="Complete Task"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                if task_id in self.created_task_ids:
                    self.created_task_ids.remove(task_id)
                response.success()
            elif response.status_code == 401:
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to complete task: {response.status_code}")
    
    @task(1)
    def delete_task(self):
        """Delete a task"""
        if not self.created_task_ids:
            return
        
        task_id = random.choice(self.created_task_ids)
        
        with self.client.delete(
            f"/api/v1/tasks/{task_id}",
            headers=self.get_headers(),
            catch_response=True,
            name="Delete Task"
        ) as response:
            if response.status_code in [200, 204]:
                if task_id in self.created_task_ids:
                    self.created_task_ids.remove(task_id)
                response.success()
            elif response.status_code == 404:
                if task_id in self.created_task_ids:
                    self.created_task_ids.remove(task_id)
                response.success()
            elif response.status_code == 401:
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to delete task: {response.status_code}")
    
    @task(2)
    def get_categories(self):
        """Get task categories"""
        with self.client.get(
            "/api/v1/tasks/categories",
            headers=self.get_headers(),
            catch_response=True,
            name="Get Categories"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                self.authenticate()
                response.failure("Unauthorized - token expired")
            else:
                response.failure(f"Failed to get categories: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Check API health - no auth required"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class StepLoadShape(LoadTestShape):
    """
    A step load shape that ramps up users gradually over time.
    
    Stages:
    - 0-60s:  5 users (warm-up)
    - 60-120s: 10 users
    - 120-180s: 20 users
    - 180-240s: 30 users
    - 240-300s: 50 users
    - 300-360s: 75 users
    - 360-420s: 100 users
    - 420-480s: 125 users
    - 480-540s: 150 users
    - 540-600s: 200 users (peak load)
    - 600-660s: 150 users (sustained)
    - 660-720s: 100 users (wind down)
    """
    
    step_time = 60  # Time in seconds for each step
    step_load = 5   # Initial number of users
    spawn_rate = 2  # Users to spawn per second
    
    # Define the stages: (time_in_seconds, number_of_users)
    stages = [
        {"duration": 60, "users": 5, "spawn_rate": 1},
        {"duration": 120, "users": 10, "spawn_rate": 2},
        {"duration": 180, "users": 20, "spawn_rate": 3},
        {"duration": 240, "users": 30, "spawn_rate": 4},
        {"duration": 300, "users": 50, "spawn_rate": 5},
        {"duration": 360, "users": 75, "spawn_rate": 6},
        {"duration": 420, "users": 100, "spawn_rate": 7},
        {"duration": 480, "users": 125, "spawn_rate": 8},
        {"duration": 540, "users": 150, "spawn_rate": 9},
        {"duration": 600, "users": 200, "spawn_rate": 10},  # Peak load
        {"duration": 660, "users": 150, "spawn_rate": 8},   # Sustained
        {"duration": 720, "users": 100, "spawn_rate": 5},   # Wind down
    ]
    
    def tick(self):
        """
        Returns a tuple with (user_count, spawn_rate) for the current tick.
        Returns None to stop the test.
        """
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        # Test completed - return None to stop
        return None


# Optional: Add event listeners for custom logging
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    print("=" * 60)
    print("Starting Load Test")
    print("=" * 60)
    print(f"Target host: {environment.host}")
    print(f"Using StepLoadShape for gradual ramp-up")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    print("=" * 60)
    print("Load Test Completed")
    print("=" * 60)
    stats = environment.stats
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print("=" * 60)
