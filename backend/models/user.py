from pydantic import BaseModel, ConfigDict, field_validator

class CategoryException(Exception):
    def __init__(self, message: str, category_name: str | None = None):
        self.category_name = category_name
        if category_name:
            new_message = f"CategoryException for {self.category_name}: {message}"        
        else:
            new_message = f"CategoryException: {message}"
        self.message = new_message
        
        super().__init__(self.message)


class TagException(Exception):
    def __init__(self, message: str, tag_name: str | None = None):
        self.tag_name = tag_name 
        if tag_name:
            new_message = f"TagException for {self.tag_name}: {message}"        
        else:
            new_message = f"TagException: {message}"
        self.message = new_message

        super().__init__(self.message)


class Category(BaseModel):
    '''
    args:
        name: str
        color: str 
    '''
    
    name: str
    color: str 

    @field_validator('name')
    def validate_category_name(cls, v):
        if not v or not v.strip():
            raise CategoryException('Category name cannot be empty')
        return v.strip()

class Tag(BaseModel):
    '''
    args:
        name: str
        color: str 
    '''
    
    name: str
    color: str

    @field_validator('name')
    def validate_tag_name(cls, v):
        if not v or not v.strip():
            raise TagException('Tag name cannot be empty')
        return v.strip()

class UserCreate(BaseModel):
    '''
    args:
        username: str
        email: str | None = None
        password: str
        full_name: str | None = None
        categories: list[Category] | None = None 
        tags: list[Tag] | None = None 
    '''
    username: str
    email: str | None = None
    password: str
    full_name: str | None = None

    categories: list[Category] | None = [Category(name="General", color="#5dafb0")] #JUSTADDED
    tags: list[Tag] | None = None #JUSTADDED
    
    @field_validator('categories')
    def validate_categories(cls, categories):
        if categories is not None:
            names = [cat.name for cat in categories]
            if len(names) != len(set(names)):
                raise CategoryException("Duplicate category names are not allowed")
        return categories

    @field_validator('tags')
    def validate_tags(cls, tags):
        if tags is not None:
            names = [tag.name for tag in tags]
            if len(names) != len(set(names)):
                raise TagException("Duplicate tag names are not allowed")
        return tags


class UserRead(BaseModel):
    '''
    args:
        id: int
        username: str
        email: str | None = None
        full_name: str | None = None
        disabled: bool = False
        categories: list[Category] | None = None 
        tags: list[Tag] | None = None
    '''
    model_config = ConfigDict(
        from_attributes=True)  # Allows Pydantic to read from SQLAlchemy models

    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False

    categories: list[Category] | None = None #JUSTADDED
    tags: list[Tag] | None = None #JUSTADDED

class UserUpdate(BaseModel):
    '''
    args:
        username: str
        email: str | None = None
        full_name: str | None = None
        categories: list[Category] | None = None 
        tags: list[Tag] | None = None
    '''

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    username: str
    email: str | None = None
    full_name: str | None = None

    categories: list[Category] | None = None #JUSTADDED
    tags: list[Tag] | None = None #JUSTADDED

    @field_validator('categories')
    def validate_categories(cls, categories):
        if categories is not None:
            names = [cat.name for cat in categories]
            if len(names) != len(set(names)):
                raise CategoryException("Duplicate category names are not allowed")
        return categories

    @field_validator('tags')
    def validate_tags(cls, tags):
        if tags is not None:
            names = [tag.name for tag in tags]
            if len(names) != len(set(names)):
                raise TagException("Duplicate tag names are not allowed")
        return tags



class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserInDB(UserRead):
    hashed_password: str
