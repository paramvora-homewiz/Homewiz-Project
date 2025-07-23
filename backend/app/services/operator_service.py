# app/services/operator_service.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..db import models
from ..models import operator as operator_models

def create_operator(db: Session, operator: operator_models.OperatorCreate) -> models.Operator:
    """
    Creates a new operator in the database.
    """
    db_operator = models.Operator(**operator.dict())
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator

def get_operator_by_id(db: Session, operator_id: int) -> Optional[models.Operator]:
    """
    Retrieves an operator from the database by their operator_id.
    """
    return db.query(models.Operator).filter(models.Operator.operator_id == operator_id).first()

def update_operator(db: Session, operator_id: int, operator_update: operator_models.OperatorUpdate) -> Optional[models.Operator]:
    """
    Updates the details of an operator in the database.
    """
    db_operator = get_operator_by_id(db, operator_id)
    if db_operator:
        for key, value in operator_update.dict(exclude_unset=True).items():
            setattr(db_operator, key, value)
        db.commit()
        db.refresh(db_operator)
        return db_operator
    return None

def delete_operator(db: Session, operator_id: int) -> bool:
    """
    Deletes an operator from the database by their operator_id.
    """
    db_operator = get_operator_by_id(db, operator_id)
    if db_operator:
        db.delete(db_operator)
        db.commit()
        return True
    return False

def get_all_operators(db: Session) -> List[models.Operator]:
    """
    Retrieves all operators from the database.
    """
    return db.query(models.Operator).all()