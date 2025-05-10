from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
import calendar

from models import db, Case, Client, User, Appointment, Document, Invoice, Payment
from routes.auth import login_required

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/cases/status')
@login_required
def cases_by_status():
    # الحصول على إحصائيات القضايا حسب الحالة
    open_cases = Case.query.filter_by(status='open').count()
    closed_cases = Case.query.filter_by(status='closed').count()
    pending_cases = Case.query.filter_by(status='pending').count()
    postponed_cases = Case.query.filter_by(status='postponed').count()
    
    total_cases = open_cases + closed_cases + pending_cases + postponed_cases
    
    # حساب النسب المئوية
    open_percentage = (open_cases / total_cases * 100) if total_cases > 0 else 0
    closed_percentage = (closed_cases / total_cases * 100) if total_cases > 0 else 0
    pending_percentage = (pending_cases / total_cases * 100) if total_cases > 0 else 0
    postponed_percentage = (postponed_cases / total_cases * 100) if total_cases > 0 else 0
    
    # الحصول على بيانات القضايا حسب النوع والحالة
    type_status_data = {
        'open': {
            'civil': Case.query.filter_by(status='open', case_type='مدني').count(),
            'criminal': Case.query.filter_by(status='open', case_type='جنائي').count(),
            'commercial': Case.query.filter_by(status='open', case_type='تجاري').count(),
            'labor': Case.query.filter_by(status='open', case_type='عمالي').count(),
            'personal': Case.query.filter_by(status='open', case_type='أحوال شخصية').count(),
            'administrative': Case.query.filter_by(status='open', case_type='إداري').count(),
            'real_estate': Case.query.filter_by(status='open', case_type='عقاري').count(),
            'other': Case.query.filter_by(status='open', case_type='آخر').count()
        },
        'closed': {
            'civil': Case.query.filter_by(status='closed', case_type='مدني').count(),
            'criminal': Case.query.filter_by(status='closed', case_type='جنائي').count(),
            'commercial': Case.query.filter_by(status='closed', case_type='تجاري').count(),
            'labor': Case.query.filter_by(status='closed', case_type='عمالي').count(),
            'personal': Case.query.filter_by(status='closed', case_type='أحوال شخصية').count(),
            'administrative': Case.query.filter_by(status='closed', case_type='إداري').count(),
            'real_estate': Case.query.filter_by(status='closed', case_type='عقاري').count(),
            'other': Case.query.filter_by(status='closed', case_type='آخر').count()
        },
        'pending': {
            'civil': Case.query.filter_by(status='pending', case_type='مدني').count(),
            'criminal': Case.query.filter_by(status='pending', case_type='جنائي').count(),
            'commercial': Case.query.filter_by(status='pending', case_type='تجاري').count(),
            'labor': Case.query.filter_by(status='pending', case_type='عمالي').count(),
            'personal': Case.query.filter_by(status='pending', case_type='أحوال شخصية').count(),
            'administrative': Case.query.filter_by(status='pending', case_type='إداري').count(),
            'real_estate': Case.query.filter_by(status='pending', case_type='عقاري').count(),
            'other': Case.query.filter_by(status='pending', case_type='آخر').count()
        },
        'postponed': {
            'civil': Case.query.filter_by(status='postponed', case_type='مدني').count(),
            'criminal': Case.query.filter_by(status='postponed', case_type='جنائي').count(),
            'commercial': Case.query.filter_by(status='postponed', case_type='تجاري').count(),
            'labor': Case.query.filter_by(status='postponed', case_type='عمالي').count(),
            'personal': Case.query.filter_by(status='postponed', case_type='أحوال شخصية').count(),
            'administrative': Case.query.filter_by(status='postponed', case_type='إداري').count(),
            'real_estate': Case.query.filter_by(status='postponed', case_type='عقاري').count(),
            'other': Case.query.filter_by(status='postponed', case_type='آخر').count()
        }
    }
    
    # الحصول على جميع القضايا
    cases = Case.query.order_by(Case.opened_date.desc()).all()
    
    return render_template('reports/cases_by_status.html',
                          open_cases=open_cases,
                          closed_cases=closed_cases,
                          pending_cases=pending_cases,
                          postponed_cases=postponed_cases,
                          open_percentage=open_percentage,
                          closed_percentage=closed_percentage,
                          pending_percentage=pending_percentage,
                          postponed_percentage=postponed_percentage,
                          type_status_data=type_status_data,
                          cases=cases)

@reports_bp.route('/financial/summary')
@login_required
def financial_summary():
    # الحصول على الفترة المطلوبة
    period = request.args.get('period', 'month')
    
    # تحديد نطاق التاريخ بناءً على الفترة
    today = datetime.utcnow().date()
    if period == 'month':
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1], 23, 59, 59)
        period_text = f"الشهر الحالي ({today.strftime('%B %Y')})"
    elif period == 'quarter':
        quarter = (today.month - 1) // 3 + 1
        start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end_month = quarter * 3
        end_date = datetime(today.year, end_month, calendar.monthrange(today.year, end_month)[1], 23, 59, 59)
        period_text = f"الربع الحالي (Q{quarter} {today.year})"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        period_text = f"السنة الحالية ({today.year})"
    else:  # 'all'
        start_date = datetime(2000, 1, 1)  # تاريخ قديم جداً
        end_date = datetime(2100, 12, 31, 23, 59, 59)  # تاريخ مستقبلي جداً
        period_text = "كل الفترات"
    
    # الحصول على إحصائيات الفواتير
    total_invoices_count = Invoice.query.filter(Invoice.issue_date.between(start_date, end_date)).count()
    total_invoices_amount = db.session.query(func.sum(Invoice.amount)).filter(Invoice.issue_date.between(start_date, end_date)).scalar() or 0
    
    # الحصول على إحصائيات المدفوعات
    total_payments_count = Payment.query.filter(Payment.payment_date.between(start_date, end_date)).count()
    total_payments_amount = db.session.query(func.sum(Payment.amount)).filter(Payment.payment_date.between(start_date, end_date)).scalar() or 0
    
    # الحصول على إحصائيات الفواتير غير المدفوعة
    pending_invoices = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status.in_(['unpaid', 'partial'])
    ).all()
    pending_invoices_count = len(pending_invoices)
    pending_invoices_amount = sum(invoice.amount for invoice in pending_invoices)
    
    # الحصول على إحصائيات الفواتير المتأخرة
    overdue_invoices = []
    for invoice in Invoice.query.filter(
        Invoice.status.in_(['unpaid', 'partial']),
        Invoice.due_date < today
    ).all():
        invoice.days_overdue = (today - invoice.due_date.date()).days
        overdue_invoices.append(invoice)
    
    overdue_invoices_count = len(overdue_invoices)
    overdue_invoices_amount = sum(invoice.amount for invoice in overdue_invoices)
    
    # الحصول على إحصائيات الفواتير حسب الحالة
    paid_invoices_count = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status == 'paid'
    ).count()
    
    unpaid_invoices_count = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status == 'unpaid'
    ).count()
    
    partial_invoices_count = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status == 'partial'
    ).count()
    
    cancelled_invoices_count = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date),
        Invoice.status == 'cancelled'
    ).count()
    
    # الحصول على أحدث الفواتير
    recent_invoices = Invoice.query.filter(
        Invoice.issue_date.between(start_date, end_date)
    ).order_by(Invoice.issue_date.desc()).limit(10).all()
    
    # الحصول على أحدث المدفوعات
    recent_payments = Payment.query.filter(
        Payment.payment_date.between(start_date, end_date)
    ).order_by(Payment.payment_date.desc()).limit(10).all()
    
    # إعداد بيانات الرسم البياني الشهري
    monthly_labels = []
    monthly_invoices = []
    monthly_payments = []
    
    # تحديد عدد الأشهر بناءً على الفترة
    if period == 'month':
        num_months = 1
    elif period == 'quarter':
        num_months = 3
    elif period == 'year':
        num_months = 12
    else:
        num_months = 12  # عرض آخر 12 شهر للفترة 'all'
    
    # حساب الإيرادات الشهرية
    for i in range(num_months):
        if period == 'month':
            # عرض الأيام في الشهر الحالي
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            for day in range(1, days_in_month + 1, 5):  # كل 5 أيام
                day_date = datetime(today.year, today.month, min(day, days_in_month))
                day_end = datetime(today.year, today.month, min(day + 4, days_in_month), 23, 59, 59)
                
                monthly_labels.append(f"{day}-{min(day + 4, days_in_month)}")
                
                # حساب مبالغ الفواتير والمدفوعات لهذه الفترة
                invoices_amount = db.session.query(func.sum(Invoice.amount)).filter(
                    Invoice.issue_date.between(day_date, day_end)
                ).scalar() or 0
                
                payments_amount = db.session.query(func.sum(Payment.amount)).filter(
                    Payment.payment_date.between(day_date, day_end)
                ).scalar() or 0
                
                monthly_invoices.append(float(invoices_amount))
                monthly_payments.append(float(payments_amount))
        else:
            # عرض الأشهر
            month = (today.month - i) % 12
            if month == 0:
                month = 12
            year = today.year - ((i - month + today.month) // 12)
            
            month_start = datetime(year, month, 1)
            month_end = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)
            
            month_name = month_start.strftime('%B %Y')
            monthly_labels.append(month_name)
            
            # حساب مبالغ الفواتير والمدفوعات لهذا الشهر
            invoices_amount = db.session.query(func.sum(Invoice.amount)).filter(
                Invoice.issue_date.between(month_start, month_end)
            ).scalar() or 0
            
            payments_amount = db.session.query(func.sum(Payment.amount)).filter(
                Payment.payment_date.between(month_start, month_end)
            ).scalar() or 0
            
            monthly_invoices.append(float(invoices_amount))
            monthly_payments.append(float(payments_amount))
    
    # عكس الترتيب ليكون من الأقدم إلى الأحدث
    monthly_labels.reverse()
    monthly_invoices.reverse()
    monthly_payments.reverse()
    
    # حساب إجمالي الإيرادات
    total_revenue = total_payments_amount
    
    return render_template('reports/financial_summary.html',
                          period=period,
                          period_text=period_text,
                          report_date=datetime.utcnow(),
                          total_invoices_count=total_invoices_count,
                          total_invoices_amount=total_invoices_amount,
                          total_payments_count=total_payments_count,
                          total_payments_amount=total_payments_amount,
                          pending_invoices_count=pending_invoices_count,
                          pending_invoices_amount=pending_invoices_amount,
                          overdue_invoices_count=overdue_invoices_count,
                          overdue_invoices_amount=overdue_invoices_amount,
                          paid_invoices_count=paid_invoices_count,
                          unpaid_invoices_count=unpaid_invoices_count,
                          partial_invoices_count=partial_invoices_count,
                          cancelled_invoices_count=cancelled_invoices_count,
                          recent_invoices=recent_invoices,
                          recent_payments=recent_payments,
                          overdue_invoices=overdue_invoices,
                          monthly_labels=monthly_labels,
                          monthly_invoices=monthly_invoices,
                          monthly_payments=monthly_payments,
                          total_revenue=total_revenue)

@reports_bp.route('/lawyers/performance')
@login_required
def lawyers_performance():
    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # الحصول على الفترة المطلوبة
    period = request.args.get('period', 'year')
    
    # تحديد نطاق التاريخ بناءً على الفترة
    today = datetime.utcnow().date()
    if period == 'month':
        start_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1], 23, 59, 59)
        period_text = f"الشهر الحالي ({today.strftime('%B %Y')})"
    elif period == 'quarter':
        quarter = (today.month - 1) // 3 + 1
        start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1)
        end_month = quarter * 3
        end_date = datetime(today.year, end_month, calendar.monthrange(today.year, end_month)[1], 23, 59, 59)
        period_text = f"الربع الحالي (Q{quarter} {today.year})"
    elif period == 'year':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
        period_text = f"السنة الحالية ({today.year})"
    else:  # 'all'
        start_date = datetime(2000, 1, 1)  # تاريخ قديم جداً
        end_date = datetime(2100, 12, 31, 23, 59, 59)  # تاريخ مستقبلي جداً
        period_text = "كل الفترات"
    
    # الحصول على المحامين
    lawyers = User.query.filter(User.role.in_(['admin', 'lawyer'])).all()
    
    # إعداد بيانات المحامين
    lawyer_names = []
    active_cases_by_lawyer = []
    closed_cases_by_lawyer = []
    success_rates = []
    
    for lawyer in lawyers:
        lawyer_names.append(f"{lawyer.first_name} {lawyer.last_name}")
        
        # حساب عدد القضايا النشطة
        active_cases = Case.query.filter(
            Case.lawyer_id == lawyer.id,
            Case.status.in_(['open', 'pending', 'postponed']),
            Case.opened_date.between(start_date, end_date)
        ).count()
        active_cases_by_lawyer.append(active_cases)
        
        # حساب عدد القضايا المغلقة
        closed_cases = Case.query.filter(
            Case.lawyer_id == lawyer.id,
            Case.status == 'closed',
            Case.closed_date.between(start_date, end_date) if Case.closed_date is not None else False
        ).count()
        closed_cases_by_lawyer.append(closed_cases)
        
        # حساب معدل النجاح
        won_cases = Case.query.filter(
            Case.lawyer_id == lawyer.id,
            Case.status == 'closed',
            Case.outcome == 'won',
            Case.closed_date.between(start_date, end_date) if Case.closed_date is not None else False
        ).count()
        
        success_rate = (won_cases / closed_cases * 100) if closed_cases > 0 else 0
        success_rates.append(success_rate)
        
        # إضافة إحصائيات إضافية للمحامي
        lawyer.stats = {
            'total_cases': active_cases + closed_cases,
            'active_cases': active_cases,
            'closed_cases': closed_cases,
            'success_rate': success_rate,
            'revenue': 0,  # سيتم حسابها لاحقاً
            'avg_case_duration': 0,  # سيتم حسابها لاحقاً
            'appointments_count': 0  # سيتم حسابها لاحقاً
        }
        
        # حساب الإيرادات
        lawyer_cases = Case.query.filter_by(lawyer_id=lawyer.id).all()
        case_ids = [case.id for case in lawyer_cases]
        
        invoices = Invoice.query.filter(
            Invoice.case_id.in_(case_ids) if case_ids else False,
            Invoice.issue_date.between(start_date, end_date)
        ).all()
        
        lawyer.stats['revenue'] = sum(invoice.amount for invoice in invoices)
        
        # حساب متوسط مدة القضايا
        closed_cases_with_duration = Case.query.filter(
            Case.lawyer_id == lawyer.id,
            Case.status == 'closed',
            Case.closed_date.between(start_date, end_date) if Case.closed_date is not None else False,
            Case.closed_date is not None,
            Case.opened_date is not None
        ).all()
        
        if closed_cases_with_duration:
            total_duration = sum((case.closed_date - case.opened_date).days for case in closed_cases_with_duration)
            lawyer.stats['avg_case_duration'] = total_duration // len(closed_cases_with_duration)
        
        # حساب عدد المواعيد
        lawyer.stats['appointments_count'] = Appointment.query.filter(
            Appointment.user_id == lawyer.id,
            Appointment.date.between(start_date, end_date)
        ).count()
        
        # إضافة نص العرض للدور
        if lawyer.role == 'admin':
            lawyer.role_display = 'مسؤول'
        elif lawyer.role == 'lawyer':
            lawyer.role_display = 'محامي'
        else:
            lawyer.role_display = 'موظف'
    
    # الحصول على القضايا المغلقة حديثاً
    recent_closed_cases = Case.query.filter(
        Case.status == 'closed',
        Case.closed_date.between(start_date, end_date) if Case.closed_date is not None else False
    ).order_by(Case.closed_date.desc()).limit(10).all()
    
    # إضافة مدة القضايا
    for case in recent_closed_cases:
        if case.closed_date and case.opened_date:
            case.duration_days = (case.closed_date - case.opened_date).days
        else:
            case.duration_days = 0
    
    # حساب إجمالي القضايا
    total_cases = sum(lawyer.stats['total_cases'] for lawyer in lawyers)
    
    return render_template('reports/lawyers_performance.html',
                          period=period,
                          period_text=period_text,
                          report_date=datetime.utcnow(),
                          lawyers=lawyers,
                          lawyer_names=lawyer_names,
                          active_cases_by_lawyer=active_cases_by_lawyer,
                          closed_cases_by_lawyer=closed_cases_by_lawyer,
                          success_rates=success_rates,
                          recent_closed_cases=recent_closed_cases,
                          total_cases=total_cases)

# إضافة المزيد من مسارات التقارير حسب الحاجة
@reports_bp.route('/cases/type')
@login_required
def cases_by_type():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/cases/court')
@login_required
def cases_by_court():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/cases/summary')
@login_required
def cases_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/invoices/summary')
@login_required
def invoices_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/payments/summary')
@login_required
def payments_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/revenue/monthly')
@login_required
def revenue_by_month():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/clients/activity')
@login_required
def clients_activity():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/clients/top')
@login_required
def top_clients():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/clients/new')
@login_required
def new_clients():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/clients/summary')
@login_required
def clients_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/appointments/type')
@login_required
def appointments_by_type():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/appointments/status')
@login_required
def appointments_by_status():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/appointments/upcoming')
@login_required
def upcoming_appointments():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/appointments/summary')
@login_required
def appointments_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/documents/type')
@login_required
def documents_by_type():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/documents/case')
@login_required
def documents_by_case():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/documents/recent')
@login_required
def recent_documents():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/documents/summary')
@login_required
def documents_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/lawyer/<int:lawyer_id>')
@login_required
def lawyer_details(lawyer_id):
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.lawyers_performance'))

@reports_bp.route('/cases/success-rate')
@login_required
def cases_success_rate():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/office/performance')
@login_required
def office_performance():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))

@reports_bp.route('/performance/summary')
@login_required
def performance_summary():
    flash('هذا التقرير قيد التطوير', 'info')
    return redirect(url_for('reports.index'))
