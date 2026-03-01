import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or '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'
    
    # Настройки по умолчанию
    DEFAULT_SETTINGS = {
        'ai_risk_threshold': '60',
        'plagiarism_threshold': '70',
        'max_file_size': '50',
        'allowed_file_types': '.pdf,.py,.java,.cpp,.js,.txt',
        'default_language': 'ru',
        'site_name': 'AI Assistant',
        'site_logo': '/static/img/logo.png',
        'admin_email': 'admin@example.com',
        'enable_registration': 'true',
        'max_users_per_teacher': '30'
    }