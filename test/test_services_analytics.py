import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, date, timedelta

from app.db.connection import Base
from app.services import analytics_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for analytics."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create test data for analytics
        building = models.Building(
            building_id="TEST_BUILDING_1",
            building_name="Test Building 1",
            full_address="123 Test St, Testville, CA 90210"
        )
        
        # Create rooms with different statuses
        room_data = [
            {"room_id": "ROOM_1", "room_number": "101", "building_id": "TEST_BUILDING_1", "status": "AVAILABLE", "ready_to_rent": True, "private_room_rent": 1500.00},
            {"room_id": "ROOM_2", "room_number": "102", "building_id": "TEST_BUILDING_1", "status": "OCCUPIED", "ready_to_rent": True, "private_room_rent": 1600.00, 
             "booked_from": date.today() - timedelta(days=30), "booked_till": date.today() + timedelta(days=335)},
            {"room_id": "ROOM_3", "room_number": "103", "building_id": "TEST_BUILDING_1", "status": "OCCUPIED", "ready_to_rent": True, "private_room_rent": 1700.00,
             "booked_from": date.today() - timedelta(days=60), "booked_till": date.today() + timedelta(days=305)},
            {"room_id": "ROOM_4", "room_number": "104", "building_id": "TEST_BUILDING_1", "status": "MAINTENANCE", "ready_to_rent": False, "private_room_rent": 1800.00},
            {"room_id": "ROOM_5", "room_number": "201", "building_id": "TEST_BUILDING_1", "status": "AVAILABLE", "ready_to_rent": True, "private_room_rent": 1900.00, 
             "shared_room_rent_2": 1200.00}
        ]
        
        # Create leads with different statuses
        lead_data = [
            {"lead_id": "LEAD_1", "email": "lead1@example.com", "status": "EXPLORING", "created_at": datetime.now() - timedelta(days=5)},
            {"lead_id": "LEAD_2", "email": "lead2@example.com", "status": "APPLICATION_SUBMITTED", "created_at": datetime.now() - timedelta(days=10),
             "lead_source": "WEBSITE"},
            {"lead_id": "LEAD_3", "email": "lead3@example.com", "status": "SHOWING_SCHEDULED", "created_at": datetime.now() - timedelta(days=7),
             "lead_source": "REFERRAL"},
            {"lead_id": "LEAD_4", "email": "lead4@example.com", "status": "LEASE_SIGNED", "created_at": datetime.now() - timedelta(days=15),
             "lead_source": "ADVERTISEMENT"},
            {"lead_id": "LEAD_5", "email": "lead5@example.com", "status": "MOVED_IN", "created_at": datetime.now() - timedelta(days=20),
             "lead_source": "WEBSITE"}
        ]
        
        # Create active tenants
        tenant_data = [
            {"tenant_id": "TENANT_1", "tenant_name": "Tenant 1", "room_id": "ROOM_2", "building_id": "TEST_BUILDING_1", 
             "tenant_email": "tenant1@example.com", "status": "ACTIVE", "lease_start_date": date.today() - timedelta(days=30), 
             "lease_end_date": date.today() + timedelta(days=335), "payment_status": "CURRENT"},
            {"tenant_id": "TENANT_2", "tenant_name": "Tenant 2", "room_id": "ROOM_3", "building_id": "TEST_BUILDING_1", 
             "tenant_email": "tenant2@example.com", "status": "ACTIVE", "lease_start_date": date.today() - timedelta(days=60), 
             "lease_end_date": date.today() + timedelta(days=305), "payment_status": "OVERDUE"}
        ]
        
        # Create maintenance requests
        maintenance_request_data = [
            {"request_id": "MAINT_1", "title": "Plumbing Issue", "description": "Leaky faucet", "room_id": "ROOM_2", 
             "building_id": "TEST_BUILDING_1", "tenant_id": "TENANT_1", "priority": "MEDIUM", "status": "PENDING", 
             "created_at": datetime.now() - timedelta(days=3)},
            {"request_id": "MAINT_2", "title": "Electrical Issue", "description": "Light not working", "room_id": "ROOM_3", 
             "building_id": "TEST_BUILDING_1", "tenant_id": "TENANT_2", "priority": "HIGH", "status": "IN_PROGRESS", 
             "assigned_to": 1, "created_at": datetime.now() - timedelta(days=5)},
            {"request_id": "MAINT_3", "title": "HVAC Issue", "description": "Heating not working", "room_id": "ROOM_2", 
             "building_id": "TEST_BUILDING_1", "tenant_id": "TENANT_1", "priority": "HIGH", "status": "COMPLETED", 
             "assigned_to": 1, "created_at": datetime.now() - timedelta(days=10), 
             "resolved_at": datetime.now() - timedelta(days=8)}
        ]
        
        # Add building
        db_session.add(building)
        db_session.commit()
        
        # Add rooms
        for room in room_data:
            db_session.add(models.Room(**room))
        db_session.commit()
        
        # Add leads
        for lead in lead_data:
            db_session.add(models.Lead(**lead))
        db_session.commit()
        
        # Add tenants
        for tenant in tenant_data:
            db_session.add(models.Tenant(**tenant))
        db_session.commit()
        
        # Add maintenance requests
        for request in maintenance_request_data:
            db_session.add(models.MaintenanceRequest(**request))
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_get_occupancy_rate(db):
    """Tests calculating current occupancy rate."""
    occupancy = analytics_service.get_occupancy_rate(db)
    
    assert "total_rooms" in occupancy
    assert "available_rooms" in occupancy
    assert "occupied_rooms" in occupancy
    assert "occupancy_rate" in occupancy
    
    # Given our test data: 2 occupied, 1 maintenance, 2 available
    assert occupancy["total_rooms"] == 5
    assert occupancy["available_rooms"] == 2
    assert occupancy["occupied_rooms"] == 2
    
    # Occupancy rate should be: (occupied / total) * 100 = (2 / 5) * 100 = 40%
    assert occupancy["occupancy_rate"] == 40.0

def test_get_occupancy_rate_with_building_filter(db):
    """Tests calculating occupancy rate for a specific building."""
    building_id = "TEST_BUILDING_1"
    occupancy = analytics_service.get_occupancy_rate(db, building_id)
    
    assert "total_rooms" in occupancy
    assert "available_rooms" in occupancy
    assert "occupied_rooms" in occupancy
    assert "occupancy_rate" in occupancy
    
    # Given our test data: 2 occupied, 1 maintenance, 2 available
    assert occupancy["total_rooms"] == 5
    assert occupancy["available_rooms"] == 2
    assert occupancy["occupied_rooms"] == 2
    assert occupancy["occupancy_rate"] == 40.0

def test_get_financial_metrics(db):
    """Tests calculating financial metrics."""
    financials = analytics_service.get_financial_metrics(db)
    
    assert "occupied_room_count" in financials
    assert "total_private_rent" in financials
    assert "avg_private_rent" in financials
    assert "estimated_monthly_revenue" in financials
    assert "period_start" in financials
    assert "period_end" in financials
    
    # Given our test data: 2 occupied rooms with rents of 1600 and 1700
    assert financials["occupied_room_count"] == 2
    assert financials["total_private_rent"] == 3300.0
    assert financials["avg_private_rent"] == 1650.0
    assert financials["estimated_monthly_revenue"] == 3300.0

def test_get_lead_conversion_metrics(db):
    """Tests calculating lead conversion metrics."""
    lead_metrics = analytics_service.get_lead_conversion_metrics(db)
    
    assert "total_leads" in lead_metrics
    assert "leads_by_status" in lead_metrics
    assert "conversion_rates" in lead_metrics
    assert "overall_conversion_rate" in lead_metrics
    assert "period_start" in lead_metrics
    assert "period_end" in lead_metrics
    
    # Given our test data
    assert lead_metrics["total_leads"] == 5
    assert lead_metrics["leads_by_status"]["EXPLORING"] == 1
    assert lead_metrics["leads_by_status"]["APPLICATION_SUBMITTED"] == 1
    assert lead_metrics["leads_by_status"]["SHOWING_SCHEDULED"] == 1
    assert lead_metrics["leads_by_status"]["LEASE_SIGNED"] == 1
    assert lead_metrics["leads_by_status"]["MOVED_IN"] == 1
    
    # Conversion rates: (count / total) * 100
    assert lead_metrics["conversion_rates"]["MOVED_IN"] == 20.0
    assert lead_metrics["overall_conversion_rate"] == 20.0

def test_get_maintenance_metrics(db):
    """Tests calculating maintenance request metrics."""
    maintenance_metrics = analytics_service.get_maintenance_metrics(db)
    
    assert "total_requests" in maintenance_metrics
    assert "requests_by_status" in maintenance_metrics
    assert "requests_by_priority" in maintenance_metrics
    assert "avg_resolution_time_hours" in maintenance_metrics
    assert "period_start" in maintenance_metrics
    assert "period_end" in maintenance_metrics
    
    # Given our test data
    assert maintenance_metrics["total_requests"] == 3
    assert maintenance_metrics["requests_by_status"]["PENDING"] == 1
    assert maintenance_metrics["requests_by_status"]["IN_PROGRESS"] == 1
    assert maintenance_metrics["requests_by_status"]["COMPLETED"] == 1
    
    assert maintenance_metrics["requests_by_priority"]["MEDIUM"] == 1
    assert maintenance_metrics["requests_by_priority"]["HIGH"] == 2
    
    # One resolved request took 2 days (48 hours)
    assert maintenance_metrics["avg_resolution_time_hours"] == 48.0

def test_get_room_performance_metrics(db):
    """Tests analyzing room performance."""
    room_metrics = analytics_service.get_room_performance_metrics(db)
    
    assert "total_rooms" in room_metrics
    assert "top_performing_rooms" in room_metrics
    assert "bottom_performing_rooms" in room_metrics
    
    # Given our test data: 5 total rooms, 2 occupied
    assert room_metrics["total_rooms"] == 5
    
    # Top rooms should be the occupied ones with highest rent/revenue
    top_rooms = room_metrics["top_performing_rooms"]
    assert len(top_rooms) > 0
    
    # Verify room IDs in top performers
    top_room_ids = [room["room_id"] for room in top_rooms]
    assert "ROOM_2" in top_room_ids or "ROOM_3" in top_room_ids
    
    # Bottom rooms should include available ones with no revenue
    bottom_rooms = room_metrics["bottom_performing_rooms"]
    assert len(bottom_rooms) > 0
    
    # Verify room IDs in bottom performers
    bottom_room_ids = [room["room_id"] for room in bottom_rooms]
    assert "ROOM_1" in bottom_room_ids or "ROOM_5" in bottom_room_ids

def test_get_tenant_metrics(db):
    """Tests analyzing tenant data."""
    tenant_metrics = analytics_service.get_tenant_metrics(db)
    
    assert "total_active_tenants" in tenant_metrics
    assert "avg_lease_duration_days" in tenant_metrics
    assert "payment_statuses" in tenant_metrics
    
    # Given our test data: 2 active tenants
    assert tenant_metrics["total_active_tenants"] == 2
    
    # Average lease duration should be 365 days (1 year)
    assert abs(tenant_metrics["avg_lease_duration_days"] - 365.0) < 5  # Allow small difference due to calculation
    
    # Payment statuses
    assert tenant_metrics["payment_statuses"]["CURRENT"] == 1
    assert tenant_metrics["payment_statuses"]["OVERDUE"] == 1

def test_get_dashboard_metrics(db):
    """Tests retrieving comprehensive dashboard metrics."""
    dashboard = analytics_service.get_dashboard_metrics(db)
    
    # Verify all expected metric categories are present
    assert "occupancy_metrics" in dashboard
    assert "financial_metrics" in dashboard
    assert "lead_metrics" in dashboard
    assert "maintenance_metrics" in dashboard
    assert "room_metrics" in dashboard
    assert "tenant_metrics" in dashboard
    assert "timestamp" in dashboard
    
    # Verify some key metrics from each category
    assert dashboard["occupancy_metrics"]["occupancy_rate"] == 40.0
    assert dashboard["financial_metrics"]["estimated_monthly_revenue"] == 3300.0
    assert dashboard["lead_metrics"]["total_leads"] == 5
    assert dashboard["maintenance_metrics"]["total_requests"] == 3
    assert dashboard["room_metrics"]["total_rooms"] == 5
    assert dashboard["tenant_metrics"]["total_active_tenants"] == 2

def test_get_lead_source_analysis(db):
    """Tests analyzing lead sources."""
    lead_sources = analytics_service.get_lead_source_analysis(db)
    
    assert "lead_sources" in lead_sources
    assert "total_leads_with_source" in lead_sources
    assert "period_start" in lead_sources
    assert "period_end" in lead_sources
    
    # Given our test data: 4 leads with sources (2 WEBSITE, 1 REFERRAL, 1 ADVERTISEMENT)
    assert lead_sources["total_leads_with_source"] == 4
    
    # Verify lead sources
    sources = lead_sources["lead_sources"]
    assert "WEBSITE" in sources
    assert "REFERRAL" in sources
    assert "ADVERTISEMENT" in sources
    
    # Verify counts and conversion rates
    assert sources["WEBSITE"]["total"] == 2
    assert sources["REFERRAL"]["total"] == 1
    assert sources["ADVERTISEMENT"]["total"] == 1
    
    # WEBSITE: 1 moved in out of 2 = 50%
    assert sources["WEBSITE"]["converted"] == 1
    assert sources["WEBSITE"]["conversion_rate"] == 50.0

def test_get_occupancy_history(db):
    """Tests retrieving historical occupancy data."""
    history = analytics_service.get_occupancy_history(db)
    
    assert "occupancy_history" in history
    assert "current_occupancy" in history
    
    # Verify current occupancy matches our other test
    assert history["current_occupancy"]["occupancy_rate"] == 40.0
    
    # Verify history has the right structure
    assert len(history["occupancy_history"]) > 0
    
    first_entry = history["occupancy_history"][0]
    assert "month" in first_entry
    assert "occupancy_rate" in first_entry
    
    # History should be in chronological order
    if len(history["occupancy_history"]) > 1:
        months = [entry["month"] for entry in history["occupancy_history"]]
        assert months == sorted(months)