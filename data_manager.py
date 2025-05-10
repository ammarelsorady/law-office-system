#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
مدير البيانات - مسؤول عن إدارة البيانات وتخزينها
يوفر واجهة موحدة للتعامل مع البيانات وضمان حفظها بشكل دائم
"""

import os
import json
import shutil
import sqlite3
from datetime import datetime
from flask import current_app, g

class DataManager:
    """فئة إدارة البيانات"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """تهيئة مدير البيانات مع تطبيق Flask"""
        self.app = app
        
        # إنشاء المجلدات اللازمة
        self._create_required_directories()
        
        # تسجيل دالة لتنفيذها عند إغلاق التطبيق
        app.teardown_appcontext(self._close_connection)
    
    def _create_required_directories(self):
        """إنشاء المجلدات اللازمة لتخزين البيانات"""
        # مجلد البيانات
        data_dir = os.path.join(self.app.config.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__))), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # مجلد التحميلات
        uploads_dir = os.path.join(self.app.config.get('UPLOAD_FOLDER'))
        os.makedirs(uploads_dir, exist_ok=True)
        
        # مجلد النسخ الاحتياطية
        backups_dir = os.path.join(self.app.config.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__))), 'backups')
        os.makedirs(backups_dir, exist_ok=True)
        
        # مجلد السجلات
        logs_dir = os.path.join(self.app.config.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
    
    def get_db(self):
        """الحصول على اتصال قاعدة البيانات"""
        if 'db' not in g:
            db_path = self.app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
        
        return g.db
    
    def _close_connection(self, e=None):
        """إغلاق اتصال قاعدة البيانات"""
        db = g.pop('db', None)
        
        if db is not None:
            db.close()
    
    def create_backup(self, backup_name=None):
        """إنشاء نسخة احتياطية من البيانات"""
        try:
            # إنشاء اسم النسخة الاحتياطية
            if backup_name is None:
                backup_name = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # مسار مجلد النسخة الاحتياطية
            backup_dir = os.path.join(self.app.config.get('BACKUP_FOLDER'), backup_name)
            os.makedirs(backup_dir, exist_ok=True)
            
            # نسخ قاعدة البيانات
            db_file = self.app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_file):
                shutil.copy2(db_file, os.path.join(backup_dir, 'law_office.db'))
            
            # نسخ مجلد التحميلات
            uploads_backup_dir = os.path.join(backup_dir, 'uploads')
            os.makedirs(uploads_backup_dir, exist_ok=True)
            
            # نسخ الملفات المرفوعة
            if os.path.exists(self.app.config['UPLOAD_FOLDER']):
                for file in os.listdir(self.app.config['UPLOAD_FOLDER']):
                    file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], file)
                    if os.path.isfile(file_path):
                        shutil.copy2(file_path, os.path.join(uploads_backup_dir, file))
            
            # نسخ ملف سجل الأنشطة
            logs_dir = os.path.join(self.app.config.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__))), 'logs')
            activity_log_path = os.path.join(logs_dir, 'activity_log.json')
            if os.path.exists(activity_log_path):
                logs_backup_dir = os.path.join(backup_dir, 'logs')
                os.makedirs(logs_backup_dir, exist_ok=True)
                shutil.copy2(activity_log_path, os.path.join(logs_backup_dir, 'activity_log.json'))
            
            # حذف النسخ الاحتياطية القديمة (الاحتفاظ بآخر 10 نسخ فقط)
            backup_folders = sorted([os.path.join(self.app.config.get('BACKUP_FOLDER'), d) 
                                    for d in os.listdir(self.app.config.get('BACKUP_FOLDER'))
                                    if os.path.isdir(os.path.join(self.app.config.get('BACKUP_FOLDER'), d))])
            
            if len(backup_folders) > 10:
                for old_backup in backup_folders[:-10]:
                    shutil.rmtree(old_backup, ignore_errors=True)
            
            return True
        except Exception as e:
            print(f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}")
            return False
    
    def restore_backup(self, backup_name):
        """استعادة نسخة احتياطية"""
        try:
            # مسار مجلد النسخة الاحتياطية
            backup_dir = os.path.join(self.app.config.get('BACKUP_FOLDER'), backup_name)
            
            if not os.path.exists(backup_dir):
                return False
            
            # استعادة قاعدة البيانات
            db_backup = os.path.join(backup_dir, 'law_office.db')
            if os.path.exists(db_backup):
                db_file = self.app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                shutil.copy2(db_backup, db_file)
            
            # استعادة الملفات المرفوعة
            uploads_backup_dir = os.path.join(backup_dir, 'uploads')
            if os.path.exists(uploads_backup_dir):
                for file in os.listdir(uploads_backup_dir):
                    file_path = os.path.join(uploads_backup_dir, file)
                    if os.path.isfile(file_path):
                        shutil.copy2(file_path, os.path.join(self.app.config['UPLOAD_FOLDER'], file))
            
            # استعادة ملف سجل الأنشطة
            logs_backup_dir = os.path.join(backup_dir, 'logs')
            activity_log_backup = os.path.join(logs_backup_dir, 'activity_log.json')
            if os.path.exists(activity_log_backup):
                logs_dir = os.path.join(self.app.config.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__))), 'logs')
                shutil.copy2(activity_log_backup, os.path.join(logs_dir, 'activity_log.json'))
            
            return True
        except Exception as e:
            print(f"خطأ في استعادة النسخة الاحتياطية: {str(e)}")
            return False
    
    def get_backup_list(self):
        """الحصول على قائمة النسخ الاحتياطية المتوفرة"""
        try:
            backup_folders = sorted([d for d in os.listdir(self.app.config.get('BACKUP_FOLDER'))
                                    if os.path.isdir(os.path.join(self.app.config.get('BACKUP_FOLDER'), d))],
                                   reverse=True)
            
            backups = []
            for folder in backup_folders:
                backup_path = os.path.join(self.app.config.get('BACKUP_FOLDER'), folder)
                backup_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                 for dirpath, _, filenames in os.walk(backup_path)
                                 for filename in filenames)
                
                backups.append({
                    'name': folder,
                    'path': backup_path,
                    'size': backup_size,
                    'date': datetime.strptime(folder.split('_')[0], '%Y%m%d') if '_' in folder else None
                })
            
            return backups
        except Exception as e:
            print(f"خطأ في الحصول على قائمة النسخ الاحتياطية: {str(e)}")
            return []

# إنشاء مثيل عام من مدير البيانات
data_manager = DataManager()

def init_app(app):
    """تهيئة مدير البيانات مع تطبيق Flask"""
    global data_manager
    data_manager.init_app(app)
