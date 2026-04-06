# -*- coding: utf-8 -*-
# X-EXAM v5.0 — He thong luyen thi THPT
# Features: Groups, Announcements, Exam Schedule, Source Credits
import os, json, hashlib, secrets, re, sqlite3, random
from datetime import datetime, timedelta, date
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'xexam-duytan-secret-2026-stable')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
DB = os.path.join(os.path.dirname(__file__), 'data', 'xexam.db')

# Auto-create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(DB), exist_ok=True)

# ─── DB ───
DATABASE_URL = os.environ.get('DATABASE_URL', '')

class PGCursor:
    def __init__(self, cur):
        self._c = cur; self.lastrowid = None
    def fetchone(self):
        try:
            r = self._c.fetchone()
            return dict(r) if r else None
        except: return None
    def fetchall(self):
        try: return [dict(r) for r in self._c.fetchall()]
        except: return []

class PGConn:
    def __init__(self):
        import psycopg2, psycopg2.extras
        self._pg = psycopg2; self._extras = psycopg2.extras
        self._conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    def execute(self, sql, params=None):
        cur = self._conn.cursor(cursor_factory=self._extras.RealDictCursor)
        sql = sql.replace('?', '%s')
        is_ignore = bool(re.search(r'INSERT\s+OR\s+IGNORE', sql, re.IGNORECASE))
        if is_ignore:
            sql = re.sub(r'INSERT\s+OR\s+IGNORE', 'INSERT', sql, flags=re.IGNORECASE)
            sql = sql.rstrip().rstrip(';') + ' ON CONFLICT DO NOTHING'
        is_insert = sql.strip().upper().startswith('INSERT') and not is_ignore
        if is_insert and 'RETURNING' not in sql.upper():
            sql = sql.rstrip().rstrip(';') + ' RETURNING id'
        try:
            cur.execute(sql, tuple(params) if params else None)
        except self._pg.Error as e:
            self._conn.rollback()
            print(f"PG Error: {e}")
            cur = self._conn.cursor(cursor_factory=self._extras.RealDictCursor)
            return PGCursor(cur)
        wrapper = PGCursor(cur)
        if is_insert:
            try:
                row = cur.fetchone()
                wrapper.lastrowid = row['id'] if row else None
            except: pass
        return wrapper
    def executescript(self, sql):
        sql = re.sub(r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT', 'SERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
        self._conn.autocommit = True
        cur = self._conn.cursor()
        for stmt in sql.split(';'):
            stmt = stmt.strip()
            if not stmt: continue
            try: cur.execute(stmt)
            except Exception as e: print(f"PG skip: {str(e)[:80]}")
        self._conn.autocommit = False
    def commit(self): self._conn.commit()
    def close(self): self._conn.close()

def get_db():
    if DATABASE_URL:
        return PGConn()
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    c = get_db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            fullname TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            avatar TEXT DEFAULT '🎓',
            is_approved INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT DEFAULT '',
            source TEXT DEFAULT '',
            time_limit INTEGER DEFAULT 90,
            total_score REAL DEFAULT 10.0,
            is_active INTEGER DEFAULT 1,
            is_open INTEGER DEFAULT 1,
            open_at TEXT DEFAULT NULL,
            close_at TEXT DEFAULT NULL,
            max_attempts INTEGER DEFAULT 999,
            shuffle_questions INTEGER DEFAULT 0,
            teacher_approved INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question_number INTEGER,
            type TEXT DEFAULT 'multiple_choice',
            content TEXT NOT NULL,
            option_a TEXT DEFAULT '',
            option_b TEXT DEFAULT '',
            option_c TEXT DEFAULT '',
            option_d TEXT DEFAULT '',
            correct_answer TEXT DEFAULT '',
            score REAL DEFAULT 0.25,
            explanation TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            exam_id INTEGER,
            answers TEXT DEFAULT '{}',
            score REAL DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            total_wrong INTEGER DEFAULT 0,
            total_blank INTEGER DEFAULT 0,
            time_spent INTEGER DEFAULT 0,
            teacher_comment TEXT DEFAULT '',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT DEFAULT '',
            description TEXT DEFAULT '',
            invite_code TEXT UNIQUE NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            user_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, user_id)
    );
    CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            author_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            exam_id INTEGER DEFAULT NULL,
            pin_exam_at TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Migrate exams table if missing columns
    if DATABASE_URL:
        existing = [r['column_name'] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='exams'").fetchall()]
    else:
        existing = [r[1] for r in c.execute("PRAGMA table_info(exams)").fetchall()]
    for col, defval in [('source',"TEXT DEFAULT ''"), ('is_open',"INTEGER DEFAULT 1"),
                             ('open_at',"TEXT DEFAULT NULL"), ('close_at',"TEXT DEFAULT NULL"),
                             ('max_attempts',"INTEGER DEFAULT 999"), ('shuffle_questions',"INTEGER DEFAULT 0"),
                             ('teacher_approved',"INTEGER DEFAULT 1")]:
            if col not in existing:
                try: c.execute(f"ALTER TABLE exams ADD COLUMN {col} {defval}")
                except: pass
    # Migrate submissions
    if DATABASE_URL:
        existing2 = [r['column_name'] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='submissions'").fetchall()]
    else:
        existing2 = [r[1] for r in c.execute("PRAGMA table_info(submissions)").fetchall()]
    if 'teacher_comment' not in existing2:
            try: c.execute("ALTER TABLE submissions ADD COLUMN teacher_comment TEXT DEFAULT ''")
            except: pass
    # Migrate users
    if DATABASE_URL:
        existing3 = [r['column_name'] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'").fetchall()]
    else:
        existing3 = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
    for col, defval in [('avatar',"TEXT DEFAULT '🎓'"), ('is_approved',"INTEGER DEFAULT 1")]:
            if col not in existing3:
                try: c.execute(f"ALTER TABLE users ADD COLUMN {col} {defval}")
                except: pass

    pw = hashlib.sha256('admin123'.encode()).hexdigest()
    pw2 = hashlib.sha256('123456'.encode()).hexdigest()
    pw_super = hashlib.sha256('DuyTan@2026'.encode()).hexdigest()
    try:
            c.execute("INSERT OR IGNORE INTO users(username,password_hash,fullname,role,avatar) VALUES(?,?,?,?,?)",
                      ('admin', pw, 'Quản trị viên', 'admin', '👑'))
            c.execute("INSERT OR IGNORE INTO users(username,password_hash,fullname,role,avatar) VALUES(?,?,?,?,?)",
                      ('teacher', pw, 'Giáo viên Demo', 'teacher', '👨‍🏫'))
            c.execute("INSERT OR IGNORE INTO users(username,password_hash,fullname,role,avatar) VALUES(?,?,?,?,?)",
                      ('student', pw2, 'Học sinh Demo', 'student', '🎓'))
            c.execute("INSERT OR IGNORE INTO users(username,password_hash,fullname,role,avatar) VALUES(?,?,?,?,?)",
                      ('superadmin', pw_super, 'Super Admin DuyTan', 'admin', '🛡️'))
            c.commit()
    except: pass
    c.close()

# ─── AUTH ───
def login_req(f):
    @wraps(f)
    def w(*a, **k):
            if 'user_id' not in session: return redirect('/login')
            return f(*a, **k)
    return w

def teacher_req(f):
    @wraps(f)
    def w(*a, **k):
            if 'user_id' not in session: return redirect('/login')
            if session.get('role') not in ('teacher', 'admin'):
                return jsonify({'error': 'Không có quyền'}), 403
            return f(*a, **k)
    return w

def admin_req(f):
    @wraps(f)
    def w(*a, **k):
            if 'user_id' not in session: return redirect('/login')
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin only'}), 403
            return f(*a, **k)
    return w

def get_user(): return {'id': session.get('user_id'), 'role': session.get('role'), 'fullname': session.get('fullname'), 'username': session.get('username')}

# ─── PAGES ───
@app.route('/')
def index():
    return redirect('/dashboard' if 'user_id' in session else '/login')

@app.route('/login')
def login_page(): return render_template('login.html')

@app.route('/dashboard')
@login_req
def dashboard(): return render_template('dashboard.html')

@app.route('/exam/<int:eid>')
@login_req
def exam_page(eid): return render_template('exam.html', exam_id=eid)

@app.route('/result/<int:sid>')
@login_req
def result_page(sid): return render_template('result.html', submission_id=sid)

@app.route('/create-exam')
@teacher_req
def create_exam_page(): return render_template('create_exam.html')

@app.route('/stats')
@login_req
def stats_page(): return render_template('stats.html')

@app.route('/leaderboard')
@login_req
def leaderboard_page(): return render_template('leaderboard.html')

@app.route('/teacher-review')
@teacher_req
def teacher_review_page(): return render_template('teacher_review.html')

@app.route('/chat')
@login_req
def chat_page(): return render_template('chat.html')

@app.route('/groups')
@login_req
def groups_page(): return render_template('groups.html')

@app.route('/group/<int:gid>')
@login_req
def group_detail_page(gid): return render_template('group_detail.html', group_id=gid)

@app.route('/admin')
@admin_req
def admin_page(): return render_template('admin.html')

# ─── AUTH API ───
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json or {}
    pw = hashlib.sha256(d.get('password','').encode()).hexdigest()
    c = get_db()
    u = c.execute("SELECT * FROM users WHERE username=? AND password_hash=?",
                      (d.get('username','').strip(), pw)).fetchone()
    c.close()
    if u:
            session['user_id'] = u['id']
            session['username'] = u['username']
            session['fullname'] = u['fullname']
            session['role'] = u['role']
            return jsonify({'success': True, 'user': dict(u)})
    return jsonify({'success': False, 'error': 'Sai tài khoản hoặc mật khẩu'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.json or {}
    pw = hashlib.sha256(d.get('password','').encode()).hexdigest()
    avatars = {'student':'🎓','teacher':'👨‍🏫','admin':'👑'}
    av = avatars.get(d.get('role','student'),'🎓')
    c = get_db()
    try:
            c.execute("INSERT INTO users(username,password_hash,fullname,role,avatar) VALUES(?,?,?,?,?)",
                      (d['username'].strip(), pw, d['fullname'].strip(), d.get('role','student'), av))
            c.commit(); c.close()
            return jsonify({'success': True})
    except:
            c.close()
            return jsonify({'error': 'Tên đăng nhập đã tồn tại'}), 400

@app.route('/api/logout')
def api_logout():
    session.clear()
    return redirect('/login')

# ─── EXAM APIs ───
@app.route('/api/exams')
@login_req
def api_exams():
    c = get_db()
    uid = session['user_id']
    now = datetime.now().isoformat()
    exams = c.execute("""
            SELECT e.*, u.fullname as creator_name, u.avatar as creator_avatar,
            (SELECT COUNT(*) FROM questions WHERE exam_id=e.id) as question_count,
            (SELECT COUNT(*) FROM submissions WHERE exam_id=e.id AND student_id=?) as my_attempts,
            (SELECT MAX(score) FROM submissions WHERE exam_id=e.id AND student_id=?) as my_best
            FROM exams e LEFT JOIN users u ON e.created_by=u.id
            WHERE e.is_active=1 AND (e.teacher_approved=1 OR e.created_by=?) ORDER BY e.created_at DESC
    """, (uid, uid, uid)).fetchall()
    result = []
    for e in exams:
            ed = dict(e)
            # Check schedule
            now_str = datetime.now().isoformat()
            open_ok = True
            if ed.get('open_at') and now_str < ed['open_at']:
                open_ok = False
            if ed.get('close_at') and now_str > ed['close_at']:
                open_ok = False
            ed['schedule_open'] = open_ok and bool(ed.get('is_open', 1))
            # Check if can attempt more
            attempts = ed.get('my_attempts', 0)
            max_attempts = ed.get('max_attempts', 999)
            ed['can_attempt'] = attempts < max_attempts
            ed['attempts_left'] = max(0, max_attempts - attempts)
            result.append(ed)
    c.close()
    return jsonify(result)

@app.route('/api/exam/<int:eid>')
@login_req
def api_exam(eid):
    c = get_db()
    exam = c.execute("SELECT * FROM exams WHERE id=?", (eid,)).fetchone()
    if not exam: c.close(); return jsonify({'error': 'Không tìm thấy'}), 404
    # Check max attempts
    attempts = c.execute("SELECT COUNT(*) as c FROM submissions WHERE exam_id=? AND student_id=?", (eid, session['user_id'])).fetchone()['c']
    max_attempts = exam.get('max_attempts', 999)
    if attempts >= max_attempts:
        c.close()
        return jsonify({'error': f'Bạn đã thi {attempts} lần. Tối đa {max_attempts} lần.'}), 403
    qs = c.execute("SELECT id,question_number,type,content,option_a,option_b,option_c,option_d,score FROM questions WHERE exam_id=? ORDER BY question_number", (eid,)).fetchall()
    # Shuffle if enabled
    qs_list = [dict(q) for q in qs]
    if exam.get('shuffle_questions', 0):
        random.shuffle(qs_list)
    c.close()
    return jsonify({'exam': dict(exam), 'questions': qs_list})

@app.route('/api/exam/create', methods=['POST'])
@teacher_req
def api_create_exam():
    d = request.json or {}
    c = get_db()
    user = c.execute("SELECT is_approved FROM users WHERE id=?", (session['user_id'],)).fetchone()
    teacher_approved = user['is_approved'] if user else 0
    cur = c.execute("""INSERT INTO exams(title,subject,description,source,time_limit,total_score,created_by,is_open,open_at,close_at,max_attempts,shuffle_questions,teacher_approved)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d['title'], d['subject'], d.get('description',''), d.get('source',''),
             d.get('time_limit',90), d.get('total_score',10), session['user_id'],
             d.get('is_open',1), d.get('open_at') or None, d.get('close_at') or None,
             d.get('max_attempts',999), d.get('shuffle_questions',0), teacher_approved))
    eid = cur.lastrowid
    for i, q in enumerate(d.get('questions',[]), 1):
            c.execute("""INSERT INTO questions(exam_id,question_number,type,content,option_a,option_b,option_c,option_d,correct_answer,score,explanation)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (eid, i, q.get('type','multiple_choice'), q.get('content',''),
                 q.get('option_a',''), q.get('option_b',''), q.get('option_c',''), q.get('option_d',''),
                 q.get('correct_answer',''), q.get('score',0.25), q.get('explanation','')))
    c.commit(); c.close()
    return jsonify({'success': True, 'exam_id': eid})

@app.route('/api/exam/toggle/<int:eid>', methods=['POST'])
@teacher_req
def api_toggle_exam(eid):
    c = get_db()
    exam = c.execute("SELECT is_open FROM exams WHERE id=?", (eid,)).fetchone()
    if not exam: c.close(); return jsonify({'error': 'Không tìm thấy'}), 404
    new_val = 0 if exam['is_open'] else 1
    c.execute("UPDATE exams SET is_open=? WHERE id=?", (new_val, eid))
    c.commit(); c.close()
    return jsonify({'success': True, 'is_open': new_val})

@app.route('/api/exam/delete/<int:eid>', methods=['DELETE'])
@teacher_req
def api_delete_exam(eid):
    c = get_db()
    c.execute("DELETE FROM questions WHERE exam_id=?", (eid,))
    c.execute("DELETE FROM submissions WHERE exam_id=?", (eid,))
    c.execute("DELETE FROM exams WHERE id=?", (eid,))
    c.commit(); c.close()
    return jsonify({'success': True})

# ─── SUBMIT ───
@app.route('/api/submit', methods=['POST'])
@login_req
def api_submit():
    d = request.json or {}
    eid = d['exam_id']
    ans = d.get('answers', {})
    c = get_db()
    
    # Check exam is open
    exam = c.execute("SELECT is_open,open_at,close_at FROM exams WHERE id=?", (eid,)).fetchone()
    if exam:
            now_str = datetime.now().isoformat()
            if not exam['is_open']:
                c.close(); return jsonify({'error': 'Bài kiểm tra đã đóng!'}), 403
            if exam['open_at'] and now_str < exam['open_at']:
                c.close(); return jsonify({'error': 'Bài kiểm tra chưa mở!'}), 403
            if exam['close_at'] and now_str > exam['close_at']:
                c.close(); return jsonify({'error': 'Bài kiểm tra đã hết hạn!'}), 403
    
    qs = c.execute("SELECT id,correct_answer,score,type FROM questions WHERE exam_id=?", (eid,)).fetchall()
    sc = 0.0; cor = 0; wr = 0; bl = 0
    for q in qs:
            sa = str(ans.get(str(q['id']), '')).strip()
            ca = str(q['correct_answer'] or '').strip()
            qt = q['type'] or 'multiple_choice'
            if qt == 'essay':
                if sa: sc += q['score'] * 0.5; cor += 1
                else: bl += 1
            elif qt == 'true_false':
                if not sa: bl += 1
                else:
                    total_sub = max(len(ca), 1)
                    correct_sub = sum(1 for i in range(min(len(sa), len(ca))) if sa[i].upper() == ca[i].upper())
                    if correct_sub == total_sub: sc += q['score']; cor += 1
                    elif correct_sub > 0: sc += q['score'] * correct_sub / total_sub; cor += 1
                    else: wr += 1
            else:
                if not sa: bl += 1
                elif sa.upper() == ca.upper(): sc += q['score']; cor += 1
                else: wr += 1
    
    cur = c.execute("INSERT INTO submissions(student_id,exam_id,answers,score,total_correct,total_wrong,total_blank,time_spent) VALUES(?,?,?,?,?,?,?,?)",
            (session['user_id'], eid, json.dumps(ans), round(sc, 2), cor, wr, bl, d.get('time_spent', 0)))
    sid = cur.lastrowid
    c.commit(); c.close()
    return jsonify({'success': True, 'submission_id': sid, 'score': round(sc,2), 'correct': cor, 'wrong': wr, 'blank': bl})

@app.route('/api/result/<int:sid>')
@login_req
def api_result(sid):
    c = get_db()
    sub = c.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    if not sub: c.close(); return jsonify({'error': 'Không tìm thấy'}), 404
    exam = c.execute("SELECT * FROM exams WHERE id=?", (sub['exam_id'],)).fetchone()
    qs = c.execute("SELECT * FROM questions WHERE exam_id=? ORDER BY question_number", (sub['exam_id'],)).fetchall()
    c.close()
    return jsonify({'submission': dict(sub), 'exam': dict(exam), 'questions': [dict(q) for q in qs],
                        'student_answers': json.loads(sub['answers'] or '{}')})

# ─── STATS ───
@app.route('/api/stats')
@login_req
def api_stats():
    uid = session['user_id']; c = get_db()
    te = c.execute("SELECT COUNT(DISTINCT exam_id) as c FROM submissions WHERE student_id=?", (uid,)).fetchone()['c']
    ts = c.execute("SELECT COUNT(*) as c FROM submissions WHERE student_id=?", (uid,)).fetchone()['c']
    av = c.execute("SELECT AVG(score) as a FROM submissions WHERE student_id=?", (uid,)).fetchone()['a'] or 0
    bs = c.execute("SELECT e.subject, AVG(s.score) as avg_score, COUNT(*) as attempts, MAX(s.score) as best_score FROM submissions s JOIN exams e ON s.exam_id=e.id WHERE s.student_id=? GROUP BY e.subject", (uid,)).fetchall()
    rc = c.execute("SELECT s.*,e.title,e.subject,e.total_score FROM submissions s JOIN exams e ON s.exam_id=e.id WHERE s.student_id=? ORDER BY s.submitted_at DESC LIMIT 20", (uid,)).fetchall()
    c.close()
    return jsonify({'total_exams': te, 'total_submissions': ts, 'avg_score': round(av,2),
                        'by_subject': [dict(s) for s in bs], 'recent': [dict(r) for r in rc]})

@app.route('/api/my-rank')
@login_req
def api_my_rank():
    c = get_db()
    uid = session['user_id']
    total = c.execute("SELECT COUNT(*) as c FROM submissions WHERE student_id=?", (uid,)).fetchone()['c']
    c.close()
    rank = get_rank(total)
    rank['meme'] = random.choice(MASCOT_IDLE)
    return jsonify(rank)

@app.route('/api/streak')
@login_req
def api_streak():
    uid = session['user_id']; c = get_db()
    dates = c.execute("SELECT DISTINCT DATE(submitted_at) as d FROM submissions WHERE student_id=? ORDER BY d DESC", (uid,)).fetchall()
    c.close()
    date_list = [d['d'] for d in dates if d['d']]
    today_str = date.today().isoformat()
    today_done = today_str in date_list
    streak = 0
    check = date.today() if today_done else date.today() - timedelta(days=1)
    for i in range(400):
            if (check - timedelta(days=i)).isoformat() in date_list: streak += 1
            else: break
    longest = 0; cur_s = 0
    for i, ds in enumerate(sorted(date_list)):
            if i == 0: cur_s = 1
            else:
                prev = datetime.strptime(sorted(date_list)[i-1],'%Y-%m-%d').date()
                curr = datetime.strptime(ds,'%Y-%m-%d').date()
                cur_s = cur_s+1 if (curr-prev).days==1 else 1
            longest = max(longest, cur_s)
    STREAK_BADGES = [(3,'Chăm học cấp 1','📘'),(7,'Máy giải đề','🤖'),(14,'Quái vật ôn thi','👾'),(30,'Siêu nhân học tập','🦸'),(60,'Huyền thoại','🐉')]
    badges = [{'name':n,'icon':ic,'days':d} for d,n,ic in STREAK_BADGES if longest>=d]
    return jsonify({'streak': streak, 'longest': longest, 'badges': badges, 'today_done': today_done, 'total_days': len(date_list)})

# ─── LEADERBOARD ───
@app.route('/api/leaderboard')
@login_req
def api_leaderboard():
    c = get_db()
    king_count = c.execute("SELECT u.id,u.fullname,u.avatar,COUNT(*) as total_subs,AVG(s.score) as avg_score,MAX(s.score) as best FROM submissions s JOIN users u ON s.student_id=u.id GROUP BY u.id ORDER BY total_subs DESC LIMIT 20").fetchall()
    king_score = c.execute("SELECT u.id,u.fullname,u.avatar,COUNT(*) as total_subs,AVG(s.score) as avg_score,MAX(s.score) as best FROM submissions s JOIN users u ON s.student_id=u.id GROUP BY u.id ORDER BY avg_score DESC LIMIT 20").fetchall()
    king_elite = c.execute("SELECT u.id,u.fullname,u.avatar,COUNT(*) as total_subs,AVG(s.score) as avg_score,MAX(s.score) as best,(COUNT(*)*0.3+AVG(s.score)*0.7) as elite FROM submissions s JOIN users u ON s.student_id=u.id GROUP BY u.id ORDER BY elite DESC LIMIT 20").fetchall()
    # Teacher rank by exams created
    teacher_rank = c.execute("SELECT u.id,u.fullname,u.avatar,COUNT(e.id) as total_exams FROM users u LEFT JOIN exams e ON e.created_by=u.id WHERE u.role IN('teacher','admin') GROUP BY u.id ORDER BY total_exams DESC LIMIT 20").fetchall()
    c.close()
    return jsonify({'king_count':[dict(r) for r in king_count],'king_score':[dict(r) for r in king_score],
                        'king_elite':[dict(r) for r in king_elite],'teacher_rank':[dict(r) for r in teacher_rank]})

# ─── GROUPS ───
@app.route('/api/groups')
@login_req
def api_groups():
    uid = session['user_id']; c = get_db()
    if session['role'] in ('teacher','admin'):
            groups = c.execute("SELECT g.*,(SELECT COUNT(*) FROM group_members WHERE group_id=g.id) as member_count FROM groups g WHERE g.created_by=? ORDER BY g.created_at DESC", (uid,)).fetchall()
    else:
            groups = c.execute("SELECT g.*,(SELECT COUNT(*) FROM group_members WHERE group_id=g.id) as member_count FROM groups g JOIN group_members gm ON g.id=gm.group_id WHERE gm.user_id=? ORDER BY g.created_at DESC", (uid,)).fetchall()
    c.close()
    return jsonify([dict(g) for g in groups])

@app.route('/api/group/create', methods=['POST'])
@teacher_req
def api_create_group():
    d = request.json or {}
    code = secrets.token_urlsafe(6).upper()
    c = get_db()
    cur = c.execute("INSERT INTO groups(name,subject,description,invite_code,created_by) VALUES(?,?,?,?,?)",
            (d['name'], d.get('subject',''), d.get('description',''), code, session['user_id']))
    gid = cur.lastrowid
    c.execute("INSERT OR IGNORE INTO group_members(group_id,user_id) VALUES(?,?)", (gid, session['user_id']))
    c.commit(); c.close()
    return jsonify({'success': True, 'group_id': gid, 'invite_code': code})

@app.route('/api/group/join', methods=['POST'])
@login_req
def api_join_group():
    d = request.json or {}
    code = d.get('code','').strip().upper()
    c = get_db()
    group = c.execute("SELECT * FROM groups WHERE invite_code=?", (code,)).fetchone()
    if not group: c.close(); return jsonify({'error': 'Mã mời không hợp lệ!'}), 404
    try:
            c.execute("INSERT INTO group_members(group_id,user_id) VALUES(?,?)", (group['id'], session['user_id']))
            c.commit()
    except: pass
    c.close()
    return jsonify({'success': True, 'group_name': group['name']})

@app.route('/api/group/<int:gid>')
@login_req
def api_group_detail(gid):
    c = get_db()
    group = c.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    if not group: c.close(); return jsonify({'error': 'Không tìm thấy nhóm'}), 404
    members = c.execute("SELECT u.id,u.fullname,u.role,u.avatar FROM group_members gm JOIN users u ON gm.user_id=u.id WHERE gm.group_id=?", (gid,)).fetchall()
    announcements = c.execute("SELECT a.*,u.fullname as author_name,u.avatar as author_avatar FROM announcements a JOIN users u ON a.author_id=u.id WHERE a.group_id=? ORDER BY a.created_at DESC", (gid,)).fetchall()
    c.close()
    return jsonify({'group': dict(group), 'members': [dict(m) for m in members], 'announcements': [dict(a) for a in announcements]})

@app.route('/api/group/<int:gid>/announce', methods=['POST'])
@teacher_req
def api_announce(gid):
    d = request.json or {}
    c = get_db()
    c.execute("INSERT INTO announcements(group_id,author_id,title,content,exam_id,pin_exam_at) VALUES(?,?,?,?,?,?)",
            (gid, session['user_id'], d['title'], d['content'], d.get('exam_id') or None, d.get('pin_exam_at') or None))
    c.commit(); c.close()
    return jsonify({'success': True})

# ─── TEACHER REVIEW ───
@app.route('/api/teacher/submissions')
@teacher_req
def api_teacher_subs():
    c = get_db()
    subs = c.execute("SELECT s.*,u.fullname as student_name,u.username,e.title as exam_title,e.subject,e.total_score FROM submissions s JOIN users u ON s.student_id=u.id JOIN exams e ON s.exam_id=e.id ORDER BY s.submitted_at DESC LIMIT 100").fetchall()
    c.close()
    return jsonify([dict(s) for s in subs])

@app.route('/api/teacher/comment', methods=['POST'])
@teacher_req
def api_comment():
    d = request.json or {}
    c = get_db()
    c.execute("UPDATE submissions SET teacher_comment=? WHERE id=?", (d.get('comment',''), d['submission_id']))
    c.commit(); c.close()
    return jsonify({'success': True})

# ─── QUICK EXAM ───
@app.route('/api/quick-exam', methods=['POST'])
@login_req
def api_quick_exam():
    d = request.json or {}
    subject = d.get('subject',''); num = d.get('num', 10)
    c = get_db()
    if subject:
            qs = c.execute("SELECT q.* FROM questions q JOIN exams e ON q.exam_id=e.id WHERE e.subject=? ORDER BY RANDOM() LIMIT ?", (subject, num)).fetchall()
    else:
            qs = c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (num,)).fetchall()
    if not qs: c.close(); return jsonify({'error': 'Chưa có câu hỏi nào!'}), 400
    title = f"Luyện nhanh {subject or 'Tổng hợp'} — {datetime.now().strftime('%H:%M %d/%m')}"
    cur = c.execute("INSERT INTO exams(title,subject,description,time_limit,total_score,created_by) VALUES(?,?,?,?,?,?)",
            (title, subject or 'Tổng hợp', 'Đề luyện nhanh tự động', 5, 10, session['user_id']))
    eid = cur.lastrowid; spp = round(10.0/len(qs), 2)
    for i, q in enumerate(qs, 1):
            c.execute("INSERT INTO questions(exam_id,question_number,type,content,option_a,option_b,option_c,option_d,correct_answer,score) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (eid, i, q['type'], q['content'], q['option_a'], q['option_b'], q['option_c'], q['option_d'], q['correct_answer'], spp))
    c.commit(); c.close()
    return jsonify({'success': True, 'exam_id': eid, 'num_questions': len(qs)})

# ─── UPLOAD ───
@app.route('/api/upload-exam', methods=['POST'])
@teacher_req
def api_upload():
    if 'file' not in request.files: return jsonify({'error': 'Không có file'}), 400
    f = request.files['file']
    fn = secure_filename(f.filename or 'upload')
    orig_ext = (f.filename or '').rsplit('.',1)[-1].lower() if '.' in (f.filename or '') else 'txt'
    if not fn.endswith('.' + orig_ext):
            fn = fn + '.' + orig_ext
    fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
    f.save(fp)
    text = read_file_content(fp)
    if not text or len(text) < 5:
            return jsonify({'success': False, 'error': f'Không đọc được file .{orig_ext}', 'questions': []})
    qs = parse_questions_smart(text)
    return jsonify({'success': True, 'filename': fn, 'file_type': orig_ext, 'content': text[:8000],
                        'total_chars': len(text), 'questions': qs,
                        'message': f'Đọc được {len(text)} ký tự, tìm thấy {len(qs)} câu hỏi'})

@app.route('/api/ai-auto-answer', methods=['POST'])
@teacher_req
def api_ai_auto():
    d = request.json or {}
    qs = d.get('questions', [])
    if not isinstance(qs, list):
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
    for q in qs:
        qtype = q.get('type', 'multiple_choice')
        if qtype == 'multiple_choice':
            opts = {'A': q.get('option_a',''), 'B': q.get('option_b',''),
                    'C': q.get('option_c',''), 'D': q.get('option_d','')}
            lens = {k: len(v) for k, v in opts.items() if v and v.strip()}
            if lens:
                q['correct_answer'] = max(lens, key=lens.get)
            else:
                q['correct_answer'] = 'A'
        elif qtype == 'true_false':
            # Analyze content for positive/negative keywords
            content = (q.get('content','') or '').lower()
            tf_ans = []
            sub_lines = [l.strip() for l in content.split('\n') if re.match(r'^[abcd]\)', l.strip(), re.IGNORECASE)]
            if not sub_lines:
                sub_lines = [f'y {x}' for x in ['a','b','c','d']]
            for sub in sub_lines[:4]:
                neg_words = ['khong','sai','false','khong phai','chua','khong the','khong co','0','negative']
                if any(w in sub.lower() for w in neg_words):
                    tf_ans.append('S')
                else:
                    tf_ans.append('D')
            while len(tf_ans) < 4:
                tf_ans.append('D')
            q['correct_answer'] = ''.join(tf_ans[:4])
        elif qtype == 'essay':
            q['correct_answer'] = ''
    return jsonify({'success': True, 'questions': qs,
                    'warning': 'AI chi goi y — Giao vien can kiem tra lai tat ca!'})

# ─── CHAT ───
@app.route('/api/chat', methods=['POST'])
@login_req
def api_chat():
    msg = (request.json or {}).get('message', '').strip()
    if not msg: return jsonify({'reply': 'Em chưa nhập câu hỏi!'})
    return jsonify({'reply': ai_reply(msg)})

# ─── MASCOT ───
@app.route('/api/mascot')
@login_req
def api_mascot():
    action = request.args.get('action', 'idle')
    msgs = {'correct': MASCOT_CORRECT, 'wrong': MASCOT_WRONG, 'idle': MASCOT_IDLE}
    pool = msgs.get(action, MASCOT_IDLE)
    if action == 'submit':
            pct = float(request.args.get('score',0)) / max(float(request.args.get('total',10)),1) * 100
            cat = 'god' if pct>=95 else 'great' if pct>=80 else 'good' if pct>=60 else 'ok' if pct>=40 else 'low'
            pool = MASCOT_SUBMIT.get(cat, MASCOT_IDLE)
    return jsonify({'message': random.choice(pool), 'name': 'Ôn Thi Chan'})

@app.route('/api/result-meme')
@login_req
def api_meme():
    pct = float(request.args.get('score',0)) / max(float(request.args.get('total',10)),1) * 100
    cat = 'god' if pct>=95 else 'great' if pct>=80 else 'good' if pct>=60 else 'ok' if pct>=40 else 'low'
    return jsonify({'meme': random.choice(RESULT_MEMES[cat]), 'category': cat, 'percentage': round(pct,1)})

# ─── ADMIN APIs ───
@app.route('/api/admin/overview')
@admin_req
def api_admin_overview():
    c = get_db()
    tu = c.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
    ts = c.execute("SELECT COUNT(*) as c FROM users WHERE role='student'").fetchone()['c']
    tt = c.execute("SELECT COUNT(*) as c FROM users WHERE role='teacher'").fetchone()['c']
    ta = c.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'").fetchone()['c']
    te = c.execute("SELECT COUNT(*) as c FROM exams").fetchone()['c']
    tsub = c.execute("SELECT COUNT(*) as c FROM submissions").fetchone()['c']
    tg = c.execute("SELECT COUNT(*) as c FROM groups").fetchone()['c']
    c.close()
    return jsonify({'total_users':tu,'total_students':ts,'total_teachers':tt,'total_admins':ta,'total_exams':te,'total_submissions':tsub,'total_groups':tg})

@app.route('/api/admin/users')
@admin_req
def api_admin_users():
    c = get_db()
    users = c.execute("""SELECT u.id,u.username,u.fullname,u.role,u.avatar,u.is_approved,u.created_at,
        (SELECT COUNT(*) FROM submissions WHERE student_id=u.id) as total_subs,
        (SELECT COUNT(*) FROM exams WHERE created_by=u.id) as total_exams
        FROM users u ORDER BY u.created_at DESC""").fetchall()
    c.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/delete-user/<int:uid>', methods=['DELETE'])
@admin_req
def api_admin_delete_user(uid):
    if uid == session['user_id']: return jsonify({'error':'Khong the xoa chinh minh'}),400
    c = get_db()
    u = c.execute("SELECT username FROM users WHERE id=?", (uid,)).fetchone()
    if not u: c.close(); return jsonify({'error':'User not found'}),404
    c.execute("DELETE FROM submissions WHERE student_id=?", (uid,))
    c.execute("DELETE FROM group_members WHERE user_id=?", (uid,))
    c.execute("DELETE FROM announcements WHERE author_id=?", (uid,))
    c.execute("DELETE FROM exams WHERE created_by=?", (uid,))
    c.execute("DELETE FROM users WHERE id=?", (uid,))
    c.commit(); c.close()
    return jsonify({'success':True})

@app.route('/api/admin/change-role', methods=['POST'])
@admin_req
def api_admin_change_role():
    d = request.json or {}
    uid = d.get('user_id'); new_role = d.get('role')
    if new_role not in ('student','teacher','admin'): return jsonify({'error':'Invalid role'}),400
    if uid == session['user_id']: return jsonify({'error':'Khong the doi role chinh minh'}),400
    avatars = {'student':'🎓','teacher':'👨‍🏫','admin':'👑'}
    c = get_db()
    c.execute("UPDATE users SET role=?,avatar=? WHERE id=?", (new_role, avatars.get(new_role,'🎓'), uid))
    c.commit(); c.close()
    return jsonify({'success':True})

@app.route('/api/admin/approve-teacher/<int:uid>', methods=['POST'])
@admin_req
def api_admin_approve_teacher(uid):
    c = get_db()
    c.execute("UPDATE users SET is_approved=1 WHERE id=? AND role='teacher'", (uid,))
    c.execute("UPDATE exams SET teacher_approved=1 WHERE created_by=?", (uid,))
    c.commit(); c.close()
    return jsonify({'success':True})

@app.route('/api/admin/reject-teacher/<int:uid>', methods=['POST'])
@admin_req
def api_admin_reject_teacher(uid):
    c = get_db()
    c.execute("UPDATE users SET is_approved=0 WHERE id=?", (uid,))
    c.execute("UPDATE exams SET is_active=0 WHERE created_by=?", (uid,))
    c.commit(); c.close()
    return jsonify({'success':True})

@app.route('/api/admin/all-submissions')
@admin_req
def api_admin_all_subs():
    c = get_db()
    subs = c.execute("""SELECT s.*,u.fullname as student_name,u.username,e.title as exam_title,e.subject,e.total_score 
        FROM submissions s JOIN users u ON s.student_id=u.id JOIN exams e ON s.exam_id=e.id 
        ORDER BY s.submitted_at DESC LIMIT 200""").fetchall()
    c.close()
    return jsonify([dict(s) for s in subs])

# ─── IMAGE UPLOAD FOR ESSAY ───
@app.route('/api/upload-answer-image', methods=['POST'])
@login_req
def api_upload_answer_image():
    if 'image' not in request.files: return jsonify({'error':'No image'}),400
    f = request.files['image']
    import time
    ext = (f.filename or 'img.jpg').rsplit('.',1)[-1].lower()
    fn = f"ans_{session['user_id']}_{int(time.time())}.{ext}"
    fp = os.path.join(app.config['UPLOAD_FOLDER'], fn)
    f.save(fp)
    return jsonify({'success':True,'url':f'/uploads/{fn}','filename':fn})

@app.route('/uploads/<filename>')
def serve_upload(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─── ANSWER FILE IMPORT ───
@app.route('/api/import-answers', methods=['POST'])
@teacher_req
def api_import_answers():
    if 'file' not in request.files: return jsonify({'error':'No file'}),400
    f = request.files['file']
    content = ''
    fn = (f.filename or '').lower()
    if fn.endswith('.txt') or fn.endswith('.csv'):
        content = f.read().decode('utf-8', errors='ignore')
    elif fn.endswith('.docx'):
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        f.save(tmp.name); tmp.close()
        try:
            from docx import Document
            doc = Document(tmp.name)
            content = '\n'.join([p.text for p in doc.paragraphs])
        except: content = ''
        os.unlink(tmp.name)
    else:
        content = f.read().decode('utf-8', errors='ignore')
    # Parse answers
    content = content.strip().upper()
    # Try format: 1.A 2.B 3.C or 1A 2B 3C
    import re
    answers = {}
    # Pattern: number followed by answer
    pairs = re.findall(r'(\d+)\s*[.)\-:]\s*([ABCD])', content)
    if pairs:
        for num, ans in pairs: answers[int(num)] = ans
    else:
        # Just a string of ABCD
        clean = re.sub(r'[^ABCDDS]', '', content)
        for i, ch in enumerate(clean): answers[i+1] = ch
    return jsonify({'success':True,'answers':answers,'total':len(answers),'raw':content[:500]})

# ─── DATA ───
RANKS = [(0,'Tân Binh','🐣','#9e9e9e','Mới bắt đầu hành trình!'),(10,'Đồng','🥉','#cd7f32','Chiến binh non trẻ!'),(20,'Bạc','🥈','#c0c0c0','Đang lên tay rồi đó!'),(30,'Vàng','🥇','#ffd700','Vàng 9999 luôn!'),(50,'Kim Cương','💎','#00bcd4','Sáng chói lóa mắt!'),(70,'Tinh Anh','🔮','#9c27b0','Cao thủ trong truyền thuyết!'),(90,'Cao Thủ','⚡','#ff5722','Thần đồng học tập!'),(150,'Ông Cố Nội','👑','#ff0000','Truyền thuyết sống!')]

def get_rank(total):
    rank = RANKS[0]
    for r in RANKS:
            if total >= r[0]: rank = r
    idx = RANKS.index(rank)
    nxt = RANKS[idx+1] if idx < len(RANKS)-1 else None
    prog = 0
    if nxt:
            needed = nxt[0] - rank[0]; done = total - rank[0]
            prog = min(100, int(done/needed*100)) if needed > 0 else 100
    else: prog = 100
    return {'name':rank[1],'icon':rank[2],'color':rank[3],'desc':rank[4],'min_subs':rank[0],
                'next_rank':{'name':nxt[1],'icon':nxt[2],'need':nxt[0]} if nxt else None,
                'progress':prog,'total_subs':total}

MASCOT_IDLE = ['Học đi bạn ơi, rank không tự lên đâu!','Cày 1 đề = 1 bước gần rank mới!','Hôm nay bạn đã làm bài chưa?','Ngày mai thi rồi, hôm nay phải cày!','AFK là thua, cày là thắng!','Não của bạn đang loading... hãy làm đề để upgrade!','Điểm 10 đang chờ bạn ở đề tiếp theo!','Cố công mài sắt, có ngày... lên rank Kim Cương!']
MASCOT_CORRECT = ['ĐỈNH QUÁ CHIẾN THẦN! 🔥','Não chạy bằng RTX 4090 rồi!','Câu này dễ mà, đúng không? 😎','Xuất sắc! Tiếp tục nhé!','GG! Too EZ!']
MASCOT_WRONG = ['Không sao, sai để học hỏi mà!','Câu này khó thật, đọc lại nhé!','Não cần sạc thêm cà phê rồi! ☕','Đừng buồn, còn nhiều câu dễ hơn!']
MASCOT_SUBMIT = {'god':['HỌC BÁ XUẤT HIỆN! 👑','Thần đồng là đây!'],'great':['Xuất sắc! Gần perfect rồi!'],'good':['Ổn áp! Chiến tiếp nhé! 💪'],'ok':['Được rồi, cần cố gắng thêm!'],'low':['Não cần sạc thêm cà phê! ☕','Calm down, học từ từ thôi!']}
RESULT_MEMES = {'god':[{'text':'HỌC BÁ XUẤT HIỆN!','emoji':'👑🔥'},{'text':'Full điểm! Thần đồng là bạn!','emoji':'🧠💎'}],'great':[{'text':'Gần perfect! Xuất sắc lắm!','emoji':'⭐🎯'},{'text':'Não RTX 4090 đã ON!','emoji':'🖥️🔥'}],'good':[{'text':'Ổn áp chiến tiếp!','emoji':'💪😎'}],'ok':[{'text':'Được rồi, cố gắng thêm!','emoji':'🤔💭'}],'low':[{'text':'Não cần sạc thêm cà phê!','emoji':'☕😴'},{'text':'Sai là để học, không phải để buồn!','emoji':'📚🌟'}]}

def read_file_content(fp):
    ext = fp.rsplit('.',1)[-1].lower() if '.' in fp else ''
    text = ''
    if ext == 'pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(fp)
                for page in reader.pages:
                    t = page.extract_text()
                    if t: text += t + '\n'
            except Exception as e: text = f'[PDF Error: {e}]'
    elif ext == 'docx':
            try:
                from docx import Document
                doc = Document(fp)
                for para in doc.paragraphs: text += para.text + '\n'
            except Exception as e: text = f'[DOCX Error: {e}]'
    elif ext in ('png','jpg','jpeg','gif','webp','bmp'):
            try:
                import pytesseract; from PIL import Image
                for tp in [r'C:\Program Files\Tesseract-OCR\tesseract.exe', r'C:\Users\LENOVO\AppData\Local\Tesseract-OCR\tesseract.exe']:
                    if os.path.exists(tp): pytesseract.pytesseract.tesseract_cmd = tp; break
                text = pytesseract.image_to_string(Image.open(fp), lang='vie+eng')
            except Exception as e: text = f'[OCR Error: {e}]'
    else:
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()
            except: pass
    return text.strip()

def parse_questions_smart(text):
    if not text or len(text) < 10: return []
    text = text.replace('\r\n','\n').replace('\r','\n')
    lines = text.split('\n')
    section = 'multiple_choice'
    section_map = {}
    for i, line in enumerate(lines):
            lu = line.strip().upper()
            if any(k in lu for k in ['TRAC NGHIEM NHIEU','PHUONG AN LUA CHON','NHIEU PHUONG AN','TRẮC NGHIỆM NHIỀU','PHƯƠNG ÁN LỰA CHỌN','NHIỀU PHƯƠNG ÁN']): section = 'multiple_choice'
            elif any(k in lu for k in ['DUNG SAI','ĐÚNG SAI','DUNG/SAI','ĐÚNG/SAI']): section = 'true_false'
            elif any(k in lu for k in ['TU LUAN','TỰ LUẬN']): section = 'essay'
            elif any(k in lu for k in ['TRA LOI NGAN','TRẢ LỜI NGẮN']): section = 'short_answer'
            section_map[i] = section
    q_positions = []
    for i, line in enumerate(lines):
            m = re.match(r'^\s*[Cc][aâ]u\s+(\d+)\s*[.:\)]\s*(.*)', line)
            if m: q_positions.append((i, int(m.group(1)), m.group(2).strip()))
    questions = []
    for idx, (li, qn, fl) in enumerate(q_positions):
            end = q_positions[idx+1][0] if idx+1 < len(q_positions) else len(lines)
            qt = section_map.get(li, 'multiple_choice')
            qlines = [fl] + [lines[j].strip() for j in range(li+1, end)]
            q = {'question_number': qn, 'content': '', 'type': qt, 'option_a':'','option_b':'','option_c':'','option_d':'','correct_answer':'','score':0.25}
            cl = []
            for line in qlines:
                line = line.strip()
                if not line: continue
                if qt == 'multiple_choice':
                    om = re.match(r'^\s*([ABCD])\s*[.)\s:]\s*(.+)', line)
                    if om: q[f'option_{om.group(1).lower()}'] = om.group(2).strip(); continue
                cl.append(line)
            q['content'] = '\n'.join(cl).strip() or '\n'.join(qlines).strip()[:300]
            if qt == 'true_false': q['score'] = 1.0
            elif qt == 'essay': q['score'] = 1.0
            if q['content'] and len(q['content']) > 2: questions.append(q)
    return questions

def ai_reply(msg):
    ml = msg.lower()
    if any(w in ml for w in ['nguyên hàm','tích phân','đạo hàm','integral','derivative']):
            return "Cô giáo AI: Về Nguyên hàm / Tích phân!\n\n📌 Công thức cơ bản:\n• ∫xⁿdx = xⁿ⁺¹/(n+1) + C\n• ∫sinx dx = −cosx + C\n• ∫cosx dx = sinx + C\n• ∫eˣdx = eˣ + C\n• ∫(1/x)dx = ln|x| + C\n\nPhương pháp: Đổi biến, tích phân từng phần, phân tích phân thức.\n\nEm muốn hỏi cụ thể phần nào?"
    if any(w in ml for w in ['mặt phẳng','mặt cầu','đường thẳng','tọa độ','oxyz']):
            return "Cô giáo AI: Hình học không gian Oxyz!\n\n📌 Công thức cần nhớ:\n• Mặt phẳng: ax+by+cz+d=0, VTPT n=(a,b,c)\n• Đường thẳng: (x−x₀)/a=(y−y₀)/b=(z−z₀)/c\n• Mặt cầu: (x−a)²+(y−b)²+(z−c)²=R²\n• d(M,mp) = |ax₀+by₀+cz₀+d| / √(a²+b²+c²)\n\nEm muốn hỏi phần nào cụ thể?"
    if any(w in ml for w in ['vật lý','newton','động lực','điện','từ trường','sóng']):
            return "Cô giáo AI: Môn Vật lý!\n\n📌 Công thức quan trọng:\n• F=ma, P=mg\n• Wd=mv²/2, Wt=mgh\n• U=IR, P=UI\n• T=2π√(l/g) (con lắc đơn)\n• v=λf (sóng cơ)\n\nEm cần giải bài tập cụ thể nào?"
    if any(w in ml for w in ['tin học','lập trình','python','sql','thuật toán']):
            return "Cô giáo AI: Môn Tin học!\n\n📌 Kiến thức trọng tâm:\n• Python: list, dict, loop, function\n• SQL: SELECT, WHERE, GROUP BY, JOIN\n• Thuật toán: tìm kiếm, sắp xếp\n• Độ phức tạp: O(1), O(n), O(n²), O(logn)\n\nEm muốn ôn phần nào?"
    if any(w in ml for w in ['xin chào','chào','hello','hi']):
            return "Chào em! 👋 Cô là AI Cô giáo của X-EXAM.\n\nCô có thể giúp em:\n• Giải thích kiến thức Toán, Lý, Tin\n• Gợi ý phương pháp làm bài\n• Phân tích điểm yếu cần cải thiện\n\nEm hỏi bất kỳ điều gì nhé! 😊"
    return f"Cô giáo AI nhận được câu hỏi: \"{msg[:80]}\"\n\nĐây là câu hỏi thú vị! Cô gợi ý:\n1. Xác định rõ kiến thức liên quan\n2. Viết ra công thức cần dùng\n3. Áp dụng từng bước cẩn thận\n4. Kiểm tra lại kết quả\n\nEm hỏi cụ thể hơn để cô hướng dẫn chi tiết nhé!"

# Auto-init DB on import (for gunicorn/render)
init_db()

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    init_db()
    print()
    print("="*55)
    print("  X-EXAM v5.0 - Hệ thống luyện thi THPT")
    print("  Mở trình duyệt: http://localhost:5000")
    print("  Tài khoản: admin/admin123 | student/123456")
    print("="*55)
    print()
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
