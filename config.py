import os
from datetime import timedelta

class Config:
    # إعدادات الأمان
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'مفتاح-سري-افتراضي-للتطوير-فقط'
    
    # إعدادات قاعدة البيانات
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # استخدام PostgreSQL في الإنتاج و SQLite في التطوير
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        DB_PATH = os.path.join(BASE_DIR, 'data')
        os.makedirs(DB_PATH, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(DB_PATH, "law_office.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات تحميل الملفات
    if os.environ.get('UPLOAD_FOLDER'):
        UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 ميجابايت
    
    # إعدادات النسخ الاحتياطي
    if os.environ.get('BACKUP_FOLDER'):
        BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER')
    else:
        BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')
    os.makedirs(BACKUP_FOLDER, exist_ok=True)

    # إعدادات البريد الإلكتروني
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # إعدادات الجلسة
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)  # زيادة مدة الجلسة إلى 30 يوم
    SESSION_TYPE = 'filesystem'  # استخدام نظام الملفات لتخزين الجلسات
    SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')  # مجلد تخزين الجلسات
    os.makedirs(SESSION_FILE_DIR, exist_ok=True)  # إنشاء مجلد الجلسات إذا لم يكن موجودًا
    SESSION_PERMANENT = True  # جعل الجلسات دائمة

    # إعدادات التطبيق
    APP_NAME = "نظام إدارة مكتب المحاماة"
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'

    # إعدادات التحميل
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
