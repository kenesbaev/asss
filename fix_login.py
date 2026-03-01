from app import create_app
from extensions import db
from models import User

def fix_login():
    app = create_app()
    with app.app_context():
        print("=== Проверка пользователей ===")
        
        # Проверяем существующих пользователей
        users = User.query.all()
        print(f"Найдено пользователей: {len(users)}")
        
        for user in users:
            print(f"- {user.username} ({user.role}) - активен: {user.is_active}")
        
        # Создаем/обновляем тестовых пользователей
        test_users = [
            {'username': 'student', 'password': 'student123', 'role': 'student', 'full_name': 'Test Student'},
            {'username': 'teacher', 'password': 'teacher123', 'role': 'teacher', 'full_name': 'Test Teacher'},
            {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'full_name': 'Administrator'},
            {'username': 'muxammed', 'password': 'muxammed123', 'role': 'student', 'full_name': 'Muxammed'},
            {'username': 'bibiynaz', 'password': 'bibiynaz123', 'role': 'teacher', 'full_name': 'Bibiynaz'}
        ]
        
        print("\n=== Создание/обновление пользователей ===")
        for user_data in test_users:
            user = User.query.filter_by(username=user_data['username']).first()
            
            if user:
                # Обновляем существующего пользователя
                user.set_password(user_data['password'])
                user.is_active = True
                user.role = user_data['role']
                user.full_name = user_data['full_name']
                user.email = f"{user_data['username']}@example.com"
                print(f"Обновлен пользователь: {user_data['username']}")
            else:
                # Создаем нового пользователя
                user = User(
                    username=user_data['username'],
                    role=user_data['role'],
                    full_name=user_data['full_name'],
                    email=f"{user_data['username']}@example.com",
                    is_active=True
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                print(f"Создан пользователь: {user_data['username']}")
        
        db.session.commit()
        
        print("\n=== Итоговый список пользователей ===")
        users = User.query.all()
        for user in users:
            print(f"- {user.username} ({user.role}) - пароль: {user_data['password'] if user.username in [u['username'] for u in test_users] else 'неизвестен'}")
        
        print("\n=== Учетные данные для входа ===")
        print("Студент: student / student123")
        print("Преподаватель: teacher / teacher123") 
        print("Администратор: admin / admin123")
        print("Студент Muxammed: muxammed / muxammed123")
        print("Преподаватель Bibiynaz: bibiynaz / bibiynaz123")

if __name__ == '__main__':
    fix_login()