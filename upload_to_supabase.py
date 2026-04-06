import os, sys
os.environ["DATABASE_URL"] = "postgresql://postgres:tranlequyngoc19102008@db.uthuvfwynfiggerolesp.supabase.co:5432/postgres"
sys.path.insert(0, r"C:\Users\LENOVO\Desktop\XExam - Copy")
os.chdir(r"C:\Users\LENOVO\Desktop\XExam - Copy")
import app

print("=== KIEM TRA KET NOI SUPABASE ===")
print("Mode:", "PostgreSQL" if app.DATABASE_URL else "SQLite")

try:
    app.init_db()
    c = app.get_db()
    r = c.execute("SELECT count(*) as cnt FROM users").fetchone()
    print("Users in Supabase:", r["cnt"])
    exams = c.execute("SELECT count(*) as cnt FROM exams").fetchone()
    print("Exams in Supabase:", exams["cnt"])
    c.close()
    print("OK - Ket noi thanh cong!")
except Exception as e:
    print("LOI:", str(e))
