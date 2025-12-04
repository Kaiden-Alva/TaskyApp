from fastapi.testclient import TestClient

from backend.api.v1.user import get_user_service, get_userAuth_service
from backend.main import app
from backend.services.user_service import UserService
from backend.services.user_auth_service import userAuthService
from tests.test_db import TestingSessionLocal

# Setup the TestClient
client = TestClient(app)

# Dependency to override the get_db dependency in the main app


def override_get_user_service():
    session = TestingSessionLocal()
    yield UserService(session=session)


def override_get_userAuth_service():
    session = TestingSessionLocal()
    yield userAuthService(session=session)


app.dependency_overrides[get_user_service] = override_get_user_service
app.dependency_overrides[get_userAuth_service] = override_get_userAuth_service

# ===================== User Authentication Tests =====================

def test_create_and_get_user():
    # Create a new user
    response = client.post("/api/v1/register/", json={"username": "johndoe",
                           "email": "johndoe@example.com", "password": "secretJohn", "full_name": "John Doe"})
    assert response.status_code == 200
    created_user = response.json()
    assert created_user["username"] == "johndoe"
    assert created_user["email"] == "johndoe@example.com"
    assert created_user["full_name"] == "John Doe"
    assert "password" not in created_user  # Ensure password is not returned
    assert "id" in created_user

    # Fetch the same user
    get_response = client.get(f"/api/v1/users/{created_user['id']}")
    assert get_response.status_code == 200
    fetched_user = get_response.json()
    assert fetched_user["id"] == created_user["id"]
    assert fetched_user["full_name"] == "John Doe"


def test_login_for_access_token():
    # First, create a user to test login
    register_response = client.post(
        "/api/v1/register/",
        json={
            "username": "janedoe",
            "email": "jane@example.com",
            "password": "mySecurePassword123",
            "full_name": "Jane Doe"
        }
    )
    assert register_response.status_code == 200

    # Test successful login
    login_response = client.post(
        "/api/v1/token",
        data={
            "username": "janedoe",
            "password": "mySecurePassword123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert len(token_data["access_token"]) > 0

    # Test login with wrong password
    wrong_password_response = client.post(
        "/api/v1/token",
        data={
            "username": "janedoe",
            "password": "wrongPassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert wrong_password_response.status_code == 401
    assert "Incorrect username or password" in wrong_password_response.json()[
        "detail"]

    # Test login with non-existent user
    nonexistent_user_response = client.post(
        "/api/v1/token",
        data={
            "username": "nonexistent",
            "password": "somePassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert nonexistent_user_response.status_code == 401
    assert "Incorrect username or password" in nonexistent_user_response.json()[
        "detail"]


# ===================== Category Tests =====================


def test_create_and_get_categories():
    """Test creating a category and retrieving all categories"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "categoryuser",
        "email": "category@example.com",
        "password": "catPass123",
        "full_name": "Category User"
    })
    assert response.status_code == 200
    user = response.json()
    user_id = user["id"]
    
    # Create a category
    category_data = {"name": "Work", "color": "#FF5733"}
    create_response = client.put(
        f"/api/v1/users/{user_id}/categories",
        json=category_data
    )
    assert create_response.status_code == 200
    created_category = create_response.json()
    assert created_category["name"] == "Work"
    assert created_category["color"] == "#FF5733"
    
    # Get all categories
    get_response = client.get(f"/api/v1/users/{user_id}/categories")
    assert get_response.status_code == 200
    categories = get_response.json()
    assert len(categories) >= 1
    assert any(c["name"] == "Work" for c in categories)


def test_create_multiple_categories():
    """Test creating multiple categories for a user"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "multicatuser",
        "email": "multicat@example.com",
        "password": "multiPass123",
        "full_name": "Multi Cat User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create multiple categories
    categories_to_create = [
        {"name": "Personal", "color": "#33FF57"},
        {"name": "Shopping", "color": "#3357FF"},
        {"name": "Health", "color": "#FF33A8"}
    ]
    
    for cat in categories_to_create:
        create_response = client.put(
            f"/api/v1/users/{user_id}/categories",
            json=cat
        )
        assert create_response.status_code == 200
    
    # Get all categories
    get_response = client.get(f"/api/v1/users/{user_id}/categories")
    assert get_response.status_code == 200
    categories = get_response.json()
    
    category_names = [c["name"] for c in categories]
    assert "Personal" in category_names
    assert "Shopping" in category_names
    assert "Health" in category_names


def test_update_existing_category():
    """Test updating an existing category (same name, different color)"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "updatecatuser",
        "email": "updatecat@example.com",
        "password": "updatePass123",
        "full_name": "Update Cat User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create a category
    category_data = {"name": "Fitness", "color": "#FF0000"}
    client.put(f"/api/v1/users/{user_id}/categories", json=category_data)
    
    # Update the same category with a different color
    updated_category_data = {"name": "Fitness", "color": "#00FF00"}
    update_response = client.put(
        f"/api/v1/users/{user_id}/categories",
        json=updated_category_data
    )
    assert update_response.status_code == 200
    
    # Verify the color was updated
    get_response = client.get(f"/api/v1/users/{user_id}/categories")
    categories = get_response.json()
    fitness_categories = [c for c in categories if c["name"] == "Fitness"]
    
    # Should only have one "Fitness" category with updated color
    assert len(fitness_categories) == 1
    assert fitness_categories[0]["color"] == "#00FF00"


def test_delete_category():
    """Test deleting a category"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "deletecatuser",
        "email": "deletecat@example.com",
        "password": "deletePass123",
        "full_name": "Delete Cat User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create categories
    client.put(f"/api/v1/users/{user_id}/categories",
               json={"name": "ToKeep", "color": "#111111"})
    client.put(f"/api/v1/users/{user_id}/categories",
               json={"name": "ToDelete", "color": "#222222"})
    
    # Delete one category
    delete_response = client.delete(
        f"/api/v1/users/{user_id}/categories/ToDelete"
    )
    assert delete_response.status_code == 200
    
    # Verify it was deleted
    get_response = client.get(f"/api/v1/users/{user_id}/categories")
    categories = get_response.json()
    category_names = [c["name"] for c in categories]
    
    assert "ToKeep" in category_names
    assert "ToDelete" not in category_names


def test_get_categories_for_nonexistent_user():
    """Test getting categories for a user that doesn't exist"""
    response = client.get("/api/v1/users/99999/categories")
    assert response.status_code == 404


# ===================== Tag Tests =====================


def test_create_and_get_tags():
    """Test creating a tag and retrieving all tags"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "taguser",
        "email": "tag@example.com",
        "password": "tagPass123",
        "full_name": "Tag User"
    })
    assert response.status_code == 200
    user = response.json()
    user_id = user["id"]
    
    # Create a tag
    tag_data = {"name": "urgent", "color": "#FF0000"}
    create_response = client.put(
        f"/api/v1/users/{user_id}/tags",
        json=tag_data
    )
    assert create_response.status_code == 200
    created_tag = create_response.json()
    assert created_tag["name"] == "urgent"
    assert created_tag["color"] == "#FF0000"
    
    # Get all tags
    get_response = client.get(f"/api/v1/users/{user_id}/tags")
    assert get_response.status_code == 200
    tags = get_response.json()
    assert len(tags) >= 1
    assert any(t["name"] == "urgent" for t in tags)


def test_create_multiple_tags():
    """Test creating multiple tags for a user"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "multitaguser",
        "email": "multitag@example.com",
        "password": "multitagPass123",
        "full_name": "Multi Tag User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create multiple tags
    tags_to_create = [
        {"name": "important", "color": "#FFA500"},
        {"name": "review", "color": "#00FF00"},
        {"name": "blocked", "color": "#808080"}
    ]
    
    for tag in tags_to_create:
        create_response = client.put(
            f"/api/v1/users/{user_id}/tags",
            json=tag
        )
        assert create_response.status_code == 200
    
    # Get all tags
    get_response = client.get(f"/api/v1/users/{user_id}/tags")
    assert get_response.status_code == 200
    tags = get_response.json()
    
    tag_names = [t["name"] for t in tags]
    assert "important" in tag_names
    assert "review" in tag_names
    assert "blocked" in tag_names


def test_update_existing_tag():
    """Test updating an existing tag (same name, different color)"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "updatetaguser",
        "email": "updatetag@example.com",
        "password": "updatetagPass123",
        "full_name": "Update Tag User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create a tag
    tag_data = {"name": "priority", "color": "#FF0000"}
    client.put(f"/api/v1/users/{user_id}/tags", json=tag_data)
    
    # Update the same tag with a different color
    updated_tag_data = {"name": "priority", "color": "#0000FF"}
    update_response = client.put(
        f"/api/v1/users/{user_id}/tags",
        json=updated_tag_data
    )
    assert update_response.status_code == 200
    
    # Verify the color was updated
    get_response = client.get(f"/api/v1/users/{user_id}/tags")
    tags = get_response.json()
    priority_tags = [t for t in tags if t["name"] == "priority"]
    
    # Should only have one "priority" tag with updated color
    assert len(priority_tags) == 1
    assert priority_tags[0]["color"] == "#0000FF"


def test_delete_tag():
    """Test deleting a tag"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "deletetaguser",
        "email": "deletetag@example.com",
        "password": "deletetagPass123",
        "full_name": "Delete Tag User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create tags
    client.put(f"/api/v1/users/{user_id}/tags",
               json={"name": "keepme", "color": "#111111"})
    client.put(f"/api/v1/users/{user_id}/tags",
               json={"name": "deleteme", "color": "#222222"})
    
    # Delete one tag
    delete_response = client.delete(
        f"/api/v1/users/{user_id}/tags/deleteme"
    )
    assert delete_response.status_code == 200
    
    # Verify it was deleted
    get_response = client.get(f"/api/v1/users/{user_id}/tags")
    tags = get_response.json()
    tag_names = [t["name"] for t in tags]
    
    assert "keepme" in tag_names
    assert "deleteme" not in tag_names


def test_get_tags_for_nonexistent_user():
    """Test getting tags for a user that doesn't exist"""
    response = client.get("/api/v1/users/99999/tags")
    assert response.status_code == 404


def test_category_and_tag_independence():
    """Test that categories and tags are independent"""
    # Create a user
    response = client.post("/api/v1/register/", json={
        "username": "independentuser",
        "email": "independent@example.com",
        "password": "independPass123",
        "full_name": "Independent User"
    })
    user = response.json()
    user_id = user["id"]
    
    # Create a category and a tag with the same name
    client.put(f"/api/v1/users/{user_id}/categories",
               json={"name": "common", "color": "#FF0000"})
    client.put(f"/api/v1/users/{user_id}/tags",
               json={"name": "common", "color": "#00FF00"})
    
    # Get categories and tags
    cat_response = client.get(f"/api/v1/users/{user_id}/categories")
    tag_response = client.get(f"/api/v1/users/{user_id}/tags")
    
    categories = cat_response.json()
    tags = tag_response.json()
    
    # Both should exist independently with different colors
    common_cat = next(c for c in categories if c["name"] == "common")
    common_tag = next(t for t in tags if t["name"] == "common")
    
    assert common_cat["color"] == "#FF0000"
    assert common_tag["color"] == "#00FF00"
