#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
نظام تسجيل الأنشطة والتغييرات في النظام
يقوم بحفظ جميع العمليات التي تتم على النظام في ملف سجل
"""

import os
import json
import time
from datetime import datetime
from flask import current_app, g, request, session

# تعريف أنواع الأنشطة
ACTIVITY_TYPES = {
    'LOGIN': 'تسجيل دخول',
    'LOGOUT': 'تسجيل خروج',
    'CREATE': 'إنشاء',
    'UPDATE': 'تحديث',
    'DELETE': 'حذف',
    'UPLOAD': 'رفع ملف',
    'DOWNLOAD': 'تنزيل ملف',
    'VIEW': 'عرض',
    'SEARCH': 'بحث',
    'OTHER': 'نشاط آخر'
}

# تعريف أنواع الكيانات
ENTITY_TYPES = {
    'USER': 'مستخدم',
    'CLIENT': 'عميل',
    'CASE': 'قضية',
    'APPOINTMENT': 'موعد',
    'DOCUMENT': 'مستند',
    'INVOICE': 'فاتورة',
    'PAYMENT': 'دفعة',
    'SYSTEM': 'النظام'
}

class ActivityLogger:
    """فئة لتسجيل الأنشطة في النظام"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """تهيئة المسجل مع تطبيق Flask"""
        self.app = app
        
        # إنشاء مجلد السجلات إذا لم يكن موجوداً
        log_dir = os.path.join(app.config.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # تحديد مسار ملف سجل الأنشطة
        self.activity_log_path = os.path.join(log_dir, 'activity_log.json')
        
        # إنشاء ملف السجل إذا لم يكن موجوداً
        if not os.path.exists(self.activity_log_path):
            with open(self.activity_log_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        # تسجيل دالة لتنفيذها بعد كل طلب
        app.after_request(self._after_request)
    
    def _after_request(self, response):
        """دالة تنفذ بعد كل طلب لتسجيل النشاط تلقائياً"""
        # تجاهل طلبات الملفات الثابتة
        if request.path.startswith('/static/'):
            return response
        
        # تسجيل الأنشطة الأساسية تلقائياً
        if request.endpoint:
            # تحديد نوع النشاط بناءً على الطريقة
            activity_type = 'VIEW'
            if request.method == 'POST':
                if 'delete' in request.endpoint:
                    activity_type = 'DELETE'
                elif 'edit' in request.endpoint or 'update' in request.endpoint:
                    activity_type = 'UPDATE'
                elif 'add' in request.endpoint or 'create' in request.endpoint:
                    activity_type = 'CREATE'
                elif 'upload' in request.endpoint:
                    activity_type = 'UPLOAD'
                elif 'download' in request.endpoint:
                    activity_type = 'DOWNLOAD'
                elif 'search' in request.endpoint:
                    activity_type = 'SEARCH'
                elif 'login' in request.endpoint:
                    activity_type = 'LOGIN'
                elif 'logout' in request.endpoint:
                    activity_type = 'LOGOUT'
            
            # تحديد نوع الكيان بناءً على المسار
            entity_type = 'SYSTEM'
            for key in ENTITY_TYPES:
                if key.lower() in request.endpoint:
                    entity_type = key
                    break
            
            # تسجيل النشاط
            self.log_activity(
                activity_type=activity_type,
                entity_type=entity_type,
                entity_id=request.view_args.get('id') if request.view_args else None,
                details=f"الطريقة: {request.method}, المسار: {request.path}"
            )
        
        return response
    
    def log_activity(self, activity_type, entity_type, entity_id=None, details=None, user_id=None):
        """تسجيل نشاط في السجل"""
        try:
            # الحصول على معرف المستخدم الحالي إذا لم يتم تحديده
            if user_id is None:
                user_id = session.get('user_id')
            
            # إنشاء سجل النشاط
            activity = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'activity_type': activity_type,
                'activity_name': ACTIVITY_TYPES.get(activity_type, activity_type),
                'entity_type': entity_type,
                'entity_name': ENTITY_TYPES.get(entity_type, entity_type),
                'entity_id': entity_id,
                'details': details,
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.user_agent.string if request and request.user_agent else None
            }
            
            # قراءة السجل الحالي
            activities = []
            try:
                with open(self.activity_log_path, 'r', encoding='utf-8') as f:
                    activities = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                activities = []
            
            # إضافة النشاط الجديد
            activities.append(activity)
            
            # حفظ السجل المحدث
            with open(self.activity_log_path, 'w', encoding='utf-8') as f:
                json.dump(activities, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"خطأ في تسجيل النشاط: {str(e)}")
            return False
    
    def get_activities(self, limit=100, user_id=None, activity_type=None, entity_type=None, entity_id=None, start_date=None, end_date=None):
        """الحصول على قائمة الأنشطة مع إمكانية التصفية"""
        try:
            # قراءة السجل
            with open(self.activity_log_path, 'r', encoding='utf-8') as f:
                activities = json.load(f)
            
            # تصفية الأنشطة
            filtered_activities = []
            for activity in activities:
                # تصفية حسب معرف المستخدم
                if user_id is not None and activity.get('user_id') != user_id:
                    continue
                
                # تصفية حسب نوع النشاط
                if activity_type is not None and activity.get('activity_type') != activity_type:
                    continue
                
                # تصفية حسب نوع الكيان
                if entity_type is not None and activity.get('entity_type') != entity_type:
                    continue
                
                # تصفية حسب معرف الكيان
                if entity_id is not None and activity.get('entity_id') != entity_id:
                    continue
                
                # تصفية حسب تاريخ البداية
                if start_date is not None:
                    activity_date = datetime.fromisoformat(activity.get('timestamp'))
                    if activity_date < start_date:
                        continue
                
                # تصفية حسب تاريخ النهاية
                if end_date is not None:
                    activity_date = datetime.fromisoformat(activity.get('timestamp'))
                    if activity_date > end_date:
                        continue
                
                filtered_activities.append(activity)
            
            # ترتيب الأنشطة حسب الوقت (الأحدث أولاً)
            filtered_activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # تحديد عدد النتائج
            if limit:
                filtered_activities = filtered_activities[:limit]
            
            return filtered_activities
        except Exception as e:
            print(f"خطأ في الحصول على الأنشطة: {str(e)}")
            return []

# إنشاء مثيل عام من المسجل
logger = ActivityLogger()

def init_app(app):
    """تهيئة مسجل الأنشطة مع تطبيق Flask"""
    global logger
    logger.init_app(app)
    
    # إضافة دالة مساعدة للقوالب
    @app.context_processor
    def utility_processor():
        return {
            'get_recent_activities': lambda limit=5: logger.get_activities(limit=limit)
        }
