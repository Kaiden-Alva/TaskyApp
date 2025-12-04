#!/usr/bin/env python3
"""
PostgreSQL database initialization script.
Creates tables and seeds initial data only if database is empty.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect
from backend.db.schema import Base, engine, SessionLocal, User
from backend.models.user import UserCreate
from backend.models.task import TaskCreate
from backend.services.user_service import UserService
from backend.services.task_service import TaskService
from backend.services.user_auth_service import userAuthService


def database_is_empty() -> bool:
    """Check if database has any data"""
    db_session = SessionLocal()
    try:
        # Check if users table has any data
        user_count = db_session.query(User).count()
        return user_count == 0
    finally:
        db_session.close()


def init_database():
    """Initialize database with schema and seed data if empty"""
    
    # Create all tables if they don't exist
    print("🔍 Checking database schema...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if not existing_tables:
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
    else:
        print(f"✅ Database tables already exist: {', '.join(existing_tables)}")
    
    # Check if database is empty
    if not database_is_empty():
        print("⏭️  Database already contains data. Skipping seed data.")
        print("🎉 Database initialization complete!")
        return
    
    print("🌱 Seeding initial data...")
    
    # Seed initial data
    db_session = SessionLocal()
    try:        
        user_service = UserService(db_session)
        task_service = TaskService(db_session)
        auth_service = userAuthService(db_session)
        
        # Create admin and demo users
        print("\n👥 Creating users...")
        sample_users = [
            {
                "username": "admin",
                "full_name": "Admin User",
                "email": "admin@taskmanager.com",
                "password": "admin",
            },
            {
                "username": "demo",
                "full_name": "Demo User",
                "email": "demo@taskmanager.com",
                "password": "demo",
            },
        ]
        
        created_users = {}
        for user_data in sample_users:
            # Hash the password before creating the user
            hashed_password = auth_service.get_password_hash(user_data["password"])
            user_data["password"] = hashed_password
            user = user_service.create_user(UserCreate(**user_data))
            created_users[user.username] = user
            print(f"   ✅ Created user: {user.username} (ID: {user.id})")
        
        # Create sample tasks for admin user
        print("\n📝 Creating tasks for admin user...")
        admin_tasks = [
            TaskCreate(
                name="Review System Architecture",
                description="Review and update the system architecture documentation",
                owner_id=created_users["admin"].id,
                priority=3,
                category="Work",
                tags=["important", "documentation"],
                dueDate=datetime.now() + timedelta(days=2)
            ),
            TaskCreate(
                name="User Management Audit",
                description="Audit user permissions and access levels",
                owner_id=created_users["admin"].id,
                priority=2,
                category="Security",
                tags=["security", "audit"],
                dueDate=datetime.now() + timedelta(days=5)
            ),
            TaskCreate(
                name="Setup Monitoring",
                description="Configure application monitoring and alerts",
                owner_id=created_users["admin"].id,
                priority=2,
                category="DevOps",
                tags=["infrastructure", "monitoring"]
            ),
        ]
        
        for task_data in admin_tasks:
            task = task_service.create_task(task_data)
            print(f"   ✅ {task.name}")
        
        # Create sample tasks for demo user
        print("\n📝 Creating tasks for demo user...")
        demo_tasks = [
            TaskCreate(
                name="Welcome to Task Manager!",
                description="Explore the features and get familiar with the interface",
                owner_id=created_users["demo"].id,
                priority=1,
                category="Personal",
                tags=["getting-started"],
                completed=False
            ),
            TaskCreate(
                name="Plan Weekly Goals",
                description="Set objectives for the upcoming week",
                owner_id=created_users["demo"].id,
                priority=2,
                category="Planning",
                tags=["goals", "planning"],
                dueDate=datetime.now() + timedelta(days=1)
            ),
            TaskCreate(
                name="Team Meeting Preparation",
                description="Prepare slides and agenda for the team meeting",
                owner_id=created_users["demo"].id,
                priority=3,
                category="Work",
                tags=["meeting", "urgent"],
                dueDate=datetime.now() + timedelta(days=3)
            ),
            TaskCreate(
                name="Buy Groceries",
                description="Milk, eggs, bread, vegetables, and fruits",
                owner_id=created_users["demo"].id,
                priority=1,
                category="Personal",
                tags=["shopping", "errands"],
                dueDate=datetime.now() + timedelta(days=1)
            ),
            TaskCreate(
                name="Read Documentation",
                description="Go through the PostgreSQL performance tuning guide",
                owner_id=created_users["demo"].id,
                priority=1,
                category="Learning",
                tags=["database", "learning"]
            ),
        ]
        
        for task_data in demo_tasks:
            task = task_service.create_task(task_data)
            print(f"   ✅ {task.name}")
            
        db_session.commit()
        print("\n🎉 Database initialization complete!")
        print(f"\n📊 Summary:")
        print(f"   • Users created: {len(created_users)}")
        print(f"   • Tasks created: {len(admin_tasks) + len(demo_tasks)}")
        print(f"\n🔐 Login credentials:")
        print(f"   Admin: username='admin', password='admin123'")
        print(f"   Demo:  username='demo', password='demo123'")
            
    except Exception as e:
        db_session.rollback()
        print(f"\n❌ Error during database initialization: {e}")
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    init_database()