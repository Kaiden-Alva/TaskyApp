# Business logic for user-related operations CRUD
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import Optional, List
import json
from pathlib import Path

from backend.db.schema import User
from backend.models.user import UserCreate, UserRead, Category, Tag

class UserService:
    def __init__(self, session: Session):
        self._db = session

    def list_users(self) -> list[User]:
        try:
            return self._db.query(User).all()
        except Exception as e:
            print(f"Database error in list_users: {e}")
            return []

    def get_user(self, user_id: int) -> User | None:
        try:
            return self._db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            print(f"Database error in get_user: {e}")
            return None

    def create_user(self, user_create: UserCreate) -> UserRead:
        try:
            # Convert Category and Tag objects to dictionaries for storage
            categories_dict = [cat.model_dump() for cat in (user_create.categories or [])]
            tags_dict = [tag.model_dump() for tag in (user_create.tags or [])]
            
            user = User(
                username=user_create.username,
                email=user_create.email or "",
                hashed_password=user_create.password,
                full_name=user_create.full_name or "",
                disabled=False,
                categories=categories_dict,
                tags=tags_dict
            )
            self._db.add(user)
            self._db.commit()
            self._db.refresh(user)
            return user
        except Exception as e:
            self._db.rollback()
            raise e
    
    def get_user_by_username(self, username: str) -> User | None:
        try:
            return self._db.query(User).filter(User.username == username).first()
        except Exception as e:
            print(f"Database error in get_user_by_username: {e}")
            return None

    def update_user(self, user_id: int, user_data: dict) -> User | None:
        """Update user information"""
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Update user fields
            for field, value in user_data.items():
                if hasattr(user, field) and field != 'id':  # Don't allow updating ID
                    if field == 'categories' and value is not None:
                        # Convert each category dict to Category model and then back to dict
                        categories = [Category(**cat).model_dump() for cat in value]
                        setattr(user, field, categories)
                    elif field == 'tags' and value is not None:
                        # Convert each tag dict to Tag model and then back to dict
                        tags = [Tag(**tag).model_dump() for tag in value]
                        setattr(user, field, tags)
                    else:
                        setattr(user, field, value)
            
            self._db.add(user)
            self._db.commit()
            self._db.refresh(user)
            return user
        except Exception as e:
            self._db.rollback()
            print(f"Database error in update_user: {e}")
            raise e
    
    def create_category(self, user_id: int, category: Category):
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            #get current categories
            categories_list = user.categories or []

            #check for existing category names
            category_exists = False
            for i, existing_cat in enumerate(categories_list):
                if existing_cat['name'] == category.name:
                    categories_list[i] = category.model_dump()
                    category_exists = True
                    break
            
            if not category_exists:
                categories_list.append(category.model_dump())

            #set user.categoeis to categories_list
            #setattr(user, 'categories', categories_list)
            setattr(user, 'categories', categories_list)
            flag_modified(user, "categories")  # Inform SQLAlchemy of the change`

            self._db.commit()
            self._db.refresh(user)
            return category.model_dump()
        except Exception as e:
            self._db.rollback()
            print(f"Database error in create_categories: {e}")
            raise e

    def create_tag(self, user_id: int, tag: Tag):
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            #get current categories
            tag_list = user.tags or []
            
            #check for existing category names
            tag_exists = False
            for i, existing_tag in enumerate(tag_list):
                if existing_tag['name'] == tag.name:
                    tag_list[i] = tag.model_dump()
                    tag_exists = True
                    break
            
            if not tag_exists:
                tag_list.append(tag.model_dump())

            #set user.categoeis to categories_list
            setattr(user, 'tags', tag_list)
            flag_modified(user, "tags")

            self._db.commit()
            self._db.refresh(user)
            return tag.model_dump()
        except Exception as e:
            self._db.rollback()
            print(f"Database error in create_tag: {e}")
            raise e

    def delete_category(self, user_id: int, category_name: str):
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            deleted_categories = []
            new_categories = []
            for cat in user.categories or []:
                if cat['name'] == category_name:
                    deleted_categories.append(cat)
                else:
                    new_categories.append(cat)

            setattr(user, 'categories', new_categories)
            flag_modified(user, "categories")

            self._db.commit()
            self._db.refresh(user)
            return deleted_categories
        except Exception as e:
            self._db.rollback()
            print(f"Database error in delete_category: {e}")
            raise e

    def delete_tag(self, user_id: int, tag_name: str):
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            deleted_tags = []
            new_tags = []
            for tag in user.tags or []:
                if tag['name'] == tag_name:
                    deleted_tags.append(tag)
                else:
                    new_tags.append(tag)

            setattr(user, 'tags', new_tags)
            flag_modified(user, "tags")

            self._db.commit()
            self._db.refresh(user)
            return deleted_tags
        except Exception as e:
            self._db.rollback()
            print(f"Database error in delete_tag: {e}")
            raise e

    def get_categories(self, user_id: int) -> List[dict]:
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            return user.categories or []
        except Exception as e:
            print(f"Database error in get_categories: {e}")
            return []

    def get_tags(self, user_id: int) -> List[dict]:
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            return user.tags or []
        except Exception as e:
            print(f"Database error in get_tags: {e}")
            return []


    ''' LEGACY CODE FOR CATEGORIES & TAGS - TO BE REMOVED LATER
    def update_categories(self, user_id: int, categories: list[Category]):
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            categories_list = [cat.model_dump() for cat in categories]
            setattr(user, 'categories', categories_list)

            self._db.add(user)
            self._db.commit()
            self._db.refresh(user)
            return user.categories
        except Exception as e:
            self._db.rollback()
            print(f"Database error in update_categories: {e}")
            raise e

    
    def update_tags(self, user_id: int, tags: list[Tag]):
        try:
            user = self._db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            tag_list = [tag.model_dump() for tag in tags]
            setattr(user, 'tags', tag_list)

            self._db.add(user)
            self._db.commit()
            self._db.refresh(user)
            return user.tags
        except Exception as e:
            self._db.rollback()
            print(f"Database error in update_categories: {e}")
            raise e
    '''


class UserServiceJson:
    def __init__(self, filepath: str = 'tempUsers.json'):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            self.filepath.write_text('[]')  # Initialize with empty list

    def list_users(self) -> List[UserRead]:
        users = json.loads(self.filepath.read_text())
        return [UserRead(**user) for user in users]

    def get_user(self, user_id: int) -> UserRead | None:
        users = json.loads(self.filepath.read_text())
        for user in users:
            if user['id'] == user_id:
                return UserRead(**user)
        return None
    
    def create_user(self, user_create: UserCreate) -> UserRead:
        users = json.loads(self.filepath.read_text())
        new_id = max((user.get('id', 0) for user in users), default=0) + 1
        # user_create.password should already be hashed
        new_user = UserRead(
            id=new_id,
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            disabled=False
        )
        users.append(new_user.model_dump())
        self.filepath.write_text(json.dumps(users, indent=4))
        return new_user

    def get_user_by_username(self, username: str) -> UserRead | None:
        users = json.loads(self.filepath.read_text())
        for user in users:
            if user.get('username') == username:
                return UserRead(**user)
        return None