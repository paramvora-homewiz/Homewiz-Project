from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import maintenance_service
from ..db.connection import get_db
from ..models import maintenance_request as maintenance_models

router = APIRouter()

@router.post("/maintenance-requests/", response_model=maintenance_models.MaintenanceRequest, status_code=201)
def create_maintenance_request(request: maintenance_models.MaintenanceRequestCreate, db: Session = Depends(get_db)):
    """
    Create a new maintenance request.
    """
    db_request = maintenance_service.create_maintenance_request(
        db=db,
        title=request.title,
        description=request.description,
        room_id=request.room_id,
        building_id=request.building_id,
        tenant_id=request.tenant_id,
        priority=request.priority,
        assigned_to=request.assigned_to
    )
    return db_request

@router.get("/maintenance-requests/{request_id}", response_model=maintenance_models.MaintenanceRequest)
def read_maintenance_request(request_id: str, db: Session = Depends(get_db)):
    """
    Get maintenance request by ID.
    """
    db_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request_id)
    if db_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return db_request

@router.put("/maintenance-requests/{request_id}/status", response_model=maintenance_models.MaintenanceRequest)
def update_maintenance_request_status(
    request_id: str, 
    status_update: dict, 
    db: Session = Depends(get_db)
):
    """
    Update the status of a maintenance request.
    """
    db_request = maintenance_service.update_maintenance_request_status(
        db=db,
        request_id=request_id,
        status=status_update["status"],
        notes=status_update.get("notes")
    )
    if db_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return db_request

@router.put("/maintenance-requests/{request_id}/assign", response_model=maintenance_models.MaintenanceRequest)
def assign_maintenance_request(request_id: str, operator_id: int, db: Session = Depends(get_db)):
    """
    Assign a maintenance request to an operator.
    """
    db_request = maintenance_service.assign_maintenance_request(
        db=db,
        request_id=request_id,
        operator_id=operator_id
    )
    if db_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return db_request

@router.put("/maintenance-requests/{request_id}", response_model=maintenance_models.MaintenanceRequest)
def update_maintenance_request(
    request_id: str, 
    request_update: maintenance_models.MaintenanceRequestUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update maintenance request details.
    """
    db_request = maintenance_service.update_maintenance_request(
        db=db,
        request_id=request_id,
        update_data=request_update.dict(exclude_unset=True)
    )
    if db_request is None:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return db_request

@router.delete("/maintenance-requests/{request_id}", status_code=204)
def delete_maintenance_request(request_id: str, db: Session = Depends(get_db)):
    """
    Delete maintenance request by ID.
    """
    success = maintenance_service.delete_maintenance_request(db, request_id=request_id)
    if not success:
        raise HTTPException(status_code=404, detail="Maintenance request not found")
    return {"ok": True}

@router.get("/tenants/{tenant_id}/maintenance-requests/", response_model=List[maintenance_models.MaintenanceRequest])
def read_tenant_maintenance_requests(
    tenant_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get maintenance requests for a specific tenant.
    """
    requests = maintenance_service.get_tenant_maintenance_requests(
        db=db,
        tenant_id=tenant_id,
        status=status,
        limit=limit
    )
    return requests

@router.get("/buildings/{building_id}/maintenance-requests/", response_model=List[maintenance_models.MaintenanceRequest])
def read_building_maintenance_requests(
    building_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get maintenance requests for a specific building.
    """
    requests = maintenance_service.get_building_maintenance_requests(
        db=db,
        building_id=building_id,
        status=status,
        limit=limit
    )
    return requests

@router.get("/operators/{operator_id}/maintenance-requests/", response_model=List[maintenance_models.MaintenanceRequest])
def read_operator_maintenance_requests(
    operator_id: int,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get maintenance requests assigned to a specific operator.
    """
    requests = maintenance_service.get_operator_maintenance_requests(
        db=db,
        operator_id=operator_id,
        status=status,
        limit=limit
    )
    return requests

@router.get("/maintenance-requests/by-priority/{priority}", response_model=List[maintenance_models.MaintenanceRequest])
def read_maintenance_requests_by_priority(
    priority: str,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get maintenance requests by priority.
    """
    requests = maintenance_service.get_maintenance_requests_by_priority(
        db=db,
        priority=priority,
        status=status,
        limit=limit
    )
    return requests

@router.get("/maintenance-requests/unassigned/", response_model=List[maintenance_models.MaintenanceRequest])
def read_unassigned_maintenance_requests(
    building_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get unassigned maintenance requests.
    """
    requests = maintenance_service.get_unassigned_maintenance_requests(
        db=db,
        building_id=building_id,
        limit=limit
    )
    return requests