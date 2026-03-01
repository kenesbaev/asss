from app import create_app
from extensions import db
from models import User, Assignment, Setting, Department, Subject, TeacherSubject, TeacherStudent, News, Book
from datetime import datetime, timedelta
from config import Config
import random
import string
import os

def seed():
    app = create_app()
    with app.app_context():
        # Create Demo Users
        users = [
            {'username': 'muxammed', 'password': 'muxammed123', 'role': 'student', 'full_name': 'Muxammed'},
            {'username': 'bibiynaz', 'password': 'bibiynaz123', 'role': 'teacher', 'full_name': 'Bibiynaz'},
            {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'full_name': 'Administrator'}
        ]
        
        for u_data in users:
            if not db.session.query(User).filter_by(username=u_data['username']).first():
                user = User(
                    username=u_data['username'], 
                    role=u_data['role'],
                    full_name=u_data.get('full_name'),
                    email=f"{u_data['username']}@example.com"
                )
                user.set_password(u_data['password'])
                db.session.add(user)
                print(f"Created user: {u_data['username']}")
            else:
                print(f"User {u_data['username']} already exists.")
        
        db.session.commit()

        # Create departments
        departments = [
            {'name': 'Computer Science', 'description': 'Department of Computer Science'},
            {'name': 'Mathematics', 'description': 'Department of Mathematics'},
            {'name': 'Physics', 'description': 'Department of Physics'}
        ]
        
        for dept_data in departments:
            if not db.session.query(Department).filter_by(name=dept_data['name']).first():
                dept = Department(
                    name=dept_data['name'],
                    description=dept_data['description']
                )
                db.session.add(dept)
                print(f'Created department: {dept_data["name"]}')
        
        db.session.commit()

        # Create subjects
        subjects = [
            {'name': 'System Programming', 'code': 'SP101'},
            {'name': 'Mathematics', 'code': 'MATH101'},
            {'name': 'Physics', 'code': 'PHYS101'},
            {'name': 'Algorithms', 'code': 'ALG101'},
            {'name': 'Database Systems', 'code': 'DB101'}
        ]
        
        cs_dept = db.session.query(Department).filter_by(name='Computer Science').first()
        math_dept = db.session.query(Department).filter_by(name='Mathematics').first()
        physics_dept = db.session.query(Department).filter_by(name='Physics').first()
        
        for subj_data in subjects:
            if not db.session.query(Subject).filter_by(name=subj_data['name']).first():
                # Определяем отдел для предмета
                if 'Programming' in subj_data['name'] or 'Algorithms' in subj_data['name'] or 'Database' in subj_data['name']:
                    dept_id = cs_dept.id if cs_dept else None
                elif 'Mathematics' in subj_data['name']:
                    dept_id = math_dept.id if math_dept else None
                elif 'Physics' in subj_data['name']:
                    dept_id = physics_dept.id if physics_dept else None
                else:
                    dept_id = None
                
                subj = Subject(
                    name=subj_data['name'], 
                    code=subj_data['code'],
                    department_id=dept_id
                )
                db.session.add(subj)
                print(f'Created subject: {subj_data["name"]}')
        db.session.commit()

        # Assign teacher to subjects
        teacher = db.session.query(User).filter_by(role='teacher').first()
        sys_prog_subj = db.session.query(Subject).filter_by(name='System Programming').first()
        math_subj = db.session.query(Subject).filter_by(name='Mathematics').first()
        
        if teacher and sys_prog_subj:
            if not db.session.query(TeacherSubject).filter_by(
                teacher_id=teacher.id, subject_id=sys_prog_subj.id
            ).first():
                ts = TeacherSubject(teacher_id=teacher.id, subject_id=sys_prog_subj.id)
                db.session.add(ts)
                print(f'Assigned System Programming to teacher {teacher.username}')
        
        if teacher and math_subj:
            if not db.session.query(TeacherSubject).filter_by(
                teacher_id=teacher.id, subject_id=math_subj.id
            ).first():
                ts = TeacherSubject(teacher_id=teacher.id, subject_id=math_subj.id)
                db.session.add(ts)
                print(f'Assigned Mathematics to teacher {teacher.username}')
        
        db.session.commit()

        # Assign students to teacher for System Programming
        students = db.session.query(User).filter_by(role='student').all()
        if teacher and students and sys_prog_subj:
            for s in students:
                existing = db.session.query(TeacherStudent).filter_by(
                    teacher_id=teacher.id, 
                    student_id=s.id, 
                    subject_id=sys_prog_subj.id
                ).first()
                if not existing:
                    ts = TeacherStudent(
                        teacher_id=teacher.id, 
                        student_id=s.id, 
                        subject_id=sys_prog_subj.id
                    )
                    db.session.add(ts)
            db.session.commit()
            print(f'Assigned {len(students)} students to teacher {teacher.username} for {sys_prog_subj.name}')

        # Create a sample assignment if none exists
        if teacher and sys_prog_subj and not db.session.query(Assignment).first():
            new_assignment = Assignment(
                title='System Programming Lab 1',
                description='Implement a basic shell in C or Python. Include all 9 sections in your report.',
                deadline=datetime.utcnow() + timedelta(days=7),
                teacher_id=teacher.id,
                subject_id=sys_prog_subj.id,
                assignment_type='practical',
                course='Computer Science'
            )
            db.session.add(new_assignment)
            print("Created sample assignment.")

        # Create default settings
        for key, value in Config.DEFAULT_SETTINGS.items():
            if not db.session.query(Setting).filter_by(key=key).first():
                setting = Setting(
                    key=key,
                    value=value,
                    category='detection' if 'threshold' in key 
                            else 'file' if 'file' in key 
                            else 'general'
                )
                db.session.add(setting)
                print(f"Created setting: {key} = {value}")
        
        db.session.commit()
        
        # Create sample news
        if not db.session.query(News).first():
            admin_user = db.session.query(User).filter_by(role='admin').first()
            news_items = [
                {
                    'title': 'Добро пожаловать в AI Assistant!',
                    'content': 'Мы рады приветствовать вас в нашей системе. AI Assistant поможет вам эффективно управлять учебным процессом.',
                    'author_id': admin_user.id if admin_user else None
                },
                {
                    'title': 'Новые возможности платформы',
                    'content': 'Добавлены новые функции для преподавателей и студентов. Теперь вы можете создавать задания с автоматической проверкой AI.',
                    'author_id': admin_user.id if admin_user else None
                }
            ]
            
            for news_data in news_items:
                news = News(
                    title=news_data['title'],
                    content=news_data['content'],
                    author_id=news_data['author_id'],
                    is_published=True
                )
                db.session.add(news)
                print(f"Created news: {news_data['title']}")
            
                db.session.commit()

        # Create sample books
        if not db.session.query(Book).first():
            books_folder = os.path.join(os.getcwd(), 'uploads', 'books')
            covers_folder = os.path.join(books_folder, 'covers')
            
            if not os.path.exists(books_folder):
                os.makedirs(books_folder)
            if not os.path.exists(covers_folder):
                os.makedirs(covers_folder)

            # Helper to create a simple BMP image
            def create_bmp(path, color):
                # BMP Header (14 bytes) + DIB Header (40 bytes) = 54 bytes
                # 100x140 px, 24-bit per pixel
                width, height = 100, 140
                row_size = (width * 3 + 3) & ~3 # Align to 4 bytes
                data_size = row_size * height
                file_size = 54 + data_size
                
                with open(path, 'wb') as f:
                    # BMP Header
                    f.write(b'BM')
                    f.write(file_size.to_bytes(4, 'little'))
                    f.write(b'\x00\x00\x00\x00') # Reserved
                    f.write(b'\x36\x00\x00\x00') # Offset (54)
                    
                    # DIB Header (BITMAPINFOHEADER)
                    f.write(b'\x28\x00\x00\x00') # Header size (40)
                    f.write(width.to_bytes(4, 'little'))
                    f.write(height.to_bytes(4, 'little'))
                    f.write(b'\x01\x00') # Planes
                    f.write(b'\x18\x00') # BPP (24)
                    f.write(b'\x00\x00\x00\x00') # Compression (BI_RGB)
                    f.write(data_size.to_bytes(4, 'little'))
                    f.write(b'\x00\x00\x00\x00') # X PPM
                    f.write(b'\x00\x00\x00\x00') # Y PPM
                    f.write(b'\x00\x00\x00\x00') # Colors used
                    f.write(b'\x00\x00\x00\x00') # Important colors
                    
                    # Pixel data (BGR format), bottom-up
                    b, g, r = color
                    row = bytes([b, g, r]) * width
                    padding = b'\x00' * (row_size - len(row))
                    for _ in range(height):
                        f.write(row + padding)

            # Get subjects
            subj_sp = db.session.query(Subject).filter_by(name='System Programming').first()
            subj_math = db.session.query(Subject).filter_by(name='Mathematics').first()
            subj_algo = db.session.query(Subject).filter_by(name='Algorithms').first()
            subj_db = db.session.query(Subject).filter_by(name='Database Systems').first() # Created in previous step? Or seed creates it
            
            # Fallback if subject not found (though seed creates them above)
            s_sp_id = subj_sp.id if subj_sp else None
            s_math_id = subj_math.id if subj_math else None
            s_algo_id = subj_algo.id if subj_algo else None
            s_db_id = subj_db.id if subj_db else None
            
            sample_books = [
                {
                    'title': 'Программирование на Python', 
                    'author': 'Гвидо ван Россум', 
                    'file_name': 'python_prog.pdf',
                    'cover_name': 'python_cover.bmp', 
                    'subject_id': s_sp_id,
                    'color': (50, 100, 200) # Blue-ish
                },
                {
                    'title': 'Алгоритмы и структуры данных', 
                    'author': 'Никлаус Вирт', 
                    'file_name': 'algorithms.pdf',
                    'cover_name': 'algo_cover.bmp',
                    'subject_id': s_algo_id,
                    'color': (200, 50, 50) # Red-ish
                },
                {
                    'title': 'Базы данных. Основы', 
                    'author': 'Крис Дейт', 
                    'file_name': 'databases.pdf',
                    'cover_name': 'db_cover.bmp',
                    'subject_id': s_db_id,
                    'color': (50, 200, 50) # Green-ish
                },
                {
                    'title': 'Математика для инженеров', 
                    'author': 'Г. Крейсзик', 
                    'file_name': 'eng_math.pdf',
                    'cover_name': 'math_cover.bmp',
                    'subject_id': s_math_id,
                    'color': (200, 200, 50) # Yellow-ish
                },
                {
                    'title': 'Компьютерные сети', 
                    'author': 'Эндрю Таненбаум', 
                    'file_name': 'networks.pdf',
                    'cover_name': 'networks_cover.bmp',
                    'subject_id': s_sp_id, # Reusing SP or general
                    'color': (100, 100, 200)
                }
            ]
            
            for b_data in sample_books:
                # Create dummy PDF file
                file_path = os.path.join(books_folder, b_data['file_name'])
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n")
                
                # Create dummy Cover
                cover_path = os.path.join(covers_folder, b_data['cover_name'])
                if not os.path.exists(cover_path):
                    create_bmp(cover_path, b_data['color'])
                
                book = Book(
                    title=b_data['title'],
                    author=b_data['author'],
                    file_path=file_path,
                    cover_image=cover_path,
                    subject_id=b_data['subject_id']
                )
                db.session.add(book)
                print(f"Created book: {b_data['title']}")
            
            db.session.commit()
        
        # Create admin.txt with initial entry
        import os
        if not os.path.exists('admin.txt'):
            with open('admin.txt', 'w', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SYSTEM_START | System | Application initialized\n")
            print("Created admin.txt log file.")

if __name__ == '__main__':
    seed()