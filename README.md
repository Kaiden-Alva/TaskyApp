# Smart Task Manager

A flexible task management application with both CLI and REST API interfaces, powered by PostgreSQL database with optimized performance settings.

## 🏗️ Architecture

### Project Structure

```
CS2450Project/
├── backend/
│   ├── api/v1/          # FastAPI route handlers
│   ├── core/            # Configuration and logging
│   ├── db/              # SQLAlchemy schema and database setup
│   ├── models/          # Pydantic models for validation
│   ├── services/        # Business logic layer
│   │   ├── cli.py       # CLI interface
│   │   ├── orchestrator.py  # Routes requests to services
│   │   ├── task_service.py  # Task business logic
│   │   └── user_service.py  # User business logic
│   └── main.py          # Application entry point
├── frontend/            # React frontend (Vite)
├── tests/               # Test suite
├── .env                 # Environment configuration
├── docker-compose.yml   # Docker orchestration
└── run.py               # CLI launcher script
```

### Technology Stack

- **Backend Framework**: FastAPI (async REST API)
- **ORM**: SQLAlchemy 2.0 (with modern typed mappings)
- **Database**: PostgreSQL 16 (production-grade with performance optimizations)
- **Validation**: Pydantic v2 (models with automatic validation)
- **Frontend**: React + Vite
- **Configuration**: pydantic-settings + python-dotenv
- **Testing**: pytest

### Design Patterns

**Orchestrator Pattern**: Routes requests from CLI and API to shared business logic

- CLI → Orchestrator → Services → Storage (DB/JSON)
- API → Orchestrator → Services → Storage (DB/JSON)

**Service Layer Pattern**: Business logic separated from interface/storage

- `UserService` / `UserServiceJson`: User CRUD operations
- `TaskService` / `TaskServiceJson`: Task CRUD operations

**Feature Flags**: Toggle functionality via environment variables

- `use_cli`: Enable/disable CLI interface
- `use_db`: Switch between SQLite database and JSON file storage
- `debug`: Enable debug logging and auto-reload

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **PostgreSQL 16+** (for local development without Docker)
- Python 3.12+ (for local development)
- UV package manager (for local development)
- Node.js 20+ (for local frontend development)

### Method 1: Docker Compose (Recommended) 🐳

**The easiest and recommended way to run the application:**

1. **Clone the repository**

   ```bash
   git clone https://github.com/UVUTeamProjects/CS2450Project.git
   cd CS2450Project
   ```

2. **Build and start the application**

   ```bash
   # Start backend and frontend (recommended for local development)
   docker-compose up backend frontend --build

   # Run in detached mode (runs in background)
   docker-compose up backend frontend -d

   # Build and start all services including cloudflared (production)
   # Note: Only use this on the server
   docker-compose --profile web up --build
   ```

3. **Access the application**

   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **PostgreSQL**: localhost:5432
   - **API Documentation**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

4. **Useful Docker commands**

   ```bash
   # Stop all services
   docker-compose down

   # View logs
   docker-compose logs -f backend
   docker-compose logs -f frontend

   # Rebuild after code changes
   docker-compose up --build

   # Remove all containers and volumes
   docker-compose down -v
   ```

### Method 2: Local Development (Without Docker)

For developers who want to run the application locally without Docker:

1. **Install PostgreSQL**

   ```bash
   # macOS
   brew install postgresql@16
   brew services start postgresql@16

   # Ubuntu/Debian
   sudo apt install postgresql-16
   sudo systemctl start postgresql

   # Windows - Download from postgresql.org
   ```

2. **Create database**

   ```bash
   psql -U postgres
   CREATE DATABASE smart_task_manager;
   \q
   ```

3. **Clone and install dependencies**

   ```bash
   git clone https://github.com/UVUTeamProjects/CS2450Project.git
   cd CS2450Project

   # Install Python dependencies
   pip install -e .
   # or using uv
   uv sync
   ```

4. **Configure environment variables**

   ```bash
   cp env.example .env
   # Edit .env with your PostgreSQL settings
   # DB_USER=postgres
   # DB_PASSWORD=your_password
   # DB_NAME=smart_task_manager
   # DB_HOST=localhost
   # DB_PORT=5432
   ```

5. **Database Setup**

   This creates the database schema and seeds initial users and data:

   ```bash
   python init_db.py
   ```

6. **Run the application**

   ```bash
   # Using the .env file
   python -m backend.main

   # Using command-line arguments
   python run.py --api --db
   python run.py --api --db --debug

   # CLI mode with database
   python run.py --cli --db

   # CLI mode with JSON storage
   python run.py --cli --json
   ```

7. **Run the frontend (separate terminal)**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Method 3: Environment Variable Overrides

Override `.env` values without changing the file:

```bash
# API server with database
use_cli=false use_db=true python -m backend.main

# CLI with database
use_cli=true use_db=true python -m backend.main

# CLI with JSON storage
use_cli=true use_db=false python -m backend.main
```

## 🐳 Docker Tips & Troubleshooting

### Common Docker Commands

```bash
# Check running containers
docker-compose ps

# View logs in real-time
docker-compose logs -f

# Restart a specific service
docker-compose restart backend

# Access backend container shell
docker-compose exec backend /bin/bash

# Remove all containers and volumes (fresh start)
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache

# Run database initialization
docker-compose run backend python init_db.py
```

### Troubleshooting

**Port already in use:**

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

**PostgreSQL connection issues:**

```bash
# Check PostgreSQL is healthy
docker-compose ps db
docker-compose logs db

# Restart PostgreSQL
docker-compose restart db

# Fresh start (removes all data!)
docker-compose down -v
docker-compose up --build
```

**Frontend not updating:**

```bash
# Rebuild frontend with no cache
docker-compose build --no-cache frontend
docker-compose up frontend
```

## 🗄️ Database Schema (PostgreSQL + SQLAlchemy)

### User Table

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String, index=True)
    disabled: Mapped[bool] = mapped_column(default=False)
    categories: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    tags: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
```

### Task Table

```python
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    dueDate: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    parameters: Mapped[str] = mapped_column(JSON)
    completed: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0)
```

**Key Features:**

- Modern SQLAlchemy 2.0 `Mapped[]` type annotations
- Foreign key relationships (Task → User)
- JWT authentication with hashed passwords
- JSON fields for flexible data (categories, tags, parameters)
- Priority levels (0-3) and due dates
- Task completion tracking
- Automatic table creation on startup
- Indexed columns for performance
- PostgreSQL with connection pooling and performance optimizations
- Performance-tuned for production workloads

## 📐 Pydantic Models (Validation Layer)

The application uses Pydantic v2 for request/response validation and data serialization:

### Task Models

```python
# TaskCreate - Creating new tasks
class TaskCreate(BaseModel):
    owner_id: int
    name: str                              # Required, validated non-empty
    description: str = ''                   # Optional, defaults to empty
    category: str = 'General'               # Optional, defaults to 'General'
    dueDate: Optional[datetime] = None      # Optional due date
    parameters: Dict[str, Any] = {}         # Flexible metadata
    completed: bool = False
    tags: Optional[list[str]] = None        # Task tags
    priority: int = 0                       # 0-3, validated range

# TaskRead - Reading tasks (includes ID)
class TaskRead(BaseModel):
    id: int                                 # Auto-generated
    owner_id: int
    name: str
    description: str
    category: str
    dueDate: Optional[datetime] = None
    parameters: Dict[str, Any]
    completed: bool = False
    tags: Optional[list[str]] = None
    priority: int = 0

# TaskUpdate - Updating tasks (all fields optional)
class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    dueDate: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    completed: Optional[bool] = None
    tags: Optional[list[str]] = None
    priority: int = 0
```

### User Models

```python
# UserCreate - Registration
class UserCreate(BaseModel):
    username: str                          # Required, validated unique
    email: str | None = None
    password: str                          # Will be hashed
    full_name: str | None = None
    categories: list[Category] | None = None
    tags: list[Tag] | None = None

# UserRead - User data (without password)
class UserRead(BaseModel):
    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False
    categories: list[Category] | None = None
    tags: list[Tag] | None = None

# UserUpdate - Updating user
class UserUpdate(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    categories: list[Category] | None = None
    tags: list[Tag] | None = None

# Category/Tag
class Category(BaseModel):
    name: str                              # Validated non-empty
    color: str                             # Hex color code

class Tag(BaseModel):
    name: str
    color: str
```

**Validation Features:**

- Automatic type checking and coercion
- Field validation (non-empty strings, valid ranges, etc.)
- Duplicate detection for categories and tags
- Password hashing on user creation
- Whitespace stripping on string fields
- Custom validators for complex business rules

## 🔌 FastAPI Endpoints

### Authentication Routes (`/api/v1`)

```http
POST   /api/v1/register           # Register new user
POST   /api/v1/token              # Login and get access token
POST   /api/v1/refresh            # Refresh access token
GET    /api/v1/users/me           # Get current authenticated user
```

**Authentication Examples:**

```json
// Register Request
POST /api/v1/register
{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
}

// Login Request (form data)
POST /api/v1/token
username=johndoe&password=securepassword

// Response
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}

// Use token in subsequent requests
Authorization: Bearer <access_token>
```

### User Routes (`/api/v1/users`)

```http
GET    /api/v1/users                              # List all users
GET    /api/v1/users/{user_id}                    # Get user by ID
PUT    /api/v1/users/{user_id}                    # Update user
GET    /api/v1/users/{user_id}/categories         # Get user categories
PUT    /api/v1/users/{user_id}/categories         # Create category
DELETE /api/v1/users/{user_id}/categories/{name}  # Delete category
GET    /api/v1/users/{user_id}/tags               # Get user tags
PUT    /api/v1/users/{user_id}/tags               # Create tag
DELETE /api/v1/users/{user_id}/tags/{name}        # Delete tag
```

**User Model Examples:**

```json
// UserRead Response
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "disabled": false,
  "categories": [
    { "name": "Work", "color": "#FF5733" },
    { "name": "Personal", "color": "#33FF57" }
  ],
  "tags": [
    { "name": "urgent", "color": "#FF0000" },
    { "name": "important", "color": "#FFA500" }
  ]
}
```

### Task Routes (`/api/v1/tasks`)

```http
GET    /api/v1/tasks                 # List all tasks for current user
GET    /api/v1/tasks/{task_id}       # Get task by ID
POST   /api/v1/tasks                 # Create new task
PUT    /api/v1/tasks/{task_id}       # Update task
DELETE /api/v1/tasks/{task_id}       # Delete task
POST   /api/v1/tasks/{task_id}/complete  # Mark task as complete
GET    /api/v1/tasks/categories      # Get unique categories
```

**Task Model Examples:**

```json
// TaskCreate Request
POST /api/v1/tasks
{
    "owner_id": 1,
    "name": "Complete project proposal",
    "description": "Write and submit the Q4 project proposal",
    "category": "Work",
    "dueDate": "2025-11-15T17:00:00",
    "priority": 2,
    "tags": ["urgent", "important"],
    "completed": false,
    "parameters": {
        "estimatedHours": 8,
        "assignedTo": "team-alpha"
    }
}

// TaskRead Response
{
    "id": 1,
    "owner_id": 1,
    "name": "Complete project proposal",
    "description": "Write and submit the Q4 project proposal",
    "category": "Work",
    "dueDate": "2025-11-15T17:00:00",
    "priority": 2,
    "tags": ["urgent", "important"],
    "completed": false,
    "parameters": {
        "estimatedHours": 8,
        "assignedTo": "team-alpha"
    }
}

// TaskUpdate Request (all fields optional)
PUT /api/v1/tasks/1
{
    "name": "Updated task name",
    "completed": true,
    "priority": 3
}
```

**Priority Levels:**

- `0`: No priority
- `1`: Low priority
- `2`: Medium priority
- `3`: High priority

### Interactive API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs (Interactive API testing)
- **ReDoc**: http://localhost:8000/redoc (Clean API documentation)

## 🖥️ CLI Interface

The CLI provides an interactive terminal interface for task management:

```bash
python run.py --cli --json
```

**Features:**

- User login/creation
- Add tasks with categories
- View tasks grouped by category
- Choose from existing categories or create new ones

**Example Session:**

```
Enter your name: Alice
Welcome, Alice!

Alice's Todo List:
-------------------------------------------------------

Work:
  • Complete project proposal
    Submit by Friday

Personal:
  • Buy groceries

Input options:
'1'. Add task
'2'. Remove task
'3'. Add category
'4'. Remove category
Press 'e' to exit.
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# PostgreSQL Database Configuration
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=smart_task_manager
DB_HOST=localhost
DB_PORT=5432

# Feature Flags
USE_CLI=true       # Enable CLI interface
USE_WEB=false      # Enable web interface (future)
USE_API=false      # Enable REST API
USE_DB=false       # Use database (true) or JSON files (false)

# Debugging
DEBUG=true
LOG_LEVEL=DEBUG
```

### Storage Modes

**Database Mode** (`USE_DB=true`) - Recommended:

- Uses PostgreSQL database (production-grade)
- Full SQLAlchemy ORM support with connection pooling
- Performance-optimized for production workloads
- ACID compliance and relational integrity
- Supports concurrent connections and scaling

**JSON Mode** (`USE_DB=false`) - Development only:

- Stores data in `tempUsers.json` and `tempStore.json`
- Useful for quick development/testing
- No database setup required
- Not recommended for production

### Pydantic Configuration Class

```python
class Config(BaseSettings):
    app_name: str = "Smart Task Manager"
    app_version: str = "0.1.0"
    debug: bool = False
    use_cli: bool = False
    use_db: bool = True

    # PostgreSQL configuration
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "smart_task_manager"
    db_host: str = "localhost"
    db_port: int = 5432

    @property
    def db_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

**Priority Order** (highest to lowest):

1. Command-line environment variables
2. Exported environment variables
3. `.env` file values
4. Default values in Config class

## 🧪 Testing

### Running Tests Locally

```bash
# Run all tests
pytest

# Run tests with coverage (measuring backend directory)
coverage run --source=backend -m pytest

# View terminal report
coverage report -m

# Generate HTML report for detailed analysis
coverage html

# View coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Run specific test categories
pytest tests/test_task.py          # Task model tests
pytest tests/test_db.py            # Database tests
pytest tests/api/v1/                # API endpoint tests

# Run with verbose output and show print statements
pytest -v -s

# Run tests matching a pattern
pytest -k "test_create" -v

# Generate JSON test report
pytest --json-report --json-report-file=test_output.json
```

### Test Coverage

The project maintains comprehensive test coverage across:

- **Model Validation**: Task and User Pydantic models
- **API Endpoints**: All user and task routes
- **Authentication**: JWT token generation and validation
- **Database Operations**: CRUD operations and relationships
- **Business Logic**: Task service and user service

**Coverage Report Example:**

```bash
$ pytest --cov=backend --cov-report=term

----------- coverage: platform darwin, python 3.12.0 -----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
backend/api/v1/task_api.py                87      5    94%
backend/api/v1/user.py                   132      8    94%
backend/db/schema.py                      45      2    96%
backend/models/task.py                   110      6    95%
backend/models/user.py                    85      4    95%
backend/services/task_service.py         145      9    94%
backend/services/user_service.py         128      7    95%
-----------------------------------------------------------
TOTAL                                    732     41    94%
```

### Continuous Integration

Tests run automatically on:

- Pull requests to `main` and `dev` branches
- Pre-commit hooks (if configured)
- Docker container builds

## 📦 Dependencies

**Core Dependencies:**

- `fastapi>=0.116.1` - Modern async web framework
- `uvicorn>=0.35.0` - ASGI server
- `sqlalchemy>=2.0.43` - ORM with modern type support
- `psycopg2-binary>=2.9.10` - PostgreSQL adapter for Python
- `pydantic>=2.11.9` - Data validation
- `pydantic-settings>=2.10.1` - Settings management
- `python-dotenv>=1.1.1` - Environment variable loading

**Development:**

- `pytest>=8.4.1` - Testing framework
- `httpx>=0.28.1` - HTTP client for testing
- `coverage>=7.11.0` - Code coverage tool

<!-- ## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request -->

<!-- ## 📝 License

MIT License - see LICENSE file for details -->

## 👥 Team

- UVU Team Projects -> Course: CS2450
- Ethan Howlett
- Corbin Coles
- Kaiden Alva
- Porter Jordan

## 🔮 Future Enhancements

- [x] Task completion/status tracking
- [x] Task priorities and due dates
- [x] Category management (edit/delete)
- [x] Task search and filtering
- [x] PostgreSQL support with performance optimizations
- [x] Authentication & authorization (JWT)
- [x] React frontend integration
- [ ] Task sharing between users
- [ ] Email notifications
- [ ] Real-time updates with WebSockets
- [ ] Advanced analytics and reporting

## 📚 Additional Documentation

- [PostgreSQL Migration Guide](POSTGRES_MIGRATION.md) - Complete guide for migrating to PostgreSQL
- [Authentication Setup](SETUP_AUTH.md) - JWT authentication documentation
- For UI/theme documentation, see `frontend/THEME_QUICK_REFERENCE.md`
