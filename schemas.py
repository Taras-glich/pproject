from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from datetime import datetime

class User(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True

class Author(BaseModel):
    name: str
    email: EmailStr
    bio: Optional[str] = None

class Article(BaseModel):
    title: str
    content: str
    author: Author
    tags: Optional[List[str]] = Field(default_factory=list)
    published_at: Optional[datetime] = Field(default_factory=datetime.now)

class Comment(BaseModel):
    author_name: str
    content: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

class ArticleRequest(BaseModel):
    keywords: List[str]
    date_range: Optional[Dict[str, datetime]]  # Використовується Dict для початкових і кінцевих дат
