from flask import Flask, render_template, request, jsonify, session, g
from flask_cors import CORS
from config import Config
from extensions import db
from datetime import datetime, timedelta, date
import os
import jwt
from models import User, Department, Subject, TeacherSubject, TeacherStudent, Assignment, Submission, News, Setting, Notification, ActivityLog, StudentSubject, AcademicRating, UserProfile, Group
from sqlalchemy.orm import Session, joinedload
import random

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = Config.SECRET_KEY

    CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
         allow_headers=["Content-Type", "Authorization"])
    
    db.init_app(app)
    
    # Configure AI Service
    from services.ai_service import AIService
    AIService.configure()

    # Register Blueprints
    from routes import auth, assignments, subjects, users, admin, literature
    app.register_blueprint(auth.bp)
    app.register_blueprint(assignments.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(literature.bp)

    @app.before_request
    def check_token():
        # Skip token check for static files, login, register, and health endpoints
        if (request.path.startswith('/static') or 
            request.path in ['/login', '/register', '/', '/health'] or
            request.path.startswith('/auth/') or
            request.path.startswith('/api/literature/cover') or
            not request.path.startswith('/api')):
            return

        token = request.headers.get('Authorization') or session.get('token')
        if not token:
            return jsonify({'message': 'РўРѕРєРµРЅ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚!'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]

            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user_id = data['user_id']

            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                return jsonify({'message': 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ РёР»Рё Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅ!'}), 401

            g.current_user = user

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ С‚РѕРєРµРЅР° РёСЃС‚РµРє!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'РќРµРґРµР№СЃС‚РІРёС‚РµР»СЊРЅС‹Р№ С‚РѕРєРµРЅ!'}), 401
        except Exception as e:
            return jsonify({'message': f'РћС€РёР±РєР° Р°СѓС‚РµРЅС‚РёС„РёРєР°С†РёРё: {str(e)}'}), 401

    # Page Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/test-login')
    def test_login_page():
        return render_template('test_login.html')

    @app.route('/login')
    def login_page():
        return render_template('index.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard/student')
    def student_dashboard():
        return render_template('student_dashboard.html')

    @app.route('/dashboard/teacher')
    def teacher_dashboard():
        return render_template('teacher_dashboard.html')

    @app.route('/dashboard/admin')
    def admin_dashboard():
        return render_template('admin_dashboard.html')

    @app.route('/dashboard/submissions/<int:assignment_id>')
    def view_assignment_submissions(assignment_id):
        return render_template('assignment_submissions.html', assignment_id=assignment_id)

    @app.route('/submit/<int:assignment_id>')
    def submit_page(assignment_id):
        return render_template('submit_assignment.html', assignment_id=assignment_id)

    @app.route('/results/<int:submission_id>')
    def results_page(submission_id):
        return render_template('submission_detail.html', submission_id=submission_id)


    @app.route('/api/teacher/students')
    def teacher_students_stats():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            
            if not current_user or current_user.role != 'teacher':
                return jsonify({'message': 'Unauthorized'}), 403
            
            # IDs of students from groups owned by this teacher
            groups = db.session.query(Group).filter_by(teacher_id=current_user.id).all()
            group_ids = [g.id for g in groups]
            group_student_ids = {u.id for u in db.session.query(User).filter(User.group_id.in_(group_ids)).all()} if group_ids else set()

            # Combined IDs: Linked via groups OR Explicitly linked via TeacherStudent OR submitted teacher's assignments
            linked_student_ids = {ts.student_id for ts in db.session.query(TeacherStudent).filter_by(teacher_id=current_user.id).all()}
            
            teacher_assignments = db.session.query(Assignment).filter_by(teacher_id=current_user.id).all()
            ta_ids = [a.id for a in teacher_assignments]
            submitting_student_ids = {s.student_id for s in db.session.query(Submission).filter(Submission.assignment_id.in_(ta_ids)).all()}
            
            all_student_ids = linked_student_ids.union(submitting_student_ids).union(group_student_ids)
            students = db.session.query(User).filter(User.id.in_(all_student_ids)).all()
            
            output = []
            total_students = len(students)
            total_completed = 0
            total_score = 0
            
            for student in students:
                # Submissions for this teacher's assignments
                subs = db.session.query(Submission).filter(
                    Submission.student_id == student.id,
                    Submission.assignment_id.in_(ta_ids)
                ).all()
                completed_subs = [s for s in subs if s.overall_score is not None]
                student_total_score = sum(sub.overall_score for sub in completed_subs)
                
                total_completed += len(completed_subs)
                total_score += student_total_score
                
                output.append({
                    'id': student.id,
                    'username': student.username,
                    'avatar': f"https://ui-avatars.com/api/?name={student.username}&background=random",
                    'submitted_count': len(subs),
                    'completed_count': len(completed_subs),
                    'total_score': round(student_total_score, 1)
                })
            
            avg_score = total_score / total_completed if total_completed > 0 else 0
            
            return jsonify({
                'students': output,
                'stats': {
                    'total_students': total_students,
                    'total_completed': total_completed,
                    'average_score': round(avg_score, 1)
                }
            })
            
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    @app.route('/api/admin/teacher/<int:teacher_id>/students', methods=['GET', 'POST', 'DELETE'])
    def admin_teacher_students(teacher_id):
        teacher = db.session.get(User, teacher_id)
        if not teacher or teacher.role != 'teacher':
            return jsonify({'message': 'Teacher not found'}), 404
        
        if request.method == 'GET':
            teacher_students = db.session.query(TeacherStudent).filter_by(
                teacher_id=teacher_id
            ).options(
                joinedload(TeacherStudent.student),
                joinedload(TeacherStudent.subject)
            ).all()
            
            output = []
            for ts in teacher_students:
                student = ts.student
                subject = ts.subject
                
                # Get student's submissions for this subject
                submissions = db.session.query(Submission).filter_by(
                    student_id=student.id
                ).join(Assignment).filter(
                    Assignment.subject_id == subject.id
                ).all()
                
                completed = len([s for s in submissions if s.overall_score is not None])
                total_score = sum(s.overall_score for s in submissions if s.overall_score is not None)
                
                output.append({
                    'id': ts.id,
                    'student_id': student.id,
                    'student_username': student.username,
                    'student_full_name': student.full_name,
                    'student_email': student.email,
                    'subject_id': subject.id,
                    'subject_name': subject.name,
                    'submission_count': len(submissions),
                    'completed_count': completed,
                    'total_score': total_score,
                    'enrolled_at': ts.created_at.isoformat() if ts.created_at else None
                })
            
            return jsonify(output)
        
        elif request.method == 'POST':
            data = request.get_json()
            student_id = data.get('student_id')
            subject_id = data.get('subject_id')
            
            if not student_id or not subject_id:
                return jsonify({'message': 'Student ID and Subject ID are required'}), 400
            
            # Check if student exists
            student = db.session.get(User, student_id)
            if not student or student.role != 'student':
                return jsonify({'message': 'Student not found'}), 404
            
            # Check if subject exists
            subject = db.session.get(Subject, subject_id)
            if not subject:
                return jsonify({'message': 'Subject not found'}), 404
            
            # Check if relationship already exists
            existing = db.session.query(TeacherStudent).filter_by(
                teacher_id=teacher_id,
                student_id=student_id,
                subject_id=subject_id
            ).first()
            
            if existing:
                return jsonify({'message': 'Student already assigned to teacher for this subject'}), 400
            
            # Create relationship
            teacher_student = TeacherStudent(
                teacher_id=teacher_id,
                student_id=student_id,
                subject_id=subject_id
            )
            db.session.add(teacher_student)
            db.session.commit()
            
            # Create notification for student
            notification = Notification(
                student_id=student_id,
                assignment_id=None,
                title=f'РџСЂРёРєСЂРµРїР»РµРЅ Рє РїСЂРµРїРѕРґР°РІР°С‚РµР»СЋ',
                message=f'Р’С‹ Р±С‹Р»Рё РїСЂРёРєСЂРµРїР»РµРЅС‹ Рє РїСЂРµРїРѕРґР°РІР°С‚РµР»СЋ {teacher.username} РїРѕ РїСЂРµРґРјРµС‚Сѓ {subject.name}',
                type='system',
                is_read=False
            )
            db.session.add(notification)
            db.session.commit()
            
            # Log activity
            log = ActivityLog(
                user_id=g.current_user.id,
                action='ASSIGN_STUDENT',
                details=f"Assigned student {student.username} to teacher {teacher.username} for {subject.name}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'message': 'Student assigned successfully'}), 201
        
        elif request.method == 'DELETE':
            data = request.get_json()
            teacher_student_id = data.get('teacher_student_id')
            
            if not teacher_student_id:
                return jsonify({'message': 'TeacherStudent ID is required'}), 400
            
            teacher_student = db.session.get(TeacherStudent, teacher_student_id)
            if not teacher_student or teacher_student.teacher_id != teacher_id:
                return jsonify({'message': 'Assignment not found'}), 404
            
            db.session.delete(teacher_student)
            db.session.commit()
            
            # Log activity
            log = ActivityLog(
                user_id=g.current_user.id,
                action='REMOVE_STUDENT',
                details=f"Removed student from teacher {teacher.username}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'message': 'Student removed successfully'})

    @app.route('/api/admin/news', methods=['GET', 'POST'])
    def admin_news():
        if request.method == 'GET':
            news = db.session.query(News).order_by(News.created_at.desc()).all()
            output = []
            for item in news:
                output.append({
                    'id': item.id,
                    'title': item.title,
                    'content': item.content,
                    'author': item.author.username if item.author else 'System',
                    'is_published': item.is_published,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'updated_at': item.updated_at.isoformat() if item.updated_at else None
                })
            return jsonify(output)
        else:
            data = request.get_json()
            news = News(
                title=data['title'],
                content=data['content'],
                author_id=g.current_user.id,
                is_published=data.get('is_published', True)
            )
            db.session.add(news)
            db.session.commit()
            
            # Log activity
            log = ActivityLog(
                user_id=g.current_user.id,
                action='CREATE_NEWS',
                details=f"Created news: {news.title}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'message': 'News created successfully'}), 201

    @app.route('/api/admin/news/<int:news_id>', methods=['PUT', 'DELETE'])
    def admin_news_operations(news_id):
        news = db.session.get(News, news_id)
        if not news:
            return jsonify({'message': 'News not found'}), 404
        
        if request.method == 'PUT':
            data = request.get_json()
            if 'title' in data:
                news.title = data['title']
            if 'content' in data:
                news.content = data['content']
            if 'is_published' in data:
                news.is_published = data['is_published']
            db.session.commit()
            
            # Log activity
            log = ActivityLog(
                user_id=g.current_user.id,
                action='UPDATE_NEWS',
                details=f"Updated news: {news.title}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'message': 'News updated successfully'})
        else:
            db.session.delete(news)
            db.session.commit()
            
            # Log activity
            log = ActivityLog(
                user_id=g.current_user.id,
                action='DELETE_NEWS',
                details=f"Deleted news: {news.title}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'message': 'News deleted successfully'})

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'Ai Assistant Backend'}

    @app.route('/api/admin/logs')
    def get_admin_logs():
        try:
            if not os.path.exists('admin.txt'):
                return jsonify({'logs': []})
            with open('admin.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return jsonify({'logs': lines[-50:]})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/settings', methods=['GET', 'POST'])
    def admin_settings():
        if request.method == 'POST':
            data = request.get_json()
            for key, val in data.items():
                s = db.session.query(Setting).filter_by(key=key).first()
                if not s:
                    category = 'detection' if 'threshold' in key.lower() else \
                              'file' if 'file' in key.lower() else \
                              'general'
                    s = Setting(key=key, category=category)
                    db.session.add(s)
                s.value = str(val)
            db.session.commit()
            
            try:
                log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SETTINGS_UPDATE | Admin | Updated settings\n"
                with open('admin.txt', 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except:
                pass
            
            return jsonify({'message': 'Settings saved'})
        
        settings = {s.key: s.value for s in db.session.query(Setting).all()}
        for key, default_val in Config.DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = default_val
        
        return jsonify(settings)

    @app.route('/api/admin/stats')
    def admin_dashboard_stats():
        today = date.today()
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        total_users = db.session.query(User).count()
        total_teachers = db.session.query(User).filter_by(role='teacher', is_active=True).count()
        total_students = db.session.query(User).filter_by(role='student', is_active=True).count()
        
        submissions_today = db.session.query(Submission).filter(
            db.func.date(Submission.submitted_at) == today
        ).count()
        
        total_assignments = db.session.query(Assignment).count()
        
        active_assignments = db.session.query(Assignment).filter(
            (Assignment.deadline > datetime.utcnow()) | (Assignment.deadline.is_(None))
        ).count()
        
        recent_submissions = db.session.query(Submission).filter(
            Submission.submitted_at >= week_ago
        ).count()
        
        active_users = db.session.query(User).filter(
            User.last_seen >= week_ago
        ).count()
        
        total_news = db.session.query(News).count()
        
        total_departments = db.session.query(Department).count()
        
        return jsonify({
            'total_users': total_users,
            'total_teachers': total_teachers,
            'total_students': total_students,
            'submissions_today': submissions_today,
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'recent_submissions': recent_submissions,
            'active_users': active_users,
            'total_news': total_news,
            'total_departments': total_departments,
            'ai_speed': '0.7s',
            'health': '99.5%'
        })


    @app.route('/api/teacher/student/<int:student_id>')
    def teacher_student_detail(student_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user or current_user.role != 'teacher':
                return jsonify({'message': 'Unauthorized'}), 403
            
            # Verify if student is linked to teacher via group, direct link, or submission
            groups = db.session.query(Group).filter_by(teacher_id=current_user.id).all()
            group_ids = [g.id for g in groups]
            
            is_in_group = db.session.query(User).filter(User.id == student_id, User.group_id.in_(group_ids)).first() if group_ids else None
            is_linked = db.session.query(TeacherStudent).filter_by(teacher_id=current_user.id, student_id=student_id).first()
            
            teacher_assignments = db.session.query(Assignment).filter_by(teacher_id=current_user.id).all()
            ta_ids = [a.id for a in teacher_assignments]
            has_submitted = db.session.query(Submission).filter(Submission.student_id == student_id, Submission.assignment_id.in_(ta_ids)).first() if ta_ids else None

            if not any([is_in_group, is_linked, has_submitted]) and current_user.role != 'admin':
                return jsonify({'message': 'Student not found in your list'}), 404
            
            student = db.session.get(User, student_id)
            subs = db.session.query(Submission).filter_by(student_id=student_id).all()
            
            output_subs = []
            total_score = 0
            completed_count = 0
            for s in subs:
                assign = db.session.get(Assignment, s.assignment_id)
                output_subs.append({
                    'id': s.id,
                    'assignment_title': assign.title if assign else 'Unknown',
                    'assignment_course': assign.course if assign else 'Unknown',
                    'submitted_at': s.submitted_at.isoformat() if s.submitted_at else None,
                    'overall_score': s.overall_score or 0,
                    'ai_feedback': s.ai_feedback_summary or 'РќРµС‚ РєРѕРјРјРµРЅС‚Р°СЂРёСЏ'
                })
                if s.overall_score is not None:
                    total_score += s.overall_score
                    completed_count += 1
            
            avg_score = total_score / completed_count if completed_count > 0 else 0
            
            return jsonify({
                'student': {'id': student.id, 'username': student.username, 'full_name': student.full_name},
                'submissions': output_subs,
                'total_score': total_score,
                'avg_score': avg_score,
                'completed_count': completed_count
            })
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/activity')
    def teacher_student_activity():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user or current_user.role != 'teacher':
                return jsonify({'message': 'Unauthorized'}), 403
            
            # Get IDs of students linked to this teacher OR who submitted to them
            teacher_assignments = db.session.query(Assignment).filter_by(teacher_id=current_user.id).all()
            ta_ids = [a.id for a in teacher_assignments]
            
            linked_ids = {ts.student_id for ts in db.session.query(TeacherStudent).filter_by(teacher_id=current_user.id).all()}
            submitting_ids = {s.student_id for s in db.session.query(Submission).filter(Submission.assignment_id.in_(ta_ids)).all()}
            
            all_relevant_ids = list(linked_ids.union(submitting_ids))
            
            # Fetch activity logs for these students
            activities = db.session.query(ActivityLog).filter(ActivityLog.user_id.in_(all_relevant_ids)).order_by(ActivityLog.created_at.desc()).limit(100).all()
            
            output = []
            for a in activities:
                user = db.session.get(User, a.user_id)
                output.append({
                    'id': a.id,
                    'username': user.username if user else 'Unknown',
                    'action': a.action,
                    'timestamp': a.created_at.isoformat() if a.created_at else None
                })
            
            return jsonify(output)
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/groups')
    def get_teacher_groups():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user or current_user.role != 'teacher':
                return jsonify({'message': 'Unauthorized'}), 403
            
            groups = Group.query.filter_by(teacher_id=current_user.id).all()
            output = []
            for g in groups:
                student_count = User.query.filter_by(group_id=g.id).count()
                output.append({
                    'id': g.id,
                    'name': g.name,
                    'student_count': student_count,
                    'created_at': g.created_at.isoformat()
                })
            return jsonify(output)
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    @app.route('/api/teacher/groups/<int:group_id>/students')
    def get_group_students(group_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user or current_user.role != 'teacher':
                return jsonify({'message': 'Unauthorized'}), 403
            
            group = Group.query.get_or_404(group_id)
            if group.teacher_id != current_user.id and current_user.role != 'admin':
                return jsonify({'message': 'Unauthorized'}), 403
            
            students = User.query.filter_by(group_id=group_id, role='student').all()
            output = []
            for s in students:
                output.append({
                    'id': s.id,
                    'username': s.username,
                    'email': s.email
                })
            return jsonify(output)
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    # Notification Routes for students
    @app.route('/api/notifications', methods=['GET'])
    def get_notifications():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                return jsonify({'message': 'Unauthorized'}), 403
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        notifications = db.session.query(Notification).filter_by(
            student_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(50).all()
        
        unread_count = db.session.query(Notification).filter_by(
            student_id=current_user.id, is_read=False
        ).count()
        
        output = []
        for n in notifications:
            output.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.type,
                'is_read': n.is_read,
                'assignment_id': n.assignment_id,
                'created_at': n.created_at.isoformat() if n.created_at else None
            })
        
        return jsonify({
            'notifications': output,
            'unread_count': unread_count
        })

    @app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
    def mark_notification_read(notification_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                return jsonify({'message': 'Unauthorized'}), 403
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        notification = db.session.get(Notification, notification_id)
        if not notification:
            return jsonify({'message': 'Notification not found'}), 404
        
        if notification.student_id != current_user.id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'})

    @app.route('/api/notifications/read-all', methods=['POST'])
    def mark_all_notifications_read():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user:
                return jsonify({'message': 'Unauthorized'}), 403
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        db.session.query(Notification).filter_by(
            student_id=current_user.id, is_read=False
        ).update({'is_read': True})
        db.session.commit()
        
        return jsonify({'message': 'All notifications marked as read'})

    # API for academic ratings (for student)
    @app.route('/api/subjects/academic-ratings')
    def get_academic_ratings():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'Unauthorized'}), 403
            
            # Get student's subjects and ratings
            subjects = db.session.query(Subject).join(
                StudentSubject, StudentSubject.subject_id == Subject.id
            ).filter(StudentSubject.student_id == current_user.id).all()
            
            ratings = []
            for subject in subjects:
                # Get academic rating from AcademicRating table
                academic_rating = db.session.query(AcademicRating).filter_by(
                    student_id=current_user.id,
                    subject_id=subject.id
                ).first()
                
                if academic_rating:
                    ratings.append({
                        'subject_id': subject.id,
                        'subject_name': subject.name,
                        'rating': academic_rating.rating,
                        'total_assignments': academic_rating.total_assignments,
                        'completed_assignments': academic_rating.completed_assignments,
                        'average_score': academic_rating.average_score
                    })
                else:
                    # If no academic rating record, calculate from submissions
                    assignments = db.session.query(Assignment).filter_by(
                        subject_id=subject.id
                    ).all()
                    
                    submissions = db.session.query(Submission).filter_by(
                        student_id=current_user.id
                    ).join(Assignment).filter(Assignment.subject_id == subject.id).all()
                    
                    completed = len([s for s in submissions if s.overall_score is not None])
                    total = len(assignments)
                    avg_score = 0
                    if completed > 0:
                        avg_score = sum(s.overall_score for s in submissions if s.overall_score) / completed
                    
                    rating_value = min(5.0, avg_score / 20) if avg_score > 0 else 0
                    
                    # Create academic rating record
                    new_rating = AcademicRating(
                        student_id=current_user.id,
                        subject_id=subject.id,
                        rating=rating_value,
                        total_assignments=total,
                        completed_assignments=completed,
                        average_score=avg_score
                    )
                    db.session.add(new_rating)
                    db.session.commit()
                    
                    ratings.append({
                        'subject_id': subject.id,
                        'subject_name': subject.name,
                        'rating': rating_value,
                        'total_assignments': total,
                        'completed_assignments': completed,
                        'average_score': avg_score
                    })
            
            return jsonify(ratings)
            
        except Exception as e:
            return jsonify({'message': str(e)}), 500

    @app.route('/api/academic-report/pdf')
    def generate_academic_report_pdf():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'Unauthorized'}), 403
            
            # Get student's submissions with assignment details
            submissions = db.session.query(Submission).join(
                Assignment, Submission.assignment_id == Assignment.id
            ).filter(Submission.student_id == current_user.id).all()
            
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors
                from reportlab.lib.units import inch
                import io
                
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                story = []
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=12,
                    textColor=colors.HexColor('#4318FF')
                )
                
                story.append(Paragraph("РђРљРђР”Р•РњРР§Р•РЎРљРР™ РћРўР§Р•Рў", title_style))
                story.append(Spacer(1, 12))
                
                # Student info
                info_data = [
                    ["РЎС‚СѓРґРµРЅС‚:", current_user.username],
                    ["РџРѕР»РЅРѕРµ РёРјСЏ:", current_user.full_name or 'РќРµ СѓРєР°Р·Р°РЅРѕ'],
                    ["Email:", current_user.email or 'РќРµ СѓРєР°Р·Р°РЅ'],
                    ["Р”Р°С‚Р° РѕС‚С‡РµС‚Р°:", datetime.now().strftime('%d.%m.%Y')]
                ]
                
                info_table = Table(info_data, colWidths=[2*inch, 4*inch])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F4F0FF')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                ]))
                
                story.append(info_table)
                story.append(Spacer(1, 20))
                
                if submissions:
                    story.append(Paragraph("Р’Р«РџРћР›РќР•РќРќР«Р• Р—РђР”РђРќРРЇ:", styles['Heading2']))
                    
                    table_data = [["в„–", "Р—Р°РґР°РЅРёРµ", "РџСЂРµРґРјРµС‚", "Р”Р°С‚Р°", "РћС†РµРЅРєР°"]]
                    
                    for i, submission in enumerate(submissions, 1):
                        assignment = submission.assignment
                        submitted_date = submission.submitted_at.strftime('%d.%m.%Y') if submission.submitted_at else 'РќРµ СѓРєР°Р·Р°РЅР°'
                        score = f"{submission.overall_score}%" if submission.overall_score else 'РќРµ РѕС†РµРЅРµРЅРѕ'
                        
                        table_data.append([
                            str(i),
                            assignment.title[:30] + "..." if len(assignment.title) > 30 else assignment.title,
                            assignment.course or 'РћР±С‰РёР№',
                            submitted_date,
                            score
                        ])
                    
                    table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1*inch, 1*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4318FF')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
                    ]))
                    
                    story.append(table)
                
                doc.build(story)
                buffer.seek(0)
                
                from flask import make_response
                response = make_response(buffer.getvalue())
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="Academic_Report_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.pdf"'
                return response
                
            except ImportError:
                # Fallback to text
                report_content = f"""РђРљРђР”Р•РњРР§Р•РЎРљРР™ РћРўР§Р•Рў
РЎС‚СѓРґРµРЅС‚: {current_user.username}
Р”Р°С‚Р°: {datetime.now().strftime('%d.%m.%Y')}

РћС‚С‡РµС‚ СЃРіРµРЅРµСЂРёСЂРѕРІР°РЅ СЃРёСЃС‚РµРјРѕР№ AI Assistant."""
                
                from flask import make_response
                response = make_response(report_content)
                response.headers['Content-Type'] = 'text/plain; charset=utf-8'
                response.headers['Content-Disposition'] = f'attachment; filename="Academic_Report_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.txt"'
                return response
                
        except Exception as e:
            return jsonify({'message': f'Error generating report: {str(e)}'}), 500

    @app.route('/api/submissions/<int:submission_id>/pdf')
    def get_submission_pdf(submission_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'Unauthorized'}), 403
            
            submission = db.session.query(Submission).join(
                Assignment, Submission.assignment_id == Assignment.id
            ).filter(Submission.id == submission_id, Submission.student_id == current_user.id).first()
            
            if not submission:
                return jsonify({'message': 'Submission not found'}), 404
            
            # РџРѕРґРіРѕС‚Р°РІР»РёРІР°РµРј РґР°РЅРЅС‹Рµ РґР»СЏ PDF
            submission_data = {
                'assignment_title': submission.assignment.title,
                'student_name': current_user.username,
                'submitted_at': submission.submitted_at.strftime('%d.%m.%Y %H:%M') if submission.submitted_at else 'РќРµ СѓРєР°Р·Р°РЅР°',
                'overall_score': submission.overall_score or 0,
                'status': 'РџСЂРѕРІРµСЂРµРЅРѕ' if submission.overall_score else 'Р’ РѕР±СЂР°Р±РѕС‚РєРµ',
                'ai_comment': submission.ai_feedback_summary or 'РљРѕРјРјРµРЅС‚Р°СЂРёР№ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚',
                'ai_feedback_summary': submission.ai_feedback_summary or 'РљРѕРјРјРµРЅС‚Р°СЂРёР№ РѕС‚СЃСѓС‚СЃС‚РІСѓРµС‚',
                'criteria_scores': [
                    {'criterion': 'Р РµР»РµРІР°РЅС‚РЅРѕСЃС‚СЊ', 'score': min(100, (submission.overall_score or 0) + 20), 'comment': 'Р Р°Р±РѕС‚Р° СЃРѕРѕС‚РІРµС‚СЃС‚РІСѓРµС‚ С‚РµРјРµ Р·Р°РґР°РЅРёСЏ'},
                    {'criterion': 'РљР°С‡РµСЃС‚РІРѕ РєРѕРґР°', 'score': submission.overall_score or 0, 'comment': 'РћС†РµРЅРєР° РєР°С‡РµСЃС‚РІР° РїСЂРµРґРѕСЃС‚Р°РІР»РµРЅРЅРѕРіРѕ РєРѕРґР°'},
                    {'criterion': 'РћС„РѕСЂРјР»РµРЅРёРµ', 'score': max(0, (submission.overall_score or 0) - 10), 'comment': 'РљР°С‡РµСЃС‚РІРѕ РѕС„РѕСЂРјР»РµРЅРёСЏ СЂР°Р±РѕС‚С‹'}
                ],
                'recommendations': [
                    'РЈР»СѓС‡С€РёС‚СЊ РєРѕРјРјРµРЅС‚РёСЂРѕРІР°РЅРёРµ РєРѕРґР°',
                    'Р”РѕР±Р°РІРёС‚СЊ Р±РѕР»СЊС€Рµ РїСЂРёРјРµСЂРѕРІ',
                    'РџСЂРѕРІРµСЂРёС‚СЊ СЃРѕРѕС‚РІРµС‚СЃС‚РІРёРµ С‚СЂРµР±РѕРІР°РЅРёСЏРј'
                ],
                'conclusion': f'Р Р°Р±РѕС‚Р° РѕС†РµРЅРµРЅР° РЅР° {submission.overall_score or 0} Р±Р°Р»Р»РѕРІ РёР· 100. ' + (submission.ai_feedback_summary or 'РўСЂРµР±СѓРµС‚СЃСЏ РґРѕСЂР°Р±РѕС‚РєР°.')
            }
            
            try:
                from pdf_generator import generate_submission_pdf
                pdf_bytes = generate_submission_pdf(submission_id, submission_data)
                
                from flask import make_response
                response = make_response(pdf_bytes)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="Submission_{submission_id}_Report.pdf"'
                return response
                
            except ImportError:
                # Fallback to text
                report_content = f"""РћРўР§Р•Рў РџРћ РџР РћР’Р•Р РљР• Р РђР‘РћРўР«
Р—Р°РґР°РЅРёРµ: {submission_data['assignment_title']}
РЎС‚СѓРґРµРЅС‚: {submission_data['student_name']}
РћС†РµРЅРєР°: {submission_data['overall_score']}/100
РљРѕРјРјРµРЅС‚Р°СЂРёР№: {submission_data['ai_comment']}"""
                
                from flask import make_response
                response = make_response(report_content)
                response.headers['Content-Type'] = 'text/plain; charset=utf-8'
                response.headers['Content-Disposition'] = f'attachment; filename="Submission_{submission_id}_Report.txt"'
                return response
                
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return jsonify({'message': f'Error generating PDF: {str(e)}'}), 500

    @app.route('/api/admin/<section>')
    def admin_section(section):
        sections = ['dashboard', 'users', 'departments', 'teachers', 'notifications', 'settings', 'logs']
        if section not in sections:
            return jsonify({'message': 'Section not found'}), 404
        
        # For now, return a simple response. In production, you'd render templates
        return jsonify({'section': section, 'message': f'Content for {section} section'})

    return app

def setup_database(app):
    with app.app_context():
        try:
            from sqlalchemy.orm import configure_mappers
            configure_mappers()
        except Exception as e:
            print(f"CRITICAL MODEL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return

        db.create_all()
        
        # Manual migration for presentation_path
        try:
            with db.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE submission ADD COLUMN presentation_path VARCHAR(256)"))
                conn.commit()
                print("Added presentation_path column to submission table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                pass
            else:
                print(f"Migration error (presentation_path): {e}")
        
        # Create test users if they don't exist
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
        if not User.query.filter_by(username='teacher').first():
            teacher_user = User(username='teacher', role='teacher')
            teacher_user.set_password('teacher123')
            db.session.add(teacher_user)
            
        if not User.query.filter_by(username='student').first():
            student_user = User(username='student', role='student')
            student_user.set_password('student123')
            db.session.add(student_user)
            
        db.session.commit()
        
        if not os.path.exists('admin.txt'):
            with open('admin.txt', 'w', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SYSTEM_START | System | Application started\n")

if __name__ == '__main__':
    app = create_app()
    setup_database(app)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
