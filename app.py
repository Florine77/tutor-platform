from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATABASE = 'tutor.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade TEXT,
            subject TEXT,
            weaknesses TEXT,
            goal TEXT,
            personality TEXT,
            attention TEXT,
            device TEXT,
            parent_contact TEXT,
            parent_notes TEXT,
            before_score REAL,
            after_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            title TEXT,
            objectives TEXT,
            knowledge_points TEXT,
            examples TEXT,
            expected_problems TEXT,
            materials_link TEXT,
            homework TEXT,
            estimated_minutes_warmup INTEGER DEFAULT 5,
            estimated_minutes_teaching INTEGER DEFAULT 20,
            estimated_minutes_practice INTEGER DEFAULT 20,
            estimated_minutes_quiz INTEGER DEFAULT 10,
            estimated_minutes_summary INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lesson_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_plan_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            mastered TEXT,
            not_mastered TEXT,
            repeated_mistakes TEXT,
            attitude_score INTEGER,
            time_review TEXT,
            self_reflection TEXT,
            parent_feedback TEXT,
            homework_assigned TEXT,
            homework_deadline TEXT,
            next_topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_plan_id) REFERENCES lesson_plans(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            knowledge_point TEXT,
            question TEXT,
            wrong_answer TEXT,
            correct_answer TEXT,
            reason TEXT,
            source TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stage_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            test_title TEXT,
            score REAL,
            total_score REAL,
            notes TEXT,
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    
    db.commit()
    db.close()

if not os.path.exists(DATABASE):
    init_db()
else:
    init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students', methods=['GET'])
def get_students():
    db = get_db()
    students = db.execute('SELECT * FROM students ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(s) for s in students])

@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.json
    db = get_db()
    cursor = db.execute('''
        INSERT INTO students (name, grade, subject, weaknesses, goal, personality, attention, device, parent_contact, parent_notes, before_score, after_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data.get('grade',''), data.get('subject',''), data.get('weaknesses',''), 
          data.get('goal',''), data.get('personality',''), data.get('attention',''), 
          data.get('device',''), data.get('parent_contact',''), data.get('parent_notes',''),
          data.get('before_score'), data.get('after_score')))
    db.commit()
    student_id = cursor.lastrowid
    db.close()
    return jsonify({'id': student_id, 'message': '学生添加成功'}), 201

@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.json
    db = get_db()
    db.execute('''
        UPDATE students SET name=?, grade=?, subject=?, weaknesses=?, goal=?, personality=?, attention=?, device=?, parent_contact=?, parent_notes=?, before_score=?, after_score=?
        WHERE id=?
    ''', (data['name'], data.get('grade',''), data.get('subject',''), data.get('weaknesses',''),
          data.get('goal',''), data.get('personality',''), data.get('attention',''),
          data.get('device',''), data.get('parent_contact',''), data.get('parent_notes',''),
          data.get('before_score'), data.get('after_score'), id))
    db.commit()
    db.close()
    return jsonify({'message': '学生信息更新成功'})

@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    db = get_db()
    db.execute('DELETE FROM lesson_reviews WHERE student_id=?', (id,))
    db.execute('DELETE FROM lesson_plans WHERE student_id=?', (id,))
    db.execute('DELETE FROM error_book WHERE student_id=?', (id,))
    db.execute('DELETE FROM stage_tests WHERE student_id=?', (id,))
    db.execute('DELETE FROM students WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({'message': '学生及所有关联数据已删除'})

@app.route('/api/lesson-plans', methods=['GET'])
def get_lesson_plans():
    student_id = request.args.get('student_id')
    db = get_db()
    if student_id:
        plans = db.execute('SELECT * FROM lesson_plans WHERE student_id=? ORDER BY created_at DESC', (student_id,)).fetchall()
    else:
        plans = db.execute('SELECT * FROM lesson_plans ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(p) for p in plans])

@app.route('/api/lesson-plans', methods=['POST'])
def add_lesson_plan():
    data = request.json
    db = get_db()
    cursor = db.execute('''
        INSERT INTO lesson_plans (student_id, title, objectives, knowledge_points, examples, expected_problems, materials_link, homework,
            estimated_minutes_warmup, estimated_minutes_teaching, estimated_minutes_practice, estimated_minutes_quiz, estimated_minutes_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['student_id'], data.get('title',''), data.get('objectives',''), data.get('knowledge_points',''),
          data.get('examples',''), data.get('expected_problems',''), data.get('materials_link',''), data.get('homework',''),
          data.get('estimated_minutes_warmup',5), data.get('estimated_minutes_teaching',20), 
          data.get('estimated_minutes_practice',20), data.get('estimated_minutes_quiz',10), data.get('estimated_minutes_summary',5)))
    db.commit()
    plan_id = cursor.lastrowid
    db.close()
    return jsonify({'id': plan_id, 'message': '备课记录保存成功'}), 201

@app.route('/api/lesson-plans/<int:id>', methods=['DELETE'])
def delete_lesson_plan(id):
    db = get_db()
    db.execute('DELETE FROM lesson_reviews WHERE lesson_plan_id=?', (id,))
    db.execute('DELETE FROM lesson_plans WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({'message': '备课记录及关联复盘已删除'})

@app.route('/api/lesson-reviews', methods=['GET'])
def get_lesson_reviews():
    student_id = request.args.get('student_id')
    db = get_db()
    if student_id:
        reviews = db.execute('SELECT * FROM lesson_reviews WHERE student_id=? ORDER BY created_at DESC', (student_id,)).fetchall()
    else:
        reviews = db.execute('SELECT * FROM lesson_reviews ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in reviews])

@app.route('/api/lesson-reviews', methods=['POST'])
def add_lesson_review():
    data = request.json
    db = get_db()
    cursor = db.execute('''
        INSERT INTO lesson_reviews (lesson_plan_id, student_id, mastered, not_mastered, repeated_mistakes, attitude_score, time_review, self_reflection, parent_feedback, homework_assigned, homework_deadline, next_topic)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['lesson_plan_id'], data['student_id'], data.get('mastered',''), data.get('not_mastered',''),
          data.get('repeated_mistakes',''), data.get('attitude_score',3), data.get('time_review',''),
          data.get('self_reflection',''), data.get('parent_feedback',''), data.get('homework_assigned',''),
          data.get('homework_deadline',''), data.get('next_topic','')))
    db.commit()
    review_id = cursor.lastrowid
    db.close()
    return jsonify({'id': review_id, 'message': '复盘记录保存成功'}), 201

@app.route('/api/lesson-reviews/<int:id>', methods=['DELETE'])
def delete_lesson_review(id):
    db = get_db()
    db.execute('DELETE FROM lesson_reviews WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({'message': '复盘记录已删除'})

@app.route('/api/lesson-reviews/<int:id>', methods=['PUT'])
def update_lesson_review(id):
    data = request.json
    db = get_db()
    db.execute('''
        UPDATE lesson_reviews SET mastered=?, not_mastered=?, repeated_mistakes=?, attitude_score=?, time_review=?, self_reflection=?, parent_feedback=?, homework_assigned=?, homework_deadline=?, next_topic=?
        WHERE id=?
    ''', (data.get('mastered',''), data.get('not_mastered',''), data.get('repeated_mistakes',''),
          data.get('attitude_score',3), data.get('time_review',''), data.get('self_reflection',''),
          data.get('parent_feedback',''), data.get('homework_assigned',''), data.get('homework_deadline',''), data.get('next_topic',''), id))
    db.commit()
    db.close()
    return jsonify({'message': '复盘记录更新成功'})

@app.route('/api/error-book', methods=['GET'])
def get_error_book():
    student_id = request.args.get('student_id')
    db = get_db()
    if student_id:
        errors = db.execute('SELECT * FROM error_book WHERE student_id=? ORDER BY added_at DESC', (student_id,)).fetchall()
    else:
        errors = db.execute('SELECT * FROM error_book ORDER BY added_at DESC').fetchall()
    db.close()
    return jsonify([dict(e) for e in errors])

@app.route('/api/error-book', methods=['POST'])
def add_error():
    data = request.json
    db = get_db()
    db.execute('''
        INSERT INTO error_book (student_id, knowledge_point, question, wrong_answer, correct_answer, reason, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['student_id'], data.get('knowledge_point',''), data.get('question',''),
          data.get('wrong_answer',''), data.get('correct_answer',''), data.get('reason',''), data.get('source','')))
    db.commit()
    db.close()
    return jsonify({'message': '错题添加成功'}), 201

@app.route('/api/error-book/<int:id>', methods=['DELETE'])
def delete_error(id):
    db = get_db()
    db.execute('DELETE FROM error_book WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({'message': '错题已删除'})

@app.route('/api/stage-tests', methods=['GET'])
def get_stage_tests():
    student_id = request.args.get('student_id')
    db = get_db()
    if student_id:
        tests = db.execute('SELECT * FROM stage_tests WHERE student_id=? ORDER BY test_date DESC', (student_id,)).fetchall()
    else:
        tests = db.execute('SELECT * FROM stage_tests ORDER BY test_date DESC').fetchall()
    db.close()
    return jsonify([dict(t) for t in tests])

@app.route('/api/stage-tests', methods=['POST'])
def add_stage_test():
    data = request.json
    db = get_db()
    db.execute('''
        INSERT INTO stage_tests (student_id, test_title, score, total_score, notes, test_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['student_id'], data.get('test_title',''), data.get('score',0), data.get('total_score',100), data.get('notes',''), data.get('test_date', datetime.now().strftime('%Y-%m-%d'))))
    db.commit()
    db.close()
    return jsonify({'message': '小测记录添加成功'}), 201

@app.route('/api/stage-tests/<int:id>', methods=['DELETE'])
def delete_stage_test(id):
    db = get_db()
    db.execute('DELETE FROM stage_tests WHERE id=?', (id,))
    db.commit()
    db.close()
    return jsonify({'message': '小测记录已删除'})

@app.route('/api/generate-feedback', methods=['POST'])
def generate_feedback():
    data = request.json
    mastered = data.get('mastered', '')
    not_mastered = data.get('not_mastered', '')
    attitude = data.get('attitude_score', 3)
    next_topic = data.get('next_topic', '')
    
    attitude_text = {5:'非常积极', 4:'比较认真', 3:'态度端正', 2:'需要提醒', 1:'注意力不集中'}.get(attitude, '态度端正')
    
    feedback = f'''【本次课程反馈】

已掌握内容：{mastered if mastered else '按计划完成教学'}

需要加强：{not_mastered if not_mastered else '暂无特别薄弱环节'}

课堂表现：学生{attitude_text}

作业：请按时完成布置的练习

下次课重点：{next_topic if next_topic else '按进度继续推进'}

如有疑问，随时沟通！'''
    
    return jsonify({'feedback': feedback})

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    db = get_db()
    
    total_lessons = db.execute('SELECT COUNT(*) as count FROM lesson_reviews').fetchone()['count']
    total_students = db.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    
    student_lessons = db.execute('''
        SELECT s.name, COUNT(lr.id) as count 
        FROM students s LEFT JOIN lesson_reviews lr ON s.id = lr.student_id 
        GROUP BY s.id
    ''').fetchall()
    
    db.close()
    
    return jsonify({
        'total_lessons': total_lessons,
        'total_students': total_students,
        'student_lessons': [dict(s) for s in student_lessons]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)