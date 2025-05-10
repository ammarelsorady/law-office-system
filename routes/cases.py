from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime
from functools import wraps

from models import db, Case, Client, User, Document
from routes.auth import login_required, get_current_user

cases_bp = Blueprint('cases', __name__, url_prefix='/cases')

@cases_bp.route('/')
@login_required
def index():
    # الحصول على جميع القضايا أو فقط قضايا المحامي الحالي إذا لم يكن مسؤولاً
    if session.get('role') == 'admin':
        cases = Case.query.all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()

    return render_template('cases/index.html', cases=cases)

@cases_bp.route('/view/<int:case_id>')
@login_required
def view_case(case_id):
    case = Case.query.get_or_404(case_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and case.lawyer_id != session.get('user_id'):
        flash('ليس لديك صلاحية للوصول إلى هذه القضية', 'danger')
        return redirect(url_for('cases.index'))

    return render_template('cases/view.html', case=case)

@cases_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_case():
    # التحقق من صلاحيات المستخدم
    if session.get('role') not in ['admin', 'lawyer']:
        flash('ليس لديك صلاحية لإضافة قضية', 'danger')
        return redirect(url_for('cases.index'))

    clients = Client.query.all()
    lawyers = User.query.filter(User.role.in_(['admin', 'lawyer'])).all()

    if request.method == 'POST':
        case_number = request.form.get('case_number')
        title = request.form.get('title')
        description = request.form.get('description')
        case_type = request.form.get('case_type')
        court = request.form.get('court')
        status = request.form.get('status')
        opponent_name = request.form.get('opponent_name')
        client_id = request.form.get('client_id')
        lawyer_id = request.form.get('lawyer_id')

        # التحقق من عدم وجود قضية بنفس الرقم
        if Case.query.filter_by(case_number=case_number).first():
            flash('رقم القضية موجود بالفعل', 'danger')
            return redirect(url_for('cases.add_case'))

        # إنشاء قضية جديدة
        new_case = Case(
            case_number=case_number,
            title=title,
            description=description,
            case_type=case_type,
            court=court,
            status=status,
            opponent_name=opponent_name,
            client_id=client_id,
            lawyer_id=lawyer_id,
            opened_date=datetime.utcnow()
        )

        db.session.add(new_case)
        db.session.commit()

        flash('تم إضافة القضية بنجاح', 'success')
        return redirect(url_for('cases.view_case', case_id=new_case.id))

    return render_template('cases/add.html', clients=clients, lawyers=lawyers)

@cases_bp.route('/edit/<int:case_id>', methods=['GET', 'POST'])
@login_required
def edit_case(case_id):
    case = Case.query.get_or_404(case_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and case.lawyer_id != session.get('user_id'):
        flash('ليس لديك صلاحية لتعديل هذه القضية', 'danger')
        return redirect(url_for('cases.index'))

    clients = Client.query.all()
    lawyers = User.query.filter(User.role.in_(['admin', 'lawyer'])).all()

    if request.method == 'POST':
        case.title = request.form.get('title')
        case.description = request.form.get('description')
        case.case_type = request.form.get('case_type')
        case.court = request.form.get('court')
        case.status = request.form.get('status')
        case.opponent_name = request.form.get('opponent_name')

        # فقط المسؤول يمكنه تغيير العميل والمحامي
        if session.get('role') == 'admin':
            case.client_id = request.form.get('client_id')
            case.lawyer_id = request.form.get('lawyer_id')

        # إذا تم إغلاق القضية، قم بتعيين تاريخ الإغلاق
        if case.status == 'closed' and not case.closed_date:
            case.closed_date = datetime.utcnow()
        # إذا تم إعادة فتح القضية، قم بإزالة تاريخ الإغلاق
        elif case.status != 'closed' and case.closed_date:
            case.closed_date = None

        db.session.commit()
        flash('تم تحديث القضية بنجاح', 'success')
        return redirect(url_for('cases.view_case', case_id=case.id))

    return render_template('cases/edit.html', case=case, clients=clients, lawyers=lawyers)

@cases_bp.route('/delete/<int:case_id>', methods=['POST'])
@login_required
def delete_case(case_id):
    # فقط المسؤول يمكنه حذف القضايا
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لحذف القضايا', 'danger')
        return redirect(url_for('cases.index'))

    case = Case.query.get_or_404(case_id)

    # حذف القضية
    db.session.delete(case)
    db.session.commit()

    flash('تم حذف القضية بنجاح', 'success')
    return redirect(url_for('cases.index'))

@cases_bp.route('/search', methods=['GET'])
@login_required
def search_cases():
    query = request.args.get('query', '')

    if not query:
        return redirect(url_for('cases.index'))

    # البحث في القضايا
    if session.get('role') == 'admin':
        cases = Case.query.filter(
            (Case.case_number.like(f'%{query}%')) |
            (Case.title.like(f'%{query}%')) |
            (Case.description.like(f'%{query}%')) |
            (Case.opponent_name.like(f'%{query}%'))
        ).all()
    else:
        cases = Case.query.filter(
            (Case.lawyer_id == session.get('user_id')) &
            (
                (Case.case_number.like(f'%{query}%')) |
                (Case.title.like(f'%{query}%')) |
                (Case.description.like(f'%{query}%')) |
                (Case.opponent_name.like(f'%{query}%'))
            )
        ).all()

    return render_template('cases/search_results.html', cases=cases, query=query)
