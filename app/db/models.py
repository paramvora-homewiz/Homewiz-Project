from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from .connection import Base
class Operator(Base):
    __tablename__ = "operators"

    operator_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String)
    role = Column(String)
    active = Column(Boolean, default=True)
    date_joined = Column(Date)
    last_active = Column(Date)
    operator_type = Column(String, default="LEASING_AGENT")  # 'LEASING_AGENT', 'MAINTENANCE', 'BUILDING_MANAGER', 'ADMIN'
    permissions = Column(String)  # JSON string of permission flags
    notification_preferences = Column(String, default="EMAIL")  # 'EMAIL', 'SMS', 'BOTH', 'NONE'
    working_hours = Column(String)  # JSON string of working hours
    emergency_contact = Column(Boolean, default=False)  # Whether this operator can be contacted in emergencies
    calendar_sync_enabled = Column(Boolean, default=False)
    calendar_external_id = Column(String)  # ID for external calendar integration

    buildings = relationship("Building", back_populates="operator")
    rooms_checked = relationship("Room", back_populates="checked_by_operator", foreign_keys="[Room.last_check_by]")


class Building(Base):
    __tablename__ = "buildings"

    building_id = Column(String, primary_key=True, index=True)
    building_name = Column(String, nullable=False)
    full_address = Column(String)
    operator_id = Column(Integer, ForeignKey("operators.operator_id"))
    available = Column(Boolean, default=True)
    street = Column(String)
    area = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(String)
    floors = Column(Integer)
    total_rooms = Column(Integer)
    total_bathrooms = Column(Integer)
    bathrooms_on_each_floor = Column(Integer)
    common_kitchen = Column(String)
    min_lease_term = Column(Integer)
    pref_min_lease_term = Column(Integer)
    wifi_included = Column(Boolean, default=False)
    laundry_onsite = Column(Boolean, default=False)
    common_area = Column(String)
    secure_access = Column(Boolean, default=False)
    bike_storage = Column(Boolean, default=False)
    rooftop_access = Column(Boolean, default=False)
    pet_friendly = Column(String)
    cleaning_common_spaces = Column(String)
    utilities_included = Column(Boolean, default=False)
    fitness_area = Column(Boolean, default=False)
    work_study_area = Column(Boolean, default=False)
    social_events = Column(Boolean, default=False)
    nearby_conveniences_walk = Column(String)
    nearby_transportation = Column(String)
    priority = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    last_modified = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    property_manager = Column(Integer, ForeignKey("operators.operator_id"))
    year_built = Column(Integer)
    last_renovation = Column(Integer)
    building_rules = Column(String)
    amenities_details = Column(String)  # JSON string of detailed amenities info
    neighborhood_description = Column(String)
    building_description = Column(String)
    public_transit_info = Column(String)
    parking_info = Column(String)
    security_features = Column(String)
    disability_access = Column(Boolean, default=False)
    disability_features = Column(String)
    building_images = Column(String)  # JSON array of image URLs or references
    virtual_tour_url = Column(String)

    operator = relationship("Operator", back_populates="buildings")
    rooms = relationship("Room", back_populates="building")
    tenants = relationship("Tenant", back_populates="building")


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String, primary_key=True, index=True)
    room_number = Column(String, nullable=False)
    building_id = Column(String, ForeignKey("buildings.building_id"))
    ready_to_rent = Column(Boolean, default=True)
    status = Column(String, default="AVAILABLE")
    booked_from = Column(Date)
    booked_till = Column(Date)
    active_tenants = Column(Integer, default=0)
    maximum_people_in_room = Column(Integer)
    private_room_rent = Column(Float)
    shared_room_rent_2 = Column(Float)
    last_check = Column(Date)
    last_check_by = Column(Integer, ForeignKey("operators.operator_id"))
    current_booking_types = Column(String)
    floor_number = Column(Integer)
    bed_count = Column(Integer)
    bathroom_type = Column(String)
    bed_size = Column(String)
    bed_type = Column(String)
    view = Column(String)
    sq_footage = Column(Integer)
    mini_fridge = Column(Boolean, default=False)
    sink = Column(Boolean, default=False)
    bedding_provided = Column(Boolean, default=False)
    work_desk = Column(Boolean, default=False)
    work_chair = Column(Boolean, default=False)
    heating = Column(Boolean, default=False)
    air_conditioning = Column(Boolean, default=False)
    cable_tv = Column(Boolean, default=False)
    room_storage = Column(String)
    last_modified = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    noise_level = Column(String)  # 'QUIET', 'MODERATE', 'LIVELY'
    sunlight = Column(String)  # 'BRIGHT', 'MODERATE', 'LOW'
    furnished = Column(Boolean, default=False)
    furniture_details = Column(String)
    last_renovation_date = Column(Date)
    public_notes = Column(String)  # For listing descriptions
    internal_notes = Column(String)  # For staff only
    virtual_tour_url = Column(String)
    available_from = Column(Date)
    additional_features = Column(String)

    building = relationship("Building", back_populates="rooms")
    tenants = relationship("Tenant", back_populates="room")
    leads = relationship("Lead", back_populates="selected_room")
    checked_by_operator = relationship("Operator", back_populates="rooms_checked", foreign_keys=[last_check_by])


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True, index=True)
    tenant_name = Column(String, nullable=False)
    room_id = Column(String, ForeignKey("rooms.room_id"))
    room_number = Column(String)
    lease_start_date = Column(Date)
    lease_end_date = Column(Date)
    operator_id = Column(Integer, ForeignKey("operators.operator_id"))
    booking_type = Column(String)
    tenant_nationality = Column(String)
    tenant_email = Column(String, unique=True, index=True)
    phone = Column(String)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    emergency_contact_relation = Column(String)
    building_id = Column(String, ForeignKey("buildings.building_id"))
    status = Column(String, default="ACTIVE")
    deposit_amount = Column(Float)
    payment_status = Column(String)
    special_requests = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    last_modified = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    payment_reminders_enabled = Column(Boolean, default=True)
    communication_preferences = Column(String, default="EMAIL")  # 'EMAIL', 'SMS', 'BOTH'
    account_status = Column(String, default="ACTIVE")  # 'ACTIVE', 'INACTIVE', 'PENDING'
    last_payment_date = Column(Date)
    next_payment_date = Column(Date)
    rent_payment_method = Column(String)
    has_pets = Column(Boolean, default=False)
    pet_details = Column(String)
    has_vehicles = Column(Boolean, default=False)
    vehicle_details = Column(String)
    has_renters_insurance = Column(Boolean, default=False)
    insurance_details = Column(String)

    room = relationship("Room", back_populates="tenants")
    building = relationship("Building", back_populates="tenants")
    operator = relationship("Operator", backref="tenants") # Using backref here for simplicity


class Lead(Base):
    __tablename__ = "leads"

    lead_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False)
    interaction_count = Column(Integer, default=0)
    rooms_interested = Column(String) # JSON array as String
    selected_room_id = Column(String, ForeignKey("rooms.room_id"))
    showing_dates = Column(String) # JSON array as String
    planned_move_in = Column(Date)
    planned_move_out = Column(Date)
    visa_status = Column(String)
    notes = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    last_modified = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    lead_score = Column(Integer, default=0)
    lead_source = Column(String)  # 'WEBSITE', 'REFERRAL', 'ADVERTISEMENT', etc.
    preferred_communication = Column(String, default="EMAIL")  # 'EMAIL', 'SMS', 'PHONE'
    budget_min = Column(Float)
    budget_max = Column(Float)
    preferred_move_in_date = Column(Date)
    preferred_lease_term = Column(Integer)  # in months
    additional_preferences = Column(String)  # JSON string of additional preferences
    last_contacted = Column(TIMESTAMP(timezone=True))
    next_follow_up = Column(TIMESTAMP(timezone=True))

    selected_room = relationship("Room", back_populates="leads")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String, primary_key=True, index=True)
    user_type = Column(String, nullable=False)  # 'tenant', 'lead', 'operator'
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'maintenance', 'lease', 'application', etc.
    status = Column(String, default="UNREAD")
    priority = Column(String, default="NORMAL")  # 'HIGH', 'NORMAL', 'LOW'
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    read_at = Column(TIMESTAMP(timezone=True))

class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"

    event_id = Column(String, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # 'showing', 'maintenance', 'move-in', 'move-out'
    title = Column(String, nullable=False)
    description = Column(String)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String, default="SCHEDULED")  # 'SCHEDULED', 'CONFIRMED', 'CANCELLED', 'COMPLETED'
    
    # Relations - may be null depending on event type
    room_id = Column(String, ForeignKey("rooms.room_id"))
    building_id = Column(String, ForeignKey("buildings.building_id"))
    operator_id = Column(Integer, ForeignKey("operators.operator_id"))
    lead_id = Column(String, ForeignKey("leads.lead_id"))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"))
    
    # Relationship definitions
    room = relationship("Room", backref="scheduled_events")
    building = relationship("Building", backref="scheduled_events")
    operator = relationship("Operator", backref="scheduled_events")
    lead = relationship("Lead", backref="scheduled_events")
    tenant = relationship("Tenant", backref="scheduled_events")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    last_modified = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    request_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    priority = Column(String, default="MEDIUM")  # 'HIGH', 'MEDIUM', 'LOW', 'EMERGENCY'
    status = Column(String, default="PENDING")  # 'PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
    
    # Relations
    room_id = Column(String, ForeignKey("rooms.room_id"), nullable=False)
    building_id = Column(String, ForeignKey("buildings.building_id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("operators.operator_id"))
    
    # Relationship definitions
    room = relationship("Room", backref="maintenance_requests")
    building = relationship("Building", backref="maintenance_requests")
    tenant = relationship("Tenant", backref="maintenance_requests")
    operator = relationship("Operator", backref="assigned_maintenance_requests", foreign_keys=[assigned_to])
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    resolved_at = Column(TIMESTAMP(timezone=True))

class Checklist(Base):
    __tablename__ = "checklists"

    checklist_id = Column(String, primary_key=True, index=True)
    checklist_type = Column(String, nullable=False)  # 'MOVE_IN', 'MOVE_OUT', 'INSPECTION'
    status = Column(String, default="PENDING")  # 'PENDING', 'IN_PROGRESS', 'COMPLETED'
    
    # Relations
    room_id = Column(String, ForeignKey("rooms.room_id"), nullable=False)
    building_id = Column(String, ForeignKey("buildings.building_id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"))
    operator_id = Column(Integer, ForeignKey("operators.operator_id"))
    
    # Relationship definitions
    room = relationship("Room", backref="checklists")
    building = relationship("Building", backref="checklists")
    tenant = relationship("Tenant", backref="checklists")
    operator = relationship("Operator", backref="assigned_checklists")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    completed_at = Column(TIMESTAMP(timezone=True))

class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    item_id = Column(String, primary_key=True, index=True)
    checklist_id = Column(String, ForeignKey("checklists.checklist_id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="PENDING")  # 'PENDING', 'COMPLETED', 'SKIPPED'
    notes = Column(String)
    
    # Relationship definition
    checklist = relationship("Checklist", backref="items")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    completed_at = Column(TIMESTAMP(timezone=True))

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    document_type = Column(String, nullable=False)  # 'LEASE', 'APPLICATION', 'AGREEMENT', etc.
    content = Column(String)  # Could store JSON, HTML, or reference to external storage
    status = Column(String, default="DRAFT")  # 'DRAFT', 'PENDING_SIGNATURE', 'SIGNED', 'CANCELLED'
    
    # Relations - may be null depending on document type
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"))
    lead_id = Column(String, ForeignKey("leads.lead_id"))
    room_id = Column(String, ForeignKey("rooms.room_id"))
    building_id = Column(String, ForeignKey("buildings.building_id"))
    
    # Relationship definitions
    tenant = relationship("Tenant", backref="documents")
    lead = relationship("Lead", backref="documents")
    room = relationship("Room", backref="documents")
    building = relationship("Building", backref="documents")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    signed_at = Column(TIMESTAMP(timezone=True))

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True, index=True)
    content = Column(String, nullable=False)
    message_type = Column(String, default="TEXT")  # 'TEXT', 'EMAIL', 'SMS', 'NOTIFICATION'
    status = Column(String, default="SENT")  # 'SENT', 'DELIVERED', 'READ', 'FAILED'
    
    # Sender information
    sender_type = Column(String, nullable=False)  # 'SYSTEM', 'OPERATOR', 'TENANT', 'LEAD'
    sender_id = Column(String)  # May be null for SYSTEM messages
    
    # Recipient information
    recipient_type = Column(String, nullable=False)  # 'OPERATOR', 'TENANT', 'LEAD', 'ALL'
    recipient_id = Column(String)  # May be null for broadcasts
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    delivered_at = Column(TIMESTAMP(timezone=True))
    read_at = Column(TIMESTAMP(timezone=True))

class BuildingAnnouncement(Base):
    __tablename__ = "building_announcements"

    announcement_id = Column(String, primary_key=True, index=True)
    building_id = Column(String, ForeignKey("buildings.building_id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    priority = Column(String, default="NORMAL")  # 'HIGH', 'NORMAL', 'LOW'
    
    # Relationship definition
    building = relationship("Building", backref="announcements")
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    expires_at = Column(TIMESTAMP(timezone=True))