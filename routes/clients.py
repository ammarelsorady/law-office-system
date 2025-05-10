from flask import Blueprint, render_template, redirect, url_for, flash, request, session

from models import db, Client, Case
from routes.auth import login_required

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/')
@login_required
def index():
    clients = Client.query.all()
    return render_template('clients/index.html', clients=clients)

@clients_bp.route('/view/<int:client_id>')
@login_required
def view_client(client_id):
    client = Client.query.get_or_404(client_id)

    # الحصول على قضايا العميل
    if session.get('role') == 'admin':
        cases = Case.query.filter_by(client_id=client_id).all()
    else:
        cases = Case.query.filter_by(client_id=client_id, lawyer_id=session.get('user_id')).all()

    return render_template('clients/view.html', client=client, cases=cases)

@clients_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        id_number = request.form.get('id_number')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        notes = request.form.get('notes')

        # التحقق من عدم وجود عميل بنفس رقم الهوية
        if id_number and Client.query.filter_by(id_number=id_number).first():
            flash('رقم الهوية موجود بالفعل', 'danger')
            return redirect(url_for('clients.add_client'))

        # إنشاء عميل جديد
        new_client = Client(
            first_name=first_name,
            last_name=last_name,
            id_number=id_number,
            email=email,
            phone=phone,
            address=address,
            notes=notes
        )

        db.session.add(new_client)
        db.session.commit()

        flash('تم إضافة العميل بنجاح', 'success')
        return redirect(url_for('clients.view_client', client_id=new_client.id))

    return render_template('clients/add.html')

@clients_bp.route('/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        client.first_name = request.form.get('first_name')
        client.last_name = request.form.get('last_name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.notes = request.form.get('notes')

        # التحقق من رقم الهوية إذا تم تغييره
        id_number = request.form.get('id_number')
        if id_number != client.id_number:
            if id_number and Client.query.filter_by(id_number=id_number).first():
                flash('رقم الهوية موجود بالفعل', 'danger')
                return redirect(url_for('clients.edit_client', client_id=client_id))
            client.id_number = id_number

        db.session.commit()
        flash('تم تحديث بيانات العميل بنجاح', 'success')
        return redirect(url_for('clients.view_client', client_id=client.id))

    return render_template('clients/edit.html', client=client)

@clients_bp.route('/delete/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    # فقط المسؤول يمكنه حذف العملاء
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية لحذف العملاء', 'danger')
        return redirect(url_for('clients.index'))

    client = Client.query.get_or_404(client_id)

    # التحقق من عدم وجود قضايا مرتبطة بالعميل
    if client.cases:
        flash('لا يمكن حذف العميل لأنه مرتبط بقضايا', 'danger')
        return redirect(url_for('clients.view_client', client_id=client_id))

    # حذف العميل
    db.session.delete(client)
    db.session.commit()

    flash('تم حذف العميل بنجاح', 'success')
    return redirect(url_for('clients.index'))

@clients_bp.route('/search', methods=['GET'])
@login_required
def search_clients():
    query = request.args.get('query', '')

    if not query:
        return redirect(url_for('clients.index'))

    # البحث في العملاء
    clients = Client.query.filter(
        (Client.first_name.like(f'%{query}%')) |
        (Client.last_name.like(f'%{query}%')) |
        (Client.id_number.like(f'%{query}%')) |
        (Client.phone.like(f'%{query}%')) |
        (Client.email.like(f'%{query}%'))
    ).all()

    return render_template('clients/search_results.html', clients=clients, query=query)
