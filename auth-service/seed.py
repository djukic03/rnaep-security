from database import SessionLocal, engine
import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_users():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(models.User).first():
            users = [
                models.User(username="admin", password="admin123", role="admin"),
                models.User(username="student", password="student", role="user")
            ]
            db.add_all(users)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()