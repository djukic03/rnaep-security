from database import SessionLocal, engine
import models


def seed_users():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(models.User).first():
            users = [
                models.User(username="admin", password="admin123", role="admin"),
                models.User(username="student", password="password123", role="user")
            ]
            db.add_all(users)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()