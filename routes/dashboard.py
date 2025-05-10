from flask import Blueprint, render_template, session
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, Case, Client, Appointment, Invoice, Payment, User
from routes.auth import login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    next_week = today + timedelta(days=7)
    this_month_start = today.replace(day=1)
    this_month_end = (this_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # إحصائيات القضايا
    if session.get('role') == 'admin':
        total_cases = Case.query.count()
        open_cases = Case.query.filter_by(status='open').count()
        closed_cases = Case.query.filter_by(status='closed').count()
    else:
        total_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).count()
        open_cases = Case.query.filter_by(lawyer_id=session.get('user_id'), status='open').count()
        closed_cases = Case.query.filter_by(lawyer_id=session.get('user_id'), status='closed').count()

    # المواعيد القادمة
    if session.get('role') == 'admin':
        upcoming_appointments = Appointment.query.filter(
            Appointment.date >= today,
            Appointment.date <= next_week,
            Appointment.status != 'cancelled'
        ).order_by(Appointment.date).limit(5).all()
    else:
        upcoming_appointments = Appointment.query.filter(
            Appointment.date >= today,
            Appointment.date <= next_week,
            Appointment.status != 'cancelled',
            Appointment.user_id == session.get('user_id')
        ).order_by(Appointment.date).limit(5).all()

    # إحصائيات الفواتير
    if session.get('role') == 'admin':
        total_invoices = Invoice.query.count()
        unpaid_invoices = Invoice.query.filter(Invoice.status.in_(['unpaid', 'partial'])).count()

        # إجمالي المبالغ
        total_amount = db.session.query(func.sum(Invoice.amount)).scalar() or 0

        # إجمالي المدفوعات
        total_payments = db.session.query(func.sum(Payment.amount)).scalar() or 0

        # المدفوعات هذا الشهر
        month_payments = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= this_month_start,
            Payment.payment_date <= this_month_end
        ).scalar() or 0
    else:
        # الحصول على قضايا المحامي
        lawyer_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()
        case_ids = [case.id for case in lawyer_cases]

        # الحصول على الفواتير المرتبطة بهذه القضايا
        invoice_ids = [invoice.id for invoice in Invoice.query.filter(Invoice.case_id.in_(case_ids)).all()]

        total_invoices = len(invoice_ids)
        unpaid_invoices = Invoice.query.filter(
            Invoice.id.in_(invoice_ids),
            Invoice.status.in_(['unpaid', 'partial'])
        ).count()

        # إجمالي المبالغ
        total_amount = db.session.query(func.sum(Invoice.amount)).filter(
            Invoice.id.in_(invoice_ids)
        ).scalar() or 0

        # إجمالي المدفوعات
        total_payments = db.session.query(func.sum(Payment.amount)).filter(
            Payment.invoice_id.in_(invoice_ids)
        ).scalar() or 0

        # المدفوعات هذا الشهر
        month_payments = db.session.query(func.sum(Payment.amount)).filter(
            Payment.invoice_id.in_(invoice_ids),
            Payment.payment_date >= this_month_start,
            Payment.payment_date <= this_month_end
        ).scalar() or 0

    # إحصائيات العملاء
    total_clients = Client.query.count()

    # إحصائيات المستخدمين (للمسؤول فقط)
    if session.get('role') == 'admin':
        total_users = User.query.count()
        total_lawyers = User.query.filter_by(role='lawyer').count()
        total_staff = User.query.filter_by(role='staff').count()
    else:
        total_users = None
        total_lawyers = None
        total_staff = None

    # القضايا الأخيرة
    if session.get('role') == 'admin':
        recent_cases = Case.query.order_by(Case.opened_date.desc()).limit(5).all()
    else:
        recent_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).order_by(Case.opened_date.desc()).limit(5).all()

    return render_template('dashboard/index.html',
                          total_cases=total_cases,
                          open_cases=open_cases,
                          closed_cases=closed_cases,
                          upcoming_appointments=upcoming_appointments,
                          total_invoices=total_invoices,
                          unpaid_invoices=unpaid_invoices,
                          total_amount=total_amount,
                          total_payments=total_payments,
                          month_payments=month_payments,
                          total_clients=total_clients,
                          total_users=total_users,
                          total_lawyers=total_lawyers,
                          total_staff=total_staff,
                          recent_cases=recent_cases)
