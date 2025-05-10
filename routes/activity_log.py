#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
مسارات عرض سجل الأنشطة
"""

from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from datetime import datetime, timedelta

from routes.auth import login_required
from activity_logger import logger

activity_log_bp = Blueprint('activity_log', __name__, url_prefix='/activity-log')

@activity_log_bp.route('/')
@login_required
def index():
    """عرض سجل الأنشطة"""
    # التحقق من صلاحيات المستخدم (فقط المسؤول يمكنه عرض جميع الأنشطة)
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # الحصول على معلمات التصفية
    user_id = request.args.get('user_id')
    activity_type = request.args.get('activity_type')
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id')
    
    # معالجة تاريخ البداية والنهاية
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # إضافة يوم كامل للحصول على نهاية اليوم
            end_date = end_date + timedelta(days=1)
        except ValueError:
            pass
    
    # الحصول على عدد النتائج
    limit = request.args.get('limit', 100, type=int)
    
    # الحصول على الأنشطة
    activities = logger.get_activities(
        limit=limit,
        user_id=user_id if user_id else None,
        activity_type=activity_type if activity_type else None,
        entity_type=entity_type if entity_type else None,
        entity_id=entity_id if entity_id else None,
        start_date=start_date,
        end_date=end_date
    )
    
    # عرض القالب
    return render_template(
        'activity_log/index.html',
        activities=activities,
        user_id=user_id,
        activity_type=activity_type,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date_str,
        end_date=end_date_str,
        limit=limit
    )

@activity_log_bp.route('/user/<int:user_id>')
@login_required
def user_activities(user_id):
    """عرض أنشطة مستخدم محدد"""
    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # الحصول على الأنشطة
    activities = logger.get_activities(user_id=user_id)
    
    # عرض القالب
    return render_template(
        'activity_log/user_activities.html',
        activities=activities,
        user_id=user_id
    )

@activity_log_bp.route('/entity/<entity_type>/<int:entity_id>')
@login_required
def entity_activities(entity_type, entity_id):
    """عرض أنشطة كيان محدد (قضية، عميل، إلخ)"""
    # التحقق من صلاحيات المستخدم (يمكن إضافة المزيد من التحقق حسب نوع الكيان)
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # الحصول على الأنشطة
    activities = logger.get_activities(entity_type=entity_type, entity_id=entity_id)
    
    # عرض القالب
    return render_template(
        'activity_log/entity_activities.html',
        activities=activities,
        entity_type=entity_type,
        entity_id=entity_id
    )
