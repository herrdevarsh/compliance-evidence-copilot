from sqlalchemy import text
from src.db import engine
from src.models import Base

def main():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    Base.metadata.create_all(engine)
    print("✅ DB initialized.")

if __name__ == "__main__":
    main()
