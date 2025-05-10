from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from datetime import datetime, timedelta

from models import db, Appointment, Case, User
from routes.auth import login_required, get_current_user

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/')
@login_required
def index():
    # الحصول على المواعيد القادمة
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    if session.get('role') == 'admin':
        upcoming_appointments = Appointment.query.filter(
            Appointment.date >= today,
            Appointment.status != 'cancelled'
        ).order_by(Appointment.date).all()
    else:
        upcoming_appointments = Appointment.query.filter(
            Appointment.date >= today,
            Appointment.status != 'cancelled',
            Appointment.user_id == session.get('user_id')
        ).order_by(Appointment.date).all()

    return render_template('appointments/index.html', appointments=upcoming_appointments)

@appointments_bp.route('/calendar')
@login_required
def calendar():
    return render_template('appointments/calendar.html')

@appointments_bp.route('/api/events')
@login_required
def get_events():
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')

    try:
        start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        # إذا كان هناك خطأ في التنسيق، استخدم الشهر الحالي
        today = datetime.utcnow()
        start_date = datetime(today.year, today.month, 1)
        end_date = start_date + timedelta(days=31)

    # الحصول على المواعيد في النطاق المحدد
    if session.get('role') == 'admin':
        appointments = Appointment.query.filter(
            Appointment.date >= start_date,
            Appointment.date <= end_date
        ).all()
    else:
        appointments = Appointment.query.filter(
            Appointment.date >= start_date,
            Appointment.date <= end_date,
            Appointment.user_id == session.get('user_id')
        ).all()

    # تحويل المواعيد إلى تنسيق مناسب للتقويم
    events = []
    for appointment in appointments:
        color = '#3788d8'  # افتراضي
        if appointment.status == 'completed':
            color = '#28a745'  # أخضر
        elif appointment.status == 'cancelled':
            color = '#dc3545'  # أحمر
        elif appointment.status == 'postponed':
            color = '#ffc107'  # أصفر

        end_date = appointment.end_date or (appointment.date + timedelta(hours=1))

        events.append({
            'id': appointment.id,
            'title': appointment.title,
            'start': appointment.date.isoformat(),
            'end': end_date.isoformat(),
            'url': url_for('appointments.view_appointment', appointment_id=appointment.id),
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#fff',
            'extendedProps': {
                'location': appointment.location,
                'type': appointment.appointment_type,
                'status': appointment.status
            }
        })

    return jsonify(events)

@appointments_bp.route('/view/<int:appointment_id>')
@login_required
def view_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and appointment.user_id != session.get('user_id'):
        flash('ليس لديك صلاحية للوصول إلى هذا الموعد', 'danger')
        return redirect(url_for('appointments.index'))

    return render_template('appointments/view.html', appointment=appointment)

@appointments_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_appointment():
    # الحصول على القضايا المتاحة
    if session.get('role') == 'admin':
        cases = Case.query.filter_by(status='open').all()
        users = User.query.filter(User.role.in_(['admin', 'lawyer'])).all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id'), status='open').all()
        current_user = get_current_user()
        users = [current_user] if current_user else []

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        end_date_str = request.form.get('end_date')
        end_time_str = request.form.get('end_time')
        location = request.form.get('location')
        appointment_type = request.form.get('appointment_type')
        status = request.form.get('status')
        case_id = request.form.get('case_id')
        user_id = request.form.get('user_id') if session.get('role') == 'admin' else session.get('user_id')
        notes = request.form.get('notes')

        # تحويل التاريخ والوقت إلى كائن datetime
        try:
            date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            if end_date_str and end_time_str:
                end_date_time = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M")
            else:
                end_date_time = None
        except ValueError:
            flash('تنسيق التاريخ أو الوقت غير صحيح', 'danger')
            return redirect(url_for('appointments.add_appointment'))

        # إنشاء موعد جديد
        new_appointment = Appointment(
            title=title,
            description=description,
            date=date_time,
            end_date=end_date_time,
            location=location,
            appointment_type=appointment_type,
            status=status,
            case_id=case_id,
            user_id=user_id,
            notes=notes
        )

        db.session.add(new_appointment)
        db.session.commit()

        flash('تم إضافة الموعد بنجاح', 'success')
        return redirect(url_for('appointments.view_appointment', appointment_id=new_appointment.id))

    return render_template('appointments/add.html', cases=cases, users=users)

@appointments_bp.route('/edit/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and appointment.user_id != session.get('user_id'):
        flash('ليس لديك صلاحية لتعديل هذا الموعد', 'danger')
        return redirect(url_for('appointments.index'))

    # الحصول على القضايا المتاحة
    if session.get('role') == 'admin':
        cases = Case.query.all()
        users = User.query.filter(User.role.in_(['admin', 'lawyer'])).all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()
        current_user = get_current_user()
        users = [current_user] if current_user else []

    if request.method == 'POST':
        appointment.title = request.form.get('title')
        appointment.description = request.form.get('description')
        appointment.location = request.form.get('location')
        appointment.appointment_type = request.form.get('appointment_type')
        appointment.status = request.form.get('status')
        appointment.notes = request.form.get('notes')

        # فقط المسؤول يمكنه تغيير المستخدم
        if session.get('role') == 'admin':
            appointment.user_id = request.form.get('user_id')

        # تحويل التاريخ والوقت إلى كائن datetime
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        end_date_str = request.form.get('end_date')
        end_time_str = request.form.get('end_time')

        try:
            appointment.date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

            if end_date_str and end_time_str:
                appointment.end_date = datetime.strptime(f"{end_date_str} {end_time_str}", "%Y-%m-%d %H:%M")
            else:
                appointment.end_date = None
        except ValueError:
            flash('تنسيق التاريخ أو الوقت غير صحيح', 'danger')
            return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))

        db.session.commit()
        flash('تم تحديث الموعد بنجاح', 'success')
        return redirect(url_for('appointments.view_appointment', appointment_id=appointment.id))

    return render_template('appointments/edit.html', appointment=appointment, cases=cases, users=users)

@appointments_bp.route('/delete/<int:appointment_id>', methods=['POST'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and appointment.user_id != session.get('user_id'):
        flash('ليس لديك صلاحية لحذف هذا الموعد', 'danger')
        return redirect(url_for('appointments.index'))

    db.session.delete(appointment)
    db.session.commit()

    flash('تم حذف الموعد بنجاح', 'success')
    return redirect(url_for('appointments.index'))
