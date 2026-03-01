from app import create_app
from extensions import db
import os
import sys
from datetime import datetime

def init_database():
    """Инициализация базы данных при первом запуске"""
    app = create_app()
    
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Проверяем, есть ли пользователи
        from models import User
        if User.query.count() == 0:
            print("База данных пустая, запускаем инициализацию...")
            
            # Создаем папки для загрузок если их нет
            upload_dirs = ['uploads', 'static/avatars', 'instance']
            for dir_name in upload_dirs:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                    print(f"Создана папка: {dir_name}")
            
            # Создаем тестовых пользователей
            test_users = [
                {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'full_name': 'Administrator'},
                {'username': 'teacher', 'password': 'teacher123', 'role': 'teacher', 'full_name': 'Test Teacher'},
                {'username': 'student', 'password': 'student123', 'role': 'student', 'full_name': 'Test Student'}
            ]
            
            for user_data in test_users:
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
            
            # Создаем admin.txt если не существует
            if not os.path.exists('admin.txt'):
                with open('admin.txt', 'w', encoding='utf-8') as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | SYSTEM_START | System | Application initialized\n")
                print("Создан файл логов admin.txt")
            
            print("✅ База данных инициализирована!")
        else:
            print(f"✅ База данных уже содержит {User.query.count()} пользователей")

if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()
    
    # Запускаем приложение
    app = create_app()
    
    print("\n=== AI Assistant запущен ===")
    print("Доступные учетные данные:")
    print("Студент: student / student123")
    print("Преподаватель: teacher / teacher123")
    print("Администратор: admin / admin123")
    print("Студент Muxammed: muxammed / muxammed123")
    print("Преподаватель Bibiynaz: bibiynaz / bibiynaz123")
    print("\n🌐 Откройте браузер и перейдите по адресу: http://localhost:5000")
    print("===============================\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)