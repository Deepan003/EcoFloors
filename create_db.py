from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()

    # ✅ Only add user if not already exists
    if not Admin.query.filter_by(username="floor1admin").first():
        admin = Admin(
            username="floor1admin",
            password=generate_password_hash("floor1pass"),
            floor="First Floor"
        )
        db.session.add(admin)
        db.session.commit()

