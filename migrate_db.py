"""
Quick fix script to add new tables without breaking existing functionality
Run this to update the database schema
"""
from app import create_app
from extensions import db
from models import Subject, StudentSubject, AcademicRating, Department, TeacherSubject, TeacherStudent, News

app = create_app()

with app.app_context():
    try:
        # Create only the new tables, don't modify existing ones
        db.create_all()
        print("New tables created successfully!")
        print("   - department")
        print("   - teacher_subject")
        print("   - teacher_student")
        print("   - news")
        print("\nNote: Existing tables were not modified")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nIf you see 'table already exists' errors, that's normal - it means the tables are already there.")