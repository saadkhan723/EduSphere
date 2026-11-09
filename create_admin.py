
from getpass import getpass

from app import app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash


def create_admin():

    print("\n===== EduSphere - Create Admin =====\n")

    name = input("Enter Admin Name: ").strip()
    email = input("Enter Admin Email: ").strip().lower()

    if not name or not email:
        print("Name and email are required.")
        return

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        print("An account with this email already exists.")
        return

    password = getpass("Enter Admin Password: ")
    confirm_password = getpass("Confirm Admin Password: ")

    if len(password) < 12:
        print("Admin password must contain at least 12 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    admin = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="admin"
    )

    db.session.add(admin)
    db.session.commit()

    print("\nAdmin account created successfully!")


if __name__ == "__main__":

    with app.app_context():
        create_admin()
