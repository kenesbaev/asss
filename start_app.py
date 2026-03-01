from app import create_app
from extensions import db
from models import User
import os

def init_database():
    """Initialize database and create test users if needed"""
    db.create_all()
    
    # Check if we have users
    user_count = User.query.count()
    if user_count == 0:
        print("Creating test users...")
        test_users = [
            {'username': 'student', 'password': 'student123', 'role': 'student'},
            {'username': 'teacher', 'password': 'teacher123', 'role': 'teacher'},
            {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
            {'username': 'muxammed', 'password': 'muxammed123', 'role': 'student'},
            {'username': 'bibiynaz', 'password': 'bibiynaz123', 'role': 'teacher'}
        ]
        
        for user_data in test_users:
            user = User(
                username=user_data['username'],
                role=user_data['role'],
                is_active=True,
                email=f"{user_data['username']}@example.com"
            )
            user.set_password(user_data['password'])
            db.session.add(user)
        
        db.session.commit()
        print(f"Created {len(test_users)} test users")
    else:
        print(f"Database already contains {user_count} users")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Initialize database
        init_database()
        
        # Create upload directories
        upload_dirs = ['uploads', 'static/avatars']
        for dir_name in upload_dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"Created directory: {dir_name}")
    
    print("=== AI Assistant Started ===")
    print("Available credentials:")
    print("Student: student / student123")
    print("Teacher: teacher / teacher123")
    print("Admin: admin / admin123")
    print("Student Muxammed: muxammed / muxammed123")
    print("Teacher Bibiynaz: bibiynaz / bibiynaz123")
    print("")
    print("Open browser and go to: http://localhost:5000")
    print("Test login page: http://localhost:5000/test-login")
    print("===============================")
    
    app.run(debug=True, host='0.0.0.0', port=5000)