#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
سكريبت لإصلاح مشكلة قاعدة البيانات بشكل نهائي
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime

def get_application_path():
    """الحصول على المسار الحالي للتطبيق"""
    # إذا كان التطبيق يعمل كملف تنفيذي
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    # إذا كان التطبيق يعمل كسكريبت Python
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    return application_path

def fix_database():
    """إصلاح مشكلة قاعدة البيانات"""
    # الحصول على المسار الحالي للتطبيق
    application_path = get_application_path()
    print(f"مسار التطبيق: {application_path}")
    
    # إنشاء المجلدات اللازمة
    data_dir = os.path.join(application_path, 'data')
    logs_dir = os.path.join(application_path, 'logs')
    backups_dir = os.path.join(application_path, 'backups')
    uploads_dir = os.path.join(application_path, 'static', 'uploads')
    session_dir = os.path.join(application_path, 'flask_session')
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(backups_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(session_dir, exist_ok=True)
    
    print(f"تم إنشاء المجلدات اللازمة")
    
    # مسار قاعدة البيانات
    old_db_path = os.path.join(application_path, 'law_office.db')
    new_db_path = os.path.join(data_dir, 'law_office.db')
    
    print(f"مسار قاعدة البيانات القديم: {old_db_path}")
    print(f"مسار قاعدة البيانات الجديد: {new_db_path}")
    
    # التحقق من وجود قاعدة البيانات القديمة
    if os.path.exists(old_db_path):
        print("قاعدة البيانات القديمة موجودة")
        
        # نسخ قاعدة البيانات القديمة إلى المسار الجديد
        shutil.copy2(old_db_path, new_db_path)
        print("تم نسخ قاعدة البيانات القديمة إلى المسار الجديد")
    else:
        print("قاعدة البيانات القديمة غير موجودة")
    
    # تعديل ملف config.py
    config_path = os.path.join(application_path, 'config.py')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # تحديث مسار قاعدة البيانات
        config_content = config_content.replace(
            'DB_PATH = os.path.join(BASE_DIR, \'data\')',
            f'DB_PATH = \'{data_dir.replace("\\", "/")}\''
        )
        
        # تحديث مسار مجلد التحميلات
        config_content = config_content.replace(
            'UPLOAD_FOLDER = os.path.join(BASE_DIR, \'static\', \'uploads\')',
            f'UPLOAD_FOLDER = \'{uploads_dir.replace("\\", "/")}\''
        )
        
        # تحديث مسار مجلد النسخ الاحتياطي
        config_content = config_content.replace(
            'BACKUP_FOLDER = os.path.join(BASE_DIR, \'backups\')',
            f'BACKUP_FOLDER = \'{backups_dir.replace("\\", "/")}\''
        )
        
        # تحديث مسار مجلد الجلسات
        config_content = config_content.replace(
            'SESSION_FILE_DIR = os.path.join(BASE_DIR, \'flask_session\')',
            f'SESSION_FILE_DIR = \'{session_dir.replace("\\", "/")}\''
        )
        
        # حفظ ملف التكوين المحدث
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("تم تحديث مسارات الملفات في ملف التكوين")
    
    # التحقق من وجود قاعدة البيانات الجديدة
    if os.path.exists(new_db_path):
        print("قاعدة البيانات الجديدة موجودة")
        
        # فتح قاعدة البيانات للتأكد من أنها تعمل
        try:
            conn = sqlite3.connect(new_db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود جدول المستخدمين
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
            if cursor.fetchone():
                print("جدول المستخدمين موجود")
                
                # عرض عدد المستخدمين
                cursor.execute("SELECT COUNT(*) FROM user")
                user_count = cursor.fetchone()[0]
                print(f"عدد المستخدمين: {user_count}")
                
                # عرض المستخدمين
                cursor.execute("SELECT id, username, email, first_name, last_name, role FROM user")
                users = cursor.fetchall()
                for user in users:
                    print(f"المستخدم: {user[1]}, الاسم: {user[3]} {user[4]}, الدور: {user[5]}")
            else:
                print("جدول المستخدمين غير موجود")
            
            conn.close()
        except Exception as e:
            print(f"خطأ في فتح قاعدة البيانات: {str(e)}")
    else:
        print("قاعدة البيانات الجديدة غير موجودة")
    
    print("تم إصلاح مشكلة قاعدة البيانات بنجاح!")

if __name__ == '__main__':
    fix_database()
