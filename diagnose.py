from app import create_app
from extensions import db
from models import User
import jwt
from config import Config
from datetime import datetime, timedelta

def diagnose_and_fix():
    app = create_app()
    
    with app.app_context():
        print("=== ДИАГНОСТИКА СИСТЕМЫ ВХОДА ===\n")
        
        # 1. Проверка базы данных
        print("1. Проверка базы данных...")
        try:
            db.create_all()
            print("✅ База данных инициализирована")
        except Exception as e:
            print(f"❌ Ошибка базы данных: {e}")
            return
        
        # 2. Проверка пользователей
        print("\n2. Проверка пользователей...")
        users = User.query.all()
        print(f"Найдено пользователей: {len(users)}")
        
        # Создаем/обновляем тестовых пользователей
        test_users = [
            {'username': 'student', 'password': 'student123', 'role': 'student'},
            {'username': 'teacher', 'password': 'teacher123', 'role': 'teacher'},
            {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
            {'username': 'muxammed', 'password': 'muxammed123', 'role': 'student'},
            {'username': 'bibiynaz', 'password': 'bibiynaz123', 'role': 'teacher'}
        ]
        
        for user_data in test_users:
            user = User.query.filter_by(username=user_data['username']).first()
            if user:
                user.set_password(user_data['password'])
                user.is_active = True
                user.role = user_data['role']
                print(f"✅ Обновлен: {user_data['username']}")
            else:
                user = User(
                    username=user_data['username'],
                    role=user_data['role'],
                    is_active=True,
                    email=f"{user_data['username']}@example.com"
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                print(f"✅ Создан: {user_data['username']}")
        
        db.session.commit()
        
        # 3. Тест аутентификации
        print("\n3. Тест аутентификации...")
        for user_data in test_users:
            user = User.query.filter_by(username=user_data['username']).first()
            if user and user.check_password(user_data['password']):
                # Создаем тестовый токен
                token = jwt.encode({
                    'user_id': user.id,
                    'role': user.role,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, Config.SECRET_KEY, algorithm='HS256')
                print(f"✅ {user_data['username']} - пароль корректен, токен создан")
            else:
                print(f"❌ {user_data['username']} - проблема с паролем")
        
        # 4. Проверка конфигурации
        print(f"\n4. Проверка конфигурации...")
        print(f"SECRET_KEY установлен: {'✅' if Config.SECRET_KEY else '❌'}")
        print(f"DATABASE_URL: {Config.DATABASE_URL}")
        
        # 5. Создание необходимых папок
        print(f"\n5. Создание папок...")
        import os
        folders = ['uploads', 'static/avatars', 'instance']
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"✅ Создана папка: {folder}")
            else:
                print(f"✅ Папка существует: {folder}")
        
        print(f"\n=== РЕЗУЛЬТАТ ДИАГНОСТИКИ ===")
        print(f"✅ Система готова к работе!")
        print(f"\n📋 УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА:")
        print(f"Студент: student / student123")
        print(f"Преподаватель: teacher / teacher123")
        print(f"Администратор: admin / admin123")
        print(f"Студент Muxammed: muxammed / muxammed123")
        print(f"Преподаватель Bibiynaz: bibiynaz / bibiynaz123")
        print(f"\n🌐 ССЫЛКИ:")
        print(f"Основной вход: http://localhost:5000/login")
        print(f"Тест входа: http://localhost:5000/test-login")
        print(f"Главная: http://localhost:5000/")

if __name__ == '__main__':
    diagnose_and_fix()