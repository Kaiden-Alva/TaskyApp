import pytest

from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.schema import Base, User
from backend.services.user_service import UserService
from backend.models.user import UserCreate, UserUpdate, Category, Tag

# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    
    #clear tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def user_service(db_session):
    return UserService(db_session)

@pytest.fixture
def sample_user_create():
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="hashed_password_123",
        full_name="Test User",
        categories=[
            Category(name="Work", color="#FF5733"),
            Category(name="Personal", color="#33FF57")
        ],
        tags=[
            Tag(name="urgent", color="#FF0000"),
            Tag(name="important", color="#FFA500")
        ]
    )

@pytest.fixture
def created_user(user_service, sample_user_create):
    return user_service.create_user(sample_user_create)

#User General testing methods
#pass
def test_create_user_success(user_service, sample_user_create):
    user = user_service.create_user(sample_user_create)
    assert user.id is not None
    assert user.username == sample_user_create.username
    assert user.email == sample_user_create.email
    assert user.full_name == sample_user_create.full_name

    tempCat = [cat.model_dump() for cat in sample_user_create.categories]
    tempTag = [tag.model_dump() for tag in sample_user_create.tags]
    assert user.categories == tempCat
    assert user.tags == tempTag


#Category testing methods
#pass
def test_create_new_category(user_service, created_user):
    
    new_category = Category(name="Work", color="#0000FF")
    added_category = user_service.create_category(created_user.id, new_category)
    assert added_category is not None
    assert added_category["name"] == new_category.name
    assert added_category["color"] == new_category.color 

    assert any(c["name"] == new_category.name and c["color"] == new_category.color for c in created_user.categories)

#pass
#this function will need to be changed
def test_create_existing_category(user_service, created_user):
    existing_category = Category(name="Work", color="#333332")
    added_category = user_service.create_category(created_user.id, existing_category)

    number_of_identical_categories = 0
    for c in created_user.categories:
        if c["name"] == existing_category.name:
            number_of_identical_categories += 1

    #the create function can also act as an update function
    assert added_category is not None
    assert number_of_identical_categories == 1
    assert added_category["color"] == existing_category.color    

#pass
def test_get_categories(user_service, created_user):
    categories = user_service.get_categories(created_user.id)

    assert categories is not None
    assert categories == created_user.categories

#pass
def test_delete_category(user_service, created_user):
    category_to_delete = "Personal"
    updated_categories = user_service.delete_category(created_user.id, category_to_delete)
    assert updated_categories is not None

    assert all(c["name"] != category_to_delete for c in created_user.categories)


#Tag testing methods
#pass
def test_create_new_tag(user_service, created_user):
    new_tag = Tag(name="review", color="#00FF00")
    added_tag = user_service.create_tag(created_user.id, new_tag)

    assert added_tag is not None
    assert added_tag["name"] == new_tag.name
    assert added_tag["color"] == new_tag.color
    
    assert any(tag["name"] == new_tag.name and tag["color"] == new_tag.color for tag in created_user.tags)

#pass
#this function will need to be changed
def test_create_existing_tag(user_service, created_user):
    existing_tag = Tag(name="urgent", color="#78781b")
    added_tag = user_service.create_tag(created_user.id, existing_tag)

    number_of_identical_tags = 0
    for t in created_user.tags:
        if t["name"] == existing_tag.name:
            number_of_identical_tags += 1

    #the create function can also act as an update function
    assert added_tag is not None
    assert number_of_identical_tags == 1
    assert added_tag["color"] == existing_tag.color 

#pass
def test_get_tags(user_service, created_user):
    tags = user_service.get_tags(created_user.id)

    assert tags is not None
    assert tags == created_user.tags

#pass
def test_delete_tag(user_service, created_user):
    tag_to_delete = "important"
    updated_tags = user_service.delete_tag(created_user.id, tag_to_delete)

    assert updated_tags is not None
    assert all(tag["name"] != tag_to_delete for tag in created_user.tags)
