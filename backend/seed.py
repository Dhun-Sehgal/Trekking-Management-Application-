from dotenv import load_dotenv

load_dotenv()

from app import app, db
from models import User, ROLE_ADMIN


def seed():
    with app.app_context():
        db.create_all()
        print("Database tables created (if not already present).")

        existing_admin = User.query.filter_by(role=ROLE_ADMIN).first()
        if existing_admin:
            print(f"Admin already exists: {existing_admin.email}. Skipping creation.")
            return

        admin_email = app.config["DEFAULT_ADMIN_EMAIL"]
        admin_password = app.config["DEFAULT_ADMIN_PASSWORD"]

        admin = User(name="System Administrator", email=admin_email, role=ROLE_ADMIN, is_active=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()

        print("=" * 60)
        print("Admin superuser created successfully:")
        print(f"  Email:    {admin_email}")
        print(f"  Password: {admin_password}")
        print("Please log in and change the password in production use.")
        print("=" * 60)


if __name__ == "__main__":
    seed()
