from database import SessionLocal, engine, Base
from models import Product

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(Product).first():
        p1 = Product(id=1, name="Laptop", price=1500.0, quantity=10)
        p2 = Product(id=2, name="Mouse", price=25.0, quantity=50)
        db.add_all([p1, p2])
        db.commit()
    db.close()

if __name__ == "__main__":
    seed()