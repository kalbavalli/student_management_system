from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3, re

app = Flask(__name__)
app.secret_key = 'student-management-demo-key'
DATABASE = 'students.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        department TEXT NOT NULL,
        year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),
        phone TEXT NOT NULL)''')
    conn.commit(); conn.close()

def valid_email(x):
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', x) is not None

def validate(d):
    if not all(d.values()): return 'All fields are required.'
    if not valid_email(d['email']): return 'Enter a valid email address.'
    try:
        if int(d['year']) not in range(1, 5): raise ValueError
    except ValueError: return 'Year must be between 1 and 4.'
    return None

def form_data():
    return {k: request.form.get(k, '').strip() for k in
            ['student_id','name','email','department','year','phone']}

@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    conn = get_db()
    if search:
        students = conn.execute('''SELECT * FROM students
            WHERE student_id LIKE ? OR name LIKE ? OR email LIKE ?
            ORDER BY id DESC''', (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        students = conn.execute('SELECT * FROM students ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', students=students, search=search)

@app.route('/add', methods=['POST'])
def add():
    d = form_data(); error = validate(d)
    if error:
        flash(error, 'error'); return redirect(url_for('index'))
    conn = get_db()
    try:
        conn.execute('''INSERT INTO students
            (student_id,name,email,department,year,phone) VALUES (?,?,?,?,?,?)''',
            (d['student_id'],d['name'],d['email'],d['department'],int(d['year']),d['phone']))
        conn.commit(); flash('Student added successfully.', 'success')
    except sqlite3.IntegrityError:
        flash('Student ID or email already exists.', 'error')
    conn.close(); return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    conn = get_db()
    student = conn.execute('SELECT * FROM students WHERE id=?', (id,)).fetchone()
    if not student:
        conn.close(); flash('Student not found.', 'error'); return redirect(url_for('index'))
    if request.method == 'POST':
        d = form_data(); error = validate(d)
        if error:
            conn.close(); flash(error, 'error'); return redirect(url_for('edit', id=id))
        try:
            conn.execute('''UPDATE students SET student_id=?,name=?,email=?,department=?,year=?,phone=?
                WHERE id=?''', (d['student_id'],d['name'],d['email'],d['department'],int(d['year']),d['phone'],id))
            conn.commit(); conn.close(); flash('Student updated successfully.', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close(); flash('Student ID or email already exists.', 'error')
            return redirect(url_for('edit', id=id))
    conn.close(); return render_template('edit.html', student=student)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db(); cur = conn.execute('DELETE FROM students WHERE id=?', (id,))
    conn.commit(); conn.close()
    flash('Student deleted successfully.' if cur.rowcount else 'Student not found.',
          'success' if cur.rowcount else 'error')
    return redirect(url_for('index'))

def json_validation(d):
    required = ['student_id','name','email','department','year','phone']
    if any(not str(d.get(k, '')).strip() for k in required): return 'All fields are required.'
    if not valid_email(str(d['email'])): return 'Invalid email address.'
    try:
        if int(d['year']) not in range(1,5): raise ValueError
    except (ValueError, TypeError): return 'Year must be between 1 and 4.'
    return None

@app.route('/api/students/', methods=['GET'])
def api_all():
    conn = get_db(); rows = [dict(x) for x in conn.execute('SELECT * FROM students ORDER BY id DESC')]
    conn.close(); return jsonify(rows)

@app.route('/api/students/<int:id>/', methods=['GET'])
def api_one(id):
    conn = get_db(); row = conn.execute('SELECT * FROM students WHERE id=?',(id,)).fetchone(); conn.close()
    return (jsonify(dict(row)),200) if row else (jsonify({'error':'Student not found'}),404)

@app.route('/api/students/', methods=['POST'])
def api_create():
    d = request.get_json(silent=True) or {}; error = json_validation(d)
    if error: return jsonify({'error':error}),400
    conn = get_db()
    try:
        cur = conn.execute('''INSERT INTO students(student_id,name,email,department,year,phone)
            VALUES(?,?,?,?,?,?)''', (d['student_id'],d['name'],d['email'],d['department'],int(d['year']),d['phone']))
        conn.commit(); row = conn.execute('SELECT * FROM students WHERE id=?',(cur.lastrowid,)).fetchone()
        conn.close(); return jsonify(dict(row)),201
    except sqlite3.IntegrityError:
        conn.close(); return jsonify({'error':'Student ID or email already exists.'}),409

@app.route('/api/students/<int:id>/', methods=['PUT','PATCH'])
def api_update(id):
    d = request.get_json(silent=True) or {}; error = json_validation(d)
    if error: return jsonify({'error':error}),400
    conn = get_db()
    if not conn.execute('SELECT id FROM students WHERE id=?',(id,)).fetchone():
        conn.close(); return jsonify({'error':'Student not found'}),404
    try:
        conn.execute('''UPDATE students SET student_id=?,name=?,email=?,department=?,year=?,phone=?
            WHERE id=?''', (d['student_id'],d['name'],d['email'],d['department'],int(d['year']),d['phone'],id))
        conn.commit(); row = conn.execute('SELECT * FROM students WHERE id=?',(id,)).fetchone()
        conn.close(); return jsonify(dict(row))
    except sqlite3.IntegrityError:
        conn.close(); return jsonify({'error':'Student ID or email already exists.'}),409

@app.route('/api/students/<int:id>/', methods=['DELETE'])
def api_delete(id):
    conn = get_db(); cur = conn.execute('DELETE FROM students WHERE id=?',(id,))
    conn.commit(); conn.close()
    return (jsonify({'message':'Student deleted successfully'}),200) if cur.rowcount else (jsonify({'error':'Student not found'}),404)

if __name__ == '__main__':
    init_db(); app.run(debug=True)
