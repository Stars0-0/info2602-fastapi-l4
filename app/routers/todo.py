from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

todo_router = APIRouter(tags=["Todo Management"])


@todo_router.get('/todos', response_model=list[TodoResponse])
def get_todos(db:SessionDep, user:AuthDep):
    return user.todos

@todo_router.get('/todo/{id}', response_model=TodoResponse)
def get_todo_by_id(id:int, db:SessionDep, user:AuthDep):
    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return todo

@todo_router.post('/todos', response_model=TodoResponse)
def create_todo(db:SessionDep, user:AuthDep, todo_data:TodoCreate):
    todo = Todo(text=todo_data.text, user_id=user.id)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating an item",
        )

@todo_router.put('/todo/{id}', response_model=TodoResponse)
def update_todo(id:int, db:SessionDep, user:AuthDep, todo_data:TodoUpdate):
    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    if todo_data.text:
        todo.text = todo_data.text
    if todo_data.done is not None:
        todo.done = todo_data.done
    try:
        db.add(todo)
        db.commit()
        return todo
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while updating an item",
        )

@todo_router.delete('/todo/{id}', status_code=status.HTTP_200_OK)
def update_todo(id:int, db:SessionDep, user:AuthDep):

    todo = db.exec(select(Todo).where(Todo.id==id, Todo.user_id==user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    try:
        db.delete(todo)
        db.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )
        
#Exercise 2

@todo_router.post("/category", response_model=CategoryResponse)
def create_category(text: str, db: SessionDep, user: AuthDep):
    category = Category(text=text, user_id=user.id)

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category could not be created",
        )
        
        
        
@todo_router.post("/todo/{todo_id}/category/{cat_id}")
def add_category_to_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):

    todo = db.exec(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    ).one_or_none()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    category = db.exec(
        select(Category).where(Category.id == cat_id, Category.user_id == user.id)
    ).one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category in todo.categories:
        return {"message": "Category already assigned"}

    todo.categories.append(category)
    db.commit()

    return {"message": "Category added to todo"}



@todo_router.delete("/todo/{todo_id}/category/{cat_id}")
def remove_category_from_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):

    todo = db.exec(
        select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)
    ).one_or_none()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    category = db.exec(
        select(Category).where(Category.id == cat_id, Category.user_id == user.id)
    ).one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category not in todo.categories:
        raise HTTPException(status_code=400, detail="Category not assigned to todo")

    todo.categories.remove(category)
    db.commit()

    return {"message": "Category removed from todo"}


@todo_router.get("/category/{cat_id}/todos", response_model=list[TodoResponse])
def get_todos_for_category(cat_id: int, db: SessionDep, user: AuthDep):

    category = db.exec(
        select(Category).where(Category.id == cat_id, Category.user_id == user.id)
    ).one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category.todos