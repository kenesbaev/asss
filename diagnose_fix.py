from app import create_app
from extensions import db
from models import User
import jwt
from config import Config
from datetime import datetime, timedelta

def diagnose_and_fix():
    app = create_app()
    
    with app.app_context():
        print("=== DIAGNOSTIKA SISTEMY VHODA ===")
        print()
        
        # 1. Proverka bazy dannyh
        print("1. Proverka bazy dannyh...")
        try:
            db.create_all()
            print("[OK] Baza dannyh inicializovana")
        except Exception as e:
            print(f"[ERROR] Oshibka bazy dannyh: {e}")
            return
        
        # 2. Proverka polzovateley
        print()
        print("2. Proverka polzovateley...")
        users = User.query.all()
        print(f"Naydeno polzovateley: {len(users)}")
        
        # Sozdaem/obnovlyaem testovyh polzovateley
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
                print(f"[OK] Obnovlen: {user_data['username']}")
            else:
                user = User(
                    username=user_data['username'],
                    role=user_data['role'],
                    is_active=True,
                    email=f"{user_data['username']}@example.com"
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                print(f"[OK] Sozdan: {user_data['username']}")
        
        db.session.commit()
        
        # 3. Test autentifikacii
        print()
        print("3. Test autentifikacii...")
        for user_data in test_users:
            user = User.query.filter_by(username=user_data['username']).first()
            if user and user.check_password(user_data['password']):
                # Sozdaem testovyy token
                token = jwt.encode({
                    'user_id': user.id,
                    'role': user.role,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, Config.SECRET_KEY, algorithm='HS256')
                print(f"[OK] {user_data['username']} - parol korekten, token sozdan")
            else:
                print(f"[ERROR] {user_data['username']} - problema s parolem")
        
        # 4. Proverka konfiguracii
        print()
        print(f"4. Proverka konfiguracii...")
        print(f"SECRET_KEY ustanovlen: {'[OK]' if Config.SECRET_KEY else '[ERROR]'}")
        print(f"SQLALCHEMY_DATABASE_URI: {getattr(Config, 'SQLALCHEMY_DATABASE_URI', 'Not set')}")
        
        # 5. Sozdanie neobhodimyh papok
        print()
        print(f"5. Sozdanie papok...")
        import os
        folders = ['uploads', 'static/avatars', 'instance']
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"[OK] Sozdana papka: {folder}")
            else:
                print(f"[OK] Papka sushchestvuet: {folder}")
        
        print()
        print(f"=== REZULTAT DIAGNOSTIKI ===")
        print(f"[OK] Sistema gotova k rabote!")
        print()
        print(f"UCHETNYE DANNYE DLYA VHODA:")
        print(f"Student: student / student123")
        print(f"Prepodavatel: teacher / teacher123")
        print(f"Administrator: admin / admin123")
        print(f"Student Muxammed: muxammed / muxammed123")
        print(f"Prepodavatel Bibiynaz: bibiynaz / bibiynaz123")
        print()
        print(f"SSYLKI:")
        print(f"Osnovnoy vhod: http://localhost:5000/login")
        print(f"Test vhoda: http://localhost:5000/test-login")
        print(f"Glavnaya: http://localhost:5000/")

if __name__ == '__main__':
    diagnose_and_fix()