# app/endpoints/operators.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import operator_service
from ..db.connection import get_db
from ..models import operator as operator_models  # Import Pydantic models

router = APIRouter()

@router.post("/operators/", response_model=operator_models.Operator, status_code=201)
def create_operator(operator: operator_models.OperatorCreate, db: Session = Depends(get_db)):
    """
    Create a new operator (property manager/staff).
    """
    db_operator = operator_service.create_operator(db=db, operator=operator)
    return db_operator

@router.get("/operators/{operator_id}", response_model=operator_models.Operator)
def read_operator(operator_id: int, db: Session = Depends(get_db)):
    """
    Get operator by ID.
    """
    db_operator = operator_service.get_operator_by_id(db, operator_id=operator_id)
    if db_operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    return db_operator

@router.put("/operators/{operator_id}", response_model=operator_models.Operator)
def update_operator(operator_id: int, operator_update: operator_models.OperatorUpdate, db: Session = Depends(get_db)):
    """
    Update operator by ID.
    """
    db_operator = operator_service.update_operator(db, operator_id=operator_id, operator_update=operator_update)
    if db_operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    return db_operator

@router.delete("/operators/{operator_id}", status_code=204)
def delete_operator(operator_id: int, db: Session = Depends(get_db)):
    """
    Delete operator by ID.
    """
    db_operator = operator_service.get_operator_by_id(db, operator_id=operator_id)
    if db_operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    operator_service.delete_operator(db, operator_id=operator_id)
    return {"ok": True}

@router.get("/operators/", response_model=List[operator_models.Operator])
def read_operators(db: Session = Depends(get_db)):
    """
    Get all operators.
    """
    operators_list = operator_service.get_all_operators(db)
    return operators_list