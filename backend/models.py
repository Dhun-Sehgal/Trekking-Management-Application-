from datetime import datetime
from app import db, bcrypt

ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLE_USER = "trekker"
ROLES = (ROLE_ADMIN, ROLE_STAFF, ROLE_USER)

DIFFICULTY_CHOICES = ("Easy", "Moderate", "Hard")

TREK_STATUS_PENDING = "Pending"
TREK_STATUS_APPROVED = "Approved"
TREK_STATUS_OPEN = "Open"
TREK_STATUS_CLOSED = "Closed"
TREK_STATUS_COMPLETED = "Completed"
TREK_STATUSES = (
    TREK_STATUS_PENDING,
    TREK_STATUS_APPROVED,
    TREK_STATUS_OPEN,
    TREK_STATUS_CLOSED,
    TREK_STATUS_COMPLETED,
)

BOOKING_STATUS_BOOKED = "Booked"
BOOKING_STATUS_CANCELLED = "Cancelled"
BOOKING_STATUS_COMPLETED = "Completed"
BOOKING_STATUSES = (BOOKING_STATUS_BOOKED, BOOKING_STATUS_CANCELLED, BOOKING_STATUS_COMPLETED)


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_USER)
    phone = db.Column(db.String(20))

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    staff_status = db.Column(db.String(20), default="Active")

    assigned_treks = db.relationship("Trek", backref="assigned_staff", foreign_keys="Trek.assigned_staff_id")
    bookings = db.relationship("Booking", backref="user", foreign_keys="Booking.user_id")

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_blacklisted": self.is_blacklisted,
            "staff_status": self.staff_status if self.role == ROLE_STAFF else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Easy")
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    total_slots = db.Column(db.Integer, nullable=False, default=10)
    available_slots = db.Column(db.Integer, nullable=False, default=10)

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=TREK_STATUS_PENDING)

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship("Booking", backref="trek", foreign_keys="Booking.trek_id",cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "difficulty": self.difficulty,
            "duration_days": self.duration_days,
            "total_slots": self.total_slots,
            "available_slots": self.available_slots,
            "assigned_staff_id": self.assigned_staff_id,
            "assigned_staff_name": self.assigned_staff.name if self.assigned_staff else None,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "registered_count": Booking.query.filter_by(
                trek_id=self.id, status=BOOKING_STATUS_BOOKED
            ).count(),
        }


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default=BOOKING_STATUS_BOOKED)
    payment_status = db.Column(db.String(20), default="NA")

    __table_args__ = (db.UniqueConstraint("user_id", "trek_id", name="uq_user_trek_booking"),)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "trek_id": self.trek_id,
            "trek_name": self.trek.name if self.trek else None,
            "trek_location": self.trek.location if self.trek else None,
            "booking_date": self.booking_date.isoformat() if self.booking_date else None,
            "status": self.status,
            "payment_status": self.payment_status,
            "trek_start_date": self.trek.start_date.isoformat()
            if self.trek and self.trek.start_date
            else None,
        }
