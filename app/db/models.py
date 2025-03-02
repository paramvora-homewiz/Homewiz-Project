from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, TIMESTAMP, text
from sqlalchemy.orm import relationship

from db.connection import Base

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

    selected_room = relationship("Room", back_populates="leads")