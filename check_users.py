from config.database import get_db

db = get_db()
users = list(db.users.find({}))
for u in users:
    print("User:", u.get("matricule") or u.get("email"), "| Role:", u.get("role"), "| Pwd type:", type(u.get("password")), "| Pwd:", repr(u.get("password"))[:20])
