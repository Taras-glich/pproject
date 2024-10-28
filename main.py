from fastapi import FastAPI, Depends, HTTPException, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from typing import List, Optional, Dict
from datetime import datetime

import models
from database import get_db, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="InfoHub API", description="API для зберігання та керування інформацією")
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True


class Article(BaseModel):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = Field(default_factory=datetime.now)


class Author(BaseModel):
    name: str
    email: EmailStr
    bio: Optional[str] = None


class Comment(BaseModel):
    author_name: str
    content: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get the current user based on the token."""
    user = db.query(models.User).filter(models.User.username == token).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return user


@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Register a new user."""
    hashed_password = hash_password(password)
    new_user = models.User(username=username, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    return templates.TemplateResponse("register_success.html", {"request": request, "username": username, "title": "Успішна реєстрація"})


@app.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    """Display the registration form."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def show_login_form(request: Request):
    """Display the login form."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in a user and return a token."""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неправильне ім'я користувача або пароль")
    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Read the root endpoint."""
    return templates.TemplateResponse("index.html", {"request": request, "title": "InfoHub"})


@app.get("/add_author", response_class=HTMLResponse)
async def show_add_author_form(request: Request):
    """Display the add author form."""
    return templates.TemplateResponse("add_author.html", {"request": request})


@app.post("/authors", response_class=HTMLResponse)
async def create_author(request: Request, name: str = Form(...), email: str = Form(...), bio: str = Form(None), db: Session = Depends(get_db)):
    """Create a new author."""
    author = models.Author(name=name, email=email, bio=bio)
    db.add(author)
    db.commit()
    return RedirectResponse(url="/authors", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/authors", response_class=HTMLResponse)
async def get_authors(request: Request, db: Session = Depends(get_db)):
    """Get the list of authors."""
    authors = db.query(models.Author).all()
    return templates.TemplateResponse("authors.html", {"request": request, "authors": authors})


@app.get("/add_article", response_class=HTMLResponse)
async def show_add_article_form(request: Request):
    """Display the add article form."""
    return templates.TemplateResponse("add_article.html", {"request": request})


@app.post("/articles", response_class=HTMLResponse)
async def create_article(request: Request, title: str = Form(...), content: str = Form(...), tags: str = Form(""), db: Session = Depends(get_db)):
    """Create a new article."""
    author = db.query(models.Author).first()  # Update logic for selecting the correct author
    article = models.Article(title=title, content=content, tags=tags.split(","), author_id=author.id)
    db.add(article)
    db.commit()
    return RedirectResponse(url="/articles", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/articles", response_class=HTMLResponse)
async def get_articles(request: Request, db: Session = Depends(get_db)):
    """Get the list of articles."""
    articles = db.query(models.Article).all()
    return templates.TemplateResponse("articles.html", {"request": request, "articles": articles})


@app.get("/articles/{article_id}", response_class=HTMLResponse)
async def read_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    """Read a specific article."""
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    comments = db.query(models.Comment).filter(models.Comment.article_id == article_id).all()
    return templates.TemplateResponse("article_detail.html", {"request": request, "article": article, "comments": comments})


@app.post("/articles/{article_id}/comment", response_class=HTMLResponse)
async def create_comment(request: Request, article_id: int, author_name: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    """Add a comment to an article."""
    comment = models.Comment(article_id=article_id, author_name=author_name, content=content)
    db.add(comment)
    db.commit()
    return RedirectResponse(url=f"/articles/{article_id}", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/profile", response_class=HTMLResponse)
async def read_profile(request: Request, current_user: User = Depends(get_current_user)):
    """Display the profile of the current user."""
    user = db.query(models.User).filter(models.User.username == current_user.username).first()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
