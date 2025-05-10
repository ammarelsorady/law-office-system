from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from datetime import datetime, timedelta

from models import db, Invoice, Payment, Client, Case, User
from routes.auth import login_required, get_current_user

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')

@invoices_bp.route('/')
@login_required
def index():
    # الحصول على جميع الفواتير أو فقط الفواتير المرتبطة بقضايا المحامي الحالي
    if session.get('role') == 'admin':
        invoices = Invoice.query.order_by(Invoice.issue_date.desc()).all()
    else:
        # الحصول على قضايا المحامي
        lawyer_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()
        case_ids = [case.id for case in lawyer_cases]

        # الحصول على الفواتير المرتبطة بهذه القضايا
        invoices = Invoice.query.filter(Invoice.case_id.in_(case_ids)).order_by(Invoice.issue_date.desc()).all()

    return render_template('invoices/index.html', invoices=invoices)

@invoices_bp.route('/view/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        # التحقق مما إذا كانت الفاتورة مرتبطة بقضية للمحامي الحالي
        if invoice.case and invoice.case.lawyer_id != session.get('user_id'):
            flash('ليس لديك صلاحية للوصول إلى هذه الفاتورة', 'danger')
            return redirect(url_for('invoices.index'))

    # حساب المبلغ المدفوع والمتبقي
    paid_amount = sum(payment.amount for payment in invoice.payments)
    remaining_amount = invoice.amount - paid_amount

    return render_template('invoices/view.html', invoice=invoice, paid_amount=paid_amount, remaining_amount=remaining_amount)

@invoices_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_invoice():
    # الحصول على العملاء والقضايا
    clients = Client.query.all()

    if session.get('role') == 'admin':
        cases = Case.query.all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()

    if request.method == 'POST':
        # توليد رقم فاتورة فريد
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{Invoice.query.count() + 1:04d}"

        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        issue_date = datetime.utcnow()

        # تعيين تاريخ الاستحقاق (30 يومًا من تاريخ الإصدار افتراضيًا)
        due_date_str = request.form.get('due_date')
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        else:
            due_date = issue_date + timedelta(days=30)

        status = request.form.get('status')
        client_id = request.form.get('client_id')
        case_id = request.form.get('case_id') or None

        # إنشاء فاتورة جديدة
        new_invoice = Invoice(
            invoice_number=invoice_number,
            amount=amount,
            description=description,
            issue_date=issue_date,
            due_date=due_date,
            status=status,
            client_id=client_id,
            case_id=case_id
        )

        db.session.add(new_invoice)
        db.session.commit()

        flash('تم إنشاء الفاتورة بنجاح', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=new_invoice.id))

    return render_template('invoices/add.html', clients=clients, cases=cases)

@invoices_bp.route('/edit/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        if invoice.case and invoice.case.lawyer_id != session.get('user_id'):
            flash('ليس لديك صلاحية لتعديل هذه الفاتورة', 'danger')
            return redirect(url_for('invoices.index'))

    # الحصول على العملاء والقضايا
    clients = Client.query.all()

    if session.get('role') == 'admin':
        cases = Case.query.all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()

    if request.method == 'POST':
        invoice.amount = float(request.form.get('amount'))
        invoice.description = request.form.get('description')

        # تعيين تاريخ الاستحقاق
        due_date_str = request.form.get('due_date')
        if due_date_str:
            invoice.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

        invoice.status = request.form.get('status')

        # فقط المسؤول يمكنه تغيير العميل والقضية
        if session.get('role') == 'admin':
            invoice.client_id = request.form.get('client_id')
            case_id = request.form.get('case_id')
            invoice.case_id = case_id if case_id else None

        db.session.commit()
        flash('تم تحديث الفاتورة بنجاح', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))

    return render_template('invoices/edit.html', invoice=invoice, clients=clients, cases=cases)

@invoices_bp.route('/delete/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    # فقط المسؤول يمكنه حذف الفواتير
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لحذف الفواتير', 'danger')
        return redirect(url_for('invoices.index'))

    invoice = Invoice.query.get_or_404(invoice_id)

    # التحقق من عدم وجود مدفوعات مرتبطة بالفاتورة
    if invoice.payments:
        flash('لا يمكن حذف الفاتورة لأنها تحتوي على مدفوعات', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))

    db.session.delete(invoice)
    db.session.commit()

    flash('تم حذف الفاتورة بنجاح', 'success')
    return redirect(url_for('invoices.index'))

@invoices_bp.route('/<int:invoice_id>/add_payment', methods=['GET', 'POST'])
@login_required
def add_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and session.get('role') != 'lawyer':
        flash('ليس لديك صلاحية لإضافة مدفوعات', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))

    # حساب المبلغ المدفوع والمتبقي
    paid_amount = sum(payment.amount for payment in invoice.payments)
    remaining_amount = invoice.amount - paid_amount

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        payment_method = request.form.get('payment_method')
        reference_number = request.form.get('reference_number')
        notes = request.form.get('notes')

        # التحقق من أن المبلغ المدفوع لا يتجاوز المبلغ المتبقي
        if amount > remaining_amount:
            flash('المبلغ المدفوع يتجاوز المبلغ المتبقي للفاتورة', 'danger')
            return redirect(url_for('invoices.add_payment', invoice_id=invoice_id))

        # إنشاء دفعة جديدة
        new_payment = Payment(
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            invoice_id=invoice_id,
            received_by=session.get('user_id')
        )

        db.session.add(new_payment)

        # تحديث حالة الفاتورة
        new_paid_amount = paid_amount + amount
        if new_paid_amount >= invoice.amount:
            invoice.status = 'paid'
        elif new_paid_amount > 0:
            invoice.status = 'partial'

        db.session.commit()

        flash('تم تسجيل الدفعة بنجاح', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))

    return render_template('invoices/add_payment.html', invoice=invoice, remaining_amount=remaining_amount)

@invoices_bp.route('/payments')
@login_required
def payments():
    # الحصول على جميع المدفوعات أو فقط المدفوعات المرتبطة بقضايا المحامي الحالي
    if session.get('role') == 'admin':
        payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    else:
        # الحصول على قضايا المحامي
        lawyer_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()
        case_ids = [case.id for case in lawyer_cases]

        # الحصول على الفواتير المرتبطة بهذه القضايا
        invoice_ids = [invoice.id for invoice in Invoice.query.filter(Invoice.case_id.in_(case_ids)).all()]

        # الحصول على المدفوعات المرتبطة بهذه الفواتير
        payments = Payment.query.filter(Payment.invoice_id.in_(invoice_ids)).order_by(Payment.payment_date.desc()).all()

    return render_template('invoices/payments.html', payments=payments)
