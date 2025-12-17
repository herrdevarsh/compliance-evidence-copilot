from sqlalchemy import text
from src.db import engine

def main():
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS text_tsv tsvector;"))
        conn.execute(text("""
            UPDATE chunks
            SET text_tsv = to_tsvector('english', coalesce(text,''))
            WHERE text_tsv IS NULL;
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_text_tsv ON chunks USING GIN(text_tsv);"))
    print("✅ FTS ready.")

if __name__ == "__main__":
    main()
