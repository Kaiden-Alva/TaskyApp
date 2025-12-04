from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class TaskCreate(BaseModel):
    '''
    args:
        owner_id: int
        name: str
        description: str
        category: str
        parameters: Dict[str, Any]  # TODO: Refine structure
    '''
    model_config = ConfigDict(
        validate_assignment=True,  # Validate on assignment
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_default=True,  # Validate default values
    )
    
    owner_id: int
    name: str
    description: str = ''  # Default empty string
    category: str = 'General'  # Default category
    dueDate: Optional[datetime] = None
    parameters: Dict[str, Any] = {}  # Default empty dict
    completed: bool = False

    tags: Optional[list[str]] = None
    priority: int = 0


    # Validate inputs before assignment
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Task name cannot be empty')
        return v.strip()

    @field_validator('owner_id')
    @classmethod
    def validate_owner_id(cls, v):
        if v <= 0:
            raise ValueError('Owner ID must be a positive integer')
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        return v.strip() if v else ''

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        return v.strip() if v else 'General'
    
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if(v is None):
            v = []
        
        for i, tag in enumerate(v):
            if(tag is None):
                raise ValueError('tags in the tag list can not be None')
            elif(not isinstance(tag, str)):
                v[i] = str(tag)
        
        return v 

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if(v == None):
            v = 0

        if not isinstance(v, int) or v < 0 or v > 3:
            raise ValueError('A tasks priority must be in the interval [0,3]')
        return v 
    


class TaskRead(BaseModel):
    '''
    args:
        id: int
        owner_id: int
        name: str
        description: str
        category: str
        parameters: Dict[str, Any]  # TODO: Refine structure
    '''
    id: int
    owner_id: int
    name: str
    description: str
    category: str
    dueDate: Optional[datetime] = None
    parameters: Dict[str, Any]  # TODO: Refine structure
    completed: bool = False

    tags: Optional[list[str]] = None
    priority: int = 0


class TaskUpdate(BaseModel):
    '''
    args:
        name: str (optional)
        description: str (optional)
        category: str (optional)
        dueDate: datetime (optional)
        parameters: Dict[str, Any] (optional)
        completed: bool (optional)
    '''
    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        validate_default=True,
    )
    
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    dueDate: Optional[datetime] = None
    parameters: Optional[Dict[str, Any]] = None
    completed: Optional[bool] = None

    tags: Optional[list[str]] = None
    priority: int = 0

    # Validate inputs before assignment
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Task name cannot be empty')
        return v.strip() if v else None

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        return v.strip() if v else None

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        return v.strip() if v else None

    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return None

        for i, tag in enumerate(v):
            if tag is None:
                raise ValueError('tags in the tag list can not be None')
            elif not isinstance(tag, str):
                v[i] = str(tag)

        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if(v == None):
            v = 0

        if not isinstance(v, int) or v < 0 or v > 3:
            raise ValueError('A tasks priority must be in the interval [0,3]')
        return v 
    

class TaskList(BaseModel):
    tasks: List[TaskRead] = []
