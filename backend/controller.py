from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request,
)
from sqlalchemy import or_, func, desc

from app import db, get_redis
from models import (
    User,
    Trek,
    Booking,
    ROLE_ADMIN,
    ROLE_STAFF,
    ROLE_USER,
    TREK_STATUSES,
    TREK_STATUS_OPEN,
    DIFFICULTY_CHOICES,
    BOOKING_STATUS_BOOKED,
    BOOKING_STATUS_CANCELLED,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

# RBAC decorator

def roles_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role privileges"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _current_uid():
    return int(get_jwt_identity())


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

# redis
import json


def _cache_get(key):
    r = get_redis()
    if r is None:
        return None
    val = r.get(key)
    if val is None:
        return None
    try:
        return json.loads(val)
    except (TypeError, ValueError):
        return None


def _cache_set(key, value, ttl=None):
    r = get_redis()
    if r is None:
        return
    ttl = ttl or current_app.config.get("CACHE_TTL_SECONDS", 60)
    r.setex(key, ttl, json.dumps(value))


def _invalidate_trek_caches():
    r = get_redis()
    if r is None:
        return
    for key in r.scan_iter(match="cache:treks:*"):
        r.delete(key)



# AUTH

@api_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(name=name, email=email, phone=phone, role=ROLE_USER)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@api_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    if user.is_blacklisted:
        return jsonify({"error": "This account has been blacklisted. Contact admin."}), 403
    if not user.is_active:
        return jsonify({"error": "This account has been deactivated. Contact admin."}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role, "name": user.name})
    return jsonify({"access_token": token, "user": user.to_dict()}), 200


@api_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(_current_uid())
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict(), "role": get_jwt().get("role")}), 200


# ADMIN

@api_bp.route("/admin/dashboard", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_dashboard():
    return jsonify(
        {
            "total_treks": Trek.query.count(),
            "total_users": User.query.filter_by(role=ROLE_USER).count(),
            "total_staff": User.query.filter_by(role=ROLE_STAFF).count(),
            "total_bookings": Booking.query.count(),
            "open_treks": Trek.query.filter_by(status="Open").count(),
            "completed_treks": Trek.query.filter_by(status="Completed").count(),
        }
    )


@api_bp.route("/admin/treks", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_list_treks():
    treks = Trek.query.order_by(Trek.created_at.desc()).all()
    return jsonify({"treks": [t.to_dict() for t in treks]})


@api_bp.route("/admin/treks", methods=["POST"])
@roles_required(ROLE_ADMIN)
def admin_create_trek():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    location = (data.get("location") or "").strip()
    difficulty = data.get("difficulty", "Easy")
    duration_days = data.get("duration_days", 1)
    total_slots = data.get("total_slots", 10)

    if not name or not location:
        return jsonify({"error": "name and location are required"}), 400
    if difficulty not in DIFFICULTY_CHOICES:
        return jsonify({"error": f"difficulty must be one of {DIFFICULTY_CHOICES}"}), 400

    trek = Trek(
        name=name,
        location=location,
        difficulty=difficulty,
        duration_days=int(duration_days),
        total_slots=int(total_slots),
        available_slots=int(total_slots),
        description=data.get("description", ""),
        start_date=_parse_date(data.get("start_date")),
        end_date=_parse_date(data.get("end_date")),
        status="Pending",
    )
    db.session.add(trek)
    db.session.commit()
    _invalidate_trek_caches()
    return jsonify({"message": "Trek created", "trek": trek.to_dict()}), 201


@api_bp.route("/admin/treks/<int:trek_id>", methods=["PUT"])
@roles_required(ROLE_ADMIN)
def admin_update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json(force=True, silent=True) or {}

    for field in ("name", "location", "difficulty", "description"):
        if field in data:
            setattr(trek, field, data[field])

    if "duration_days" in data:
        trek.duration_days = int(data["duration_days"])

    if "total_slots" in data:
        new_total = int(data["total_slots"])
        booked = trek.total_slots - trek.available_slots
        trek.total_slots = new_total
        trek.available_slots = max(new_total - booked, 0)

    if "start_date" in data:
        trek.start_date = _parse_date(data["start_date"])
    if "end_date" in data:
        trek.end_date = _parse_date(data["end_date"])

    if "status" in data:
        if data["status"] not in TREK_STATUSES:
            return jsonify({"error": f"status must be one of {TREK_STATUSES}"}), 400
        trek.status = data["status"]

    db.session.commit()
    _invalidate_trek_caches()
    return jsonify({"message": "Trek updated", "trek": trek.to_dict()})


@api_bp.route("/admin/treks/<int:trek_id>", methods=["DELETE"])
@roles_required(ROLE_ADMIN)
def admin_delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    _invalidate_trek_caches()
    return jsonify({"message": "Trek deleted"})


@api_bp.route("/admin/treks/<int:trek_id>/assign-staff", methods=["PUT"])
@roles_required(ROLE_ADMIN)
def admin_assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json(force=True, silent=True) or {}
    staff = User.query.filter_by(id=data.get("staff_id"), role=ROLE_STAFF).first()
    if not staff:
        return jsonify({"error": "Valid staff_id is required"}), 400

    trek.assigned_staff_id = staff.id
    if trek.status == "Pending":
        trek.status = "Approved"
    db.session.commit()
    _invalidate_trek_caches()
    return jsonify({"message": f"{staff.name} assigned to {trek.name}", "trek": trek.to_dict()})


@api_bp.route("/admin/staff", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_list_staff():
    staff = User.query.filter_by(role=ROLE_STAFF).order_by(User.created_at.desc()).all()
    return jsonify({"staff": [s.to_dict() for s in staff]})


@api_bp.route("/admin/staff", methods=["POST"])
@roles_required(ROLE_ADMIN)
def admin_create_staff():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    staff = User(name=name, email=email, phone=phone, role=ROLE_STAFF)
    staff.set_password(password)
    db.session.add(staff)
    db.session.commit()
    return jsonify({"message": "Staff created", "staff": staff.to_dict()}), 201


@api_bp.route("/admin/users", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_list_users():
    users = User.query.filter_by(role=ROLE_USER).order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@api_bp.route("/admin/users/<int:user_id>/deactivate", methods=["PUT"])
@roles_required(ROLE_ADMIN)
def admin_deactivate_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == ROLE_ADMIN:
        return jsonify({"error": "Cannot deactivate the admin account"}), 400
    data = request.get_json(force=True, silent=True) or {}
    user.is_active = bool(data.get("is_active", not user.is_active))
    db.session.commit()
    return jsonify({"message": "User status updated", "user": user.to_dict()})


@api_bp.route("/admin/users/<int:user_id>/blacklist", methods=["PUT"])
@roles_required(ROLE_ADMIN)
def admin_blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == ROLE_ADMIN:
        return jsonify({"error": "Cannot blacklist the admin account"}), 400
    data = request.get_json(force=True, silent=True) or {}
    user.is_blacklisted = bool(data.get("is_blacklisted", not user.is_blacklisted))
    db.session.commit()
    return jsonify({"message": "User blacklist status updated", "user": user.to_dict()})


@api_bp.route("/admin/bookings", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_all_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return jsonify({"bookings": [b.to_dict() for b in bookings]})


@api_bp.route("/admin/search", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_search():
    q = (request.args.get("q") or "").strip()
    entity = (request.args.get("type") or "all").lower()
    like = f"%{q}%"

    result = {}
    if entity in ("all", "users"):
        result["users"] = [
            u.to_dict()
            for u in User.query.filter(User.role == ROLE_USER, or_(User.name.ilike(like), User.email.ilike(like))).all()
        ]
    if entity in ("all", "staff"):
        result["staff"] = [
            s.to_dict()
            for s in User.query.filter(User.role == ROLE_STAFF, or_(User.name.ilike(like), User.email.ilike(like))).all()
        ]
    if entity in ("all", "treks"):
        result["treks"] = [
            t.to_dict() for t in Trek.query.filter(or_(Trek.name.ilike(like), Trek.location.ilike(like))).all()
        ]
    return jsonify(result)


@api_bp.route("/admin/reports", methods=["GET"])
@roles_required(ROLE_ADMIN)
def admin_reports():
    treks = Trek.query.all()
    by_status, by_difficulty = {}, {}
    for t in treks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_difficulty[t.difficulty] = by_difficulty.get(t.difficulty, 0) + 1

    popular = (
        db.session.query(Trek.name, func.count(Booking.id).label("cnt"))
        .join(Booking, Booking.trek_id == Trek.id)
        .group_by(Trek.id)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "treks_by_status": by_status,
            "treks_by_difficulty": by_difficulty,
            "most_popular_treks": [{"name": n, "bookings": c} for n, c in popular],
            "total_bookings": Booking.query.count(),
            "total_completed_treks": Trek.query.filter_by(status="Completed").count(),
        }
    )



# STAFF
@api_bp.route("/staff/dashboard", methods=["GET"])
@roles_required(ROLE_STAFF)
def staff_dashboard():
    staff_id = _current_uid()
    treks = Trek.query.filter_by(assigned_staff_id=staff_id).all()
    per_trek = [
        {
            "trek_id": t.id,
            "trek_name": t.name,
            "registered_count": Booking.query.filter_by(trek_id=t.id, status=BOOKING_STATUS_BOOKED).count(),
        }
        for t in treks
    ]
    return jsonify(
        {
            "assigned_trek_count": len(treks),
            "assigned_treks": [t.to_dict() for t in treks],
            "registrations_per_trek": per_trek,
        }
    )


@api_bp.route("/staff/treks", methods=["GET"])
@roles_required(ROLE_STAFF)
def staff_my_treks():
    treks = Trek.query.filter_by(assigned_staff_id=_current_uid()).order_by(Trek.created_at.desc()).all()
    return jsonify({"treks": [t.to_dict() for t in treks]})


def _get_owned_trek_or_error(trek_id, staff_id):
    trek = Trek.query.get(trek_id)
    if not trek:
        return None, (jsonify({"error": "Trek not found"}), 404)
    if trek.assigned_staff_id != staff_id:
        return None, (jsonify({"error": "You are not assigned to this trek"}), 403)
    return trek, None


@api_bp.route("/staff/treks/<int:trek_id>", methods=["PUT"])
@roles_required(ROLE_STAFF)
def staff_update_trek(trek_id):
    trek, err = _get_owned_trek_or_error(trek_id, _current_uid())
    if err:
        return err
    data = request.get_json(force=True, silent=True) or {}

    if "available_slots" in data:
        new_available = int(data["available_slots"])
        if new_available < 0 or new_available > trek.total_slots:
            return jsonify({"error": "available_slots out of valid range"}), 400
        trek.available_slots = new_available

    if "status" in data:
        if data["status"] not in TREK_STATUSES:
            return jsonify({"error": f"status must be one of {TREK_STATUSES}"}), 400
        trek.status = data["status"]

    db.session.commit()
    _invalidate_trek_caches()
    return jsonify({"message": "Trek updated", "trek": trek.to_dict()})


@api_bp.route("/staff/treks/<int:trek_id>/participants", methods=["GET"])
@roles_required(ROLE_STAFF)
def staff_participants(trek_id):
    trek, err = _get_owned_trek_or_error(trek_id, _current_uid())
    if err:
        return err
    bookings = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
    return jsonify({"trek": trek.to_dict(), "participants": [b.to_dict() for b in bookings]})


@api_bp.route("/staff/treks/<int:trek_id>/complete", methods=["PUT"])
@roles_required(ROLE_STAFF)
def staff_mark_completed(trek_id):
    trek, err = _get_owned_trek_or_error(trek_id, _current_uid())
    if err:
        return err
    trek.status = "Completed"
    Booking.query.filter_by(trek_id=trek.id, status=BOOKING_STATUS_BOOKED).update({"status": "Completed"})
    db.session.commit()
    _invalidate_trek_caches()
    return jsonify({"message": "Trek marked as completed", "trek": trek.to_dict()})



# TREKKER 
@api_bp.route("/treks", methods=["GET"])
@roles_required(ROLE_USER)
def browse_treks():
    difficulty = request.args.get("difficulty")
    location = request.args.get("location")
    max_duration = request.args.get("max_duration")

    cache_key = f"cache:treks:list:{difficulty}:{location}:{max_duration}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify({"treks": cached, "cached": True})

    query = Trek.query.filter_by(status=TREK_STATUS_OPEN)
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))
    if max_duration:
        query = query.filter(Trek.duration_days <= int(max_duration))

    treks = query.order_by(Trek.start_date.asc()).all()
    data = [t.to_dict() for t in treks]
    _cache_set(cache_key, data)
    return jsonify({"treks": data, "cached": False})


@api_bp.route("/user/dashboard", methods=["GET"])
@roles_required(ROLE_USER)
def user_dashboard():
    uid = _current_uid()
    available = Trek.query.filter_by(status=TREK_STATUS_OPEN).count()
    my_bookings = Booking.query.filter_by(user_id=uid).all()
    booked_active = [b for b in my_bookings if b.status == BOOKING_STATUS_BOOKED]
    return jsonify(
        {
            "available_treks": available,
            "booked_treks": [b.to_dict() for b in booked_active],
            "total_bookings": len(my_bookings),
        }
    )


@api_bp.route("/user/profile", methods=["GET"])
@roles_required(ROLE_USER)
def user_get_profile():
    user = User.query.get_or_404(_current_uid())
    return jsonify({"user": user.to_dict()})


@api_bp.route("/user/profile", methods=["PUT"])
@roles_required(ROLE_USER)
def user_update_profile():
    user = User.query.get_or_404(_current_uid())
    data = request.get_json(force=True, silent=True) or {}
    if "name" in data and data["name"].strip():
        user.name = data["name"].strip()
    if "phone" in data:
        user.phone = data["phone"].strip()
    if "password" in data and data["password"]:
        user.set_password(data["password"])
    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()})


@api_bp.route("/user/bookings", methods=["GET"])
@roles_required(ROLE_USER)
def user_my_bookings():
    bookings = Booking.query.filter_by(user_id=_current_uid()).order_by(Booking.booking_date.desc()).all()
    return jsonify({"bookings": [b.to_dict() for b in bookings]})


@api_bp.route("/user/bookings", methods=["POST"])
@roles_required(ROLE_USER)
def user_book_trek():
    uid = _current_uid()
    data = request.get_json(force=True, silent=True) or {}
    trek_id = data.get("trek_id")

    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({"error": "Trek not found"}), 404
    if trek.status != TREK_STATUS_OPEN:
        return jsonify({"error": "Booking only allowed when the trek is Open"}), 400
    if trek.available_slots <= 0:
        return jsonify({"error": "No available slots for this trek"}), 400

    existing = Booking.query.filter_by(user_id=uid, trek_id=trek_id).first()
    if existing:
        if existing.status == BOOKING_STATUS_BOOKED:
            return jsonify({"error": "You have already booked this trek"}), 409
        existing.status = BOOKING_STATUS_BOOKED
        existing.payment_status = "Pending"
        trek.available_slots -= 1
        db.session.commit()
        return jsonify({"message": "Trek booked", "booking": existing.to_dict()}), 201

    booking = Booking(user_id=uid, trek_id=trek_id, status=BOOKING_STATUS_BOOKED, payment_status="Pending")
    trek.available_slots -= 1
    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Trek booked", "booking": booking.to_dict()}), 201


@api_bp.route("/user/bookings/<int:booking_id>/cancel", methods=["PUT"])
@roles_required(ROLE_USER)
def user_cancel_booking(booking_id):
    uid = _current_uid()
    booking = Booking.query.filter_by(id=booking_id, user_id=uid).first_or_404()
    if booking.status != BOOKING_STATUS_BOOKED:
        return jsonify({"error": "Only active bookings can be cancelled"}), 400
    booking.status = BOOKING_STATUS_CANCELLED
    booking.trek.available_slots = min(booking.trek.available_slots + 1, booking.trek.total_slots)
    db.session.commit()
    return jsonify({"message": "Booking cancelled", "booking": booking.to_dict()})


@api_bp.route("/user/history", methods=["GET"])
@roles_required(ROLE_USER)
def user_history():
    bookings = Booking.query.filter_by(user_id=_current_uid()).order_by(Booking.booking_date.desc()).all()
    return jsonify({"history": [b.to_dict() for b in bookings]})


@api_bp.route("/user/export-history", methods=["POST"])
@roles_required(ROLE_USER)
def user_export_history():
    from tasks import export_booking_history_csv

    task = export_booking_history_csv.delay(_current_uid())
    return jsonify({"message": "Export started", "task_id": task.id}), 202


@api_bp.route("/user/export-status/<task_id>", methods=["GET"])
@roles_required(ROLE_USER)
def user_export_status(task_id):
    from workers import celery

    result = celery.AsyncResult(task_id)
    payload = {"task_id": task_id, "state": result.state}
    if result.state == "SUCCESS":
        payload["result"] = result.result
    elif result.state == "FAILURE":
        payload["error"] = str(result.info)
    return jsonify(payload)


@api_bp.route("/user/download-export/<path:filename>", methods=["GET"])
@roles_required(ROLE_USER)
def user_download_export(filename):
    uid = _current_uid()
    expected = f"booking_history_user_{uid}.csv"
    if filename != expected:
        return jsonify({"error": "Not authorized to access this file"}), 403
    export_dir = current_app.config["EXPORT_DIR"]
    import os

    if not os.path.exists(os.path.join(export_dir, filename)):
        return jsonify({"error": "File not found. Please re-run the export."}), 404
    return send_from_directory(export_dir, filename, as_attachment=True)
