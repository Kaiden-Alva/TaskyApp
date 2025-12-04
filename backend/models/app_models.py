from pydantic import BaseModel
from typing import Optional, Dict, Any

class Command(BaseModel):
    command: str
    args: Optional[Dict[str, Any]] = None