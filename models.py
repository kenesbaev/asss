from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'student', 'teacher', 'admin'
    email = db.Column(db.String(120), nullable=True)
    full_name = db.Column(db.String(120), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Добавляем relationship
    department = db.relationship('Department', backref='users')
    group = db.relationship('Group', back_populates='members', foreign_keys=[group_id])
    
    # Relationships with cascade delete
    user_profile = db.relationship('UserProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    teacher_students_assigned = db.relationship('TeacherStudent', foreign_keys='TeacherStudent.teacher_id', back_populates='teacher', cascade='all, delete-orphan')
    student_teachers_assigned = db.relationship('TeacherStudent', foreign_keys='TeacherStudent.student_id', back_populates='student', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', back_populates='student', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='student', cascade='all, delete-orphan')
    academic_ratings = db.relationship('AcademicRating', back_populates='student', cascade='all, delete-orphan')
    student_subjects = db.relationship('StudentSubject', back_populates='student', cascade='all, delete-orphan')
    teacher_subjects = db.relationship('TeacherSubject', back_populates='teacher', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', back_populates='user', cascade='all, delete-orphan')
    news = db.relationship('News', back_populates='author', cascade='all, delete-orphan')
    managed_groups = db.relationship('Group', back_populates='teacher', foreign_keys='Group.teacher_id', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    teacher = db.relationship('User', back_populates='managed_groups', foreign_keys=[teacher_id])
    members = db.relationship('User', back_populates='group', foreign_keys='User.group_id')


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    department = db.relationship('Department', backref='subjects')

class TeacherSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('teacher_id', 'subject_id'),)
    
    teacher = db.relationship('User', foreign_keys=[teacher_id], back_populates='teacher_subjects')
    subject = db.relationship('Subject')

class TeacherStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('teacher_id', 'student_id', 'subject_id'),)
    
    teacher = db.relationship('User', foreign_keys=[teacher_id], back_populates='teacher_students_assigned')
    student = db.relationship('User', foreign_keys=[student_id], back_populates='student_teachers_assigned')
    subject = db.relationship('Subject')

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    course = db.Column(db.String(50))
    assignment_type = db.Column(db.String(50)) # 'theoretical', 'practical'
    deadline = db.Column(db.DateTime)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subject = db.relationship('Subject')
    group = db.relationship('Group', backref='assignments')

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    display_name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(256))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', back_populates='user_profile')

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(256))
    flowchart_path = db.Column(db.String(256), nullable=True)
    presentation_path = db.Column(db.String(256), nullable=True)
    overall_score = db.Column(db.Float)
    ai_feedback_summary = db.Column(db.Text)
    
    section_scores = db.relationship('SectionScore', backref='submission', lazy='dynamic')
    student = db.relationship('User', back_populates='submissions')

class SectionScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'))
    section_name = db.Column(db.String(50))
    score = db.Column(db.Float)
    content = db.Column(db.Text)
    feedback = db.Column(db.Text)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(256))
    category = db.Column(db.String(64))

class StudentSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', back_populates='student_subjects')
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id'),)

class AcademicRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    total_assignments = db.Column(db.Integer, default=0)
    completed_assignments = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student = db.relationship('User', back_populates='academic_ratings')
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    type = db.Column(db.String(50), default='assignment')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assignment = db.relationship('Assignment', backref='notifications')
    student = db.relationship('User', back_populates='notifications')

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship('User', back_populates='news')

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='activity_logs')

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    file_path = db.Column(db.String(256), nullable=False)
    cover_image = db.Column(db.String(256), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subject = db.relationship('Subject', backref='literature_list')
    downloads = db.relationship('BookDownload', back_populates='book', cascade='all,delete-orphan')

class BookDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    book = db.relationship('Book', back_populates='downloads')
    user = db.relationship('User', backref='book_downloads')
