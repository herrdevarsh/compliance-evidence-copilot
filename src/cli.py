import json
import sys
from src.rag import ask

def main():
    q = " ".join(sys.argv[1:]).strip()
    if not q:
        raise SystemExit("Usage: python -m src.cli \"your question\"")
    pack = ask(q)
    print(json.dumps(pack, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
