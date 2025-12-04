# FastApi user routes
from fastapi import APIRouter, Depends, HTTPException, Query

from typing import Optional

from backend.db.schema import SessionLocal
from backend.services.user_auth_service import get_current_active_user
from backend.services.task_service import TaskService
from backend.models.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter()


def get_task_service():
    """Dependency to get TaskService with proper session management"""
    session = SessionLocal()
    try:
        yield TaskService(session=session)
    finally:
        session.close()


@router.get("/tasks", response_model=list[TaskRead])
def get_tasks(current_user = Depends(get_current_active_user), service: TaskService = Depends(get_task_service)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return service.list_tasks(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/categories", response_model=list[str])
def get_categories(current_user = Depends(get_current_active_user), service: TaskService = Depends(get_task_service)):
    return service.get_categories(current_user.id)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, current_user = Depends(get_current_active_user), service: TaskService = Depends(get_task_service)):
    task = service.get_task(current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, service: TaskService = Depends(get_task_service)):
    new_task = service.create_task(payload)
    if not new_task:
        raise HTTPException(status_code=404, detail="Did not create task")
    return new_task


@router.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, current_user = Depends(get_current_active_user), service: TaskService = Depends(get_task_service)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # Convert TaskUpdate to dict, filtering out None values
        update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
        updated_task = service.update_task(current_user.id, task_id, update_data)
        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found or not owned by you")
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/complete", response_model=TaskRead)
def mark_task_complete(task_id: int, current_user = Depends(get_current_active_user), service: TaskService = Depends(get_task_service)):
    updated = service.mark_task_complete(current_user.id, task_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found or owned by you")
    task = service.get_task(current_user.id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task updated but not retrievable")
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, current_user = Depends(get_current_active_user), service: TaskService = Depends(get_task_service)):
    removed = service.remove_task(current_user.id, task_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Task not found or not owned by you")
    return None

