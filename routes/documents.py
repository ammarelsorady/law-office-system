import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, session
from werkzeug.utils import secure_filename
from datetime import datetime

from models import db, Document, Case, Client
from routes.auth import login_required, get_current_user

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/')
@login_required
def index():
    # الحصول على جميع المستندات أو فقط المستندات المرتبطة بقضايا المحامي الحالي
    if session.get('role') == 'admin':
        documents = Document.query.order_by(Document.uploaded_at.desc()).all()
    else:
        # الحصول على قضايا المحامي
        lawyer_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()

        # الحصول على المستندات المرتبطة بهذه القضايا
        documents = []
        for case in lawyer_cases:
            for doc in case.documents:
                if doc not in documents:
                    documents.append(doc)

    return render_template('documents/index.html', documents=documents)

@documents_bp.route('/view/<int:document_id>')
@login_required
def view_document(document_id):
    document = Document.query.get_or_404(document_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        # التحقق مما إذا كان المستند مرتبط بقضية للمحامي الحالي
        has_access = False
        for case in document.cases:
            if case.lawyer_id == session.get('user_id'):
                has_access = True
                break

        if not has_access:
            flash('ليس لديك صلاحية للوصول إلى هذا المستند', 'danger')
            return redirect(url_for('documents.index'))

    return render_template('documents/view.html', document=document)

@documents_bp.route('/preview/<int:document_id>')
@login_required
def preview_document(document_id):
    document = Document.query.get_or_404(document_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        # التحقق مما إذا كان المستند مرتبط بقضية للمحامي الحالي
        has_access = False
        for case in document.cases:
            if case.lawyer_id == session.get('user_id'):
                has_access = True
                break

        if not has_access:
            flash('ليس لديك صلاحية للوصول إلى هذا المستند', 'danger')
            return redirect(url_for('documents.index'))

    # استخراج اسم الملف من المسار
    filename = os.path.basename(document.file_path)
    directory = os.path.dirname(document.file_path)

    return send_from_directory(directory, filename, as_attachment=False)

@documents_bp.route('/download/<int:document_id>')
@login_required
def download_document(document_id):
    document = Document.query.get_or_404(document_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        # التحقق مما إذا كان المستند مرتبط بقضية للمحامي الحالي
        has_access = False
        for case in document.cases:
            if case.lawyer_id == session.get('user_id'):
                has_access = True
                break

        if not has_access:
            flash('ليس لديك صلاحية للوصول إلى هذا المستند', 'danger')
            return redirect(url_for('documents.index'))

    # استخراج اسم الملف من المسار
    filename = os.path.basename(document.file_path)
    directory = os.path.dirname(document.file_path)

    return send_from_directory(directory, filename, as_attachment=True)

@documents_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_document():
    # الحصول على القضايا والعملاء
    if session.get('role') == 'admin':
        cases = Case.query.all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()

    clients = Client.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        document_type = request.form.get('document_type')
        case_ids = request.form.getlist('case_ids')
        client_ids = request.form.getlist('client_ids')

        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('لم يتم تحديد ملف', 'danger')
            return redirect(request.url)

        file = request.files['file']

        # التحقق من أن الملف ليس فارغًا
        if file.filename == '':
            flash('لم يتم تحديد ملف', 'danger')
            return redirect(request.url)

        # التحقق من أن الملف له امتداد مسموح به
        if file and allowed_file(file.filename):
            # تأمين اسم الملف
            filename = secure_filename(file.filename)

            # إنشاء مسار فريد للملف
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            unique_filename = f"{timestamp}_{filename}"

            # حفظ الملف
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            # إنشاء مستند جديد
            new_document = Document(
                title=title,
                description=description,
                file_path=file_path,
                file_type=file.content_type,
                file_size=os.path.getsize(file_path),
                document_type=document_type,
                uploaded_by=session.get('user_id')
            )

            db.session.add(new_document)
            db.session.flush()  # للحصول على معرف المستند

            # ربط المستند بالقضايا
            if case_ids:
                for case_id in case_ids:
                    case = Case.query.get(case_id)
                    if case:
                        new_document.cases.append(case)

            # ربط المستند بالعملاء
            if client_ids:
                for client_id in client_ids:
                    client = Client.query.get(client_id)
                    if client:
                        new_document.clients.append(client)

            db.session.commit()

            flash('تم رفع المستند بنجاح', 'success')
            return redirect(url_for('documents.view_document', document_id=new_document.id))
        else:
            flash('نوع الملف غير مسموح به', 'danger')
            return redirect(request.url)

    return render_template('documents/add.html', cases=cases, clients=clients)

@documents_bp.route('/edit/<int:document_id>', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    document = Document.query.get_or_404(document_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and document.uploaded_by != session.get('user_id'):
        has_access = False
        for case in document.cases:
            if case.lawyer_id == session.get('user_id'):
                has_access = True
                break

        if not has_access:
            flash('ليس لديك صلاحية لتعديل هذا المستند', 'danger')
            return redirect(url_for('documents.index'))

    # الحصول على القضايا والعملاء
    if session.get('role') == 'admin':
        cases = Case.query.all()
    else:
        cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()

    clients = Client.query.all()

    # الحصول على معرفات القضايا والعملاء المرتبطة بالمستند
    document_case_ids = [case.id for case in document.cases]
    document_client_ids = [client.id for client in document.clients]

    if request.method == 'POST':
        document.title = request.form.get('title')
        document.description = request.form.get('description')
        document.document_type = request.form.get('document_type')

        # تحديث ارتباطات القضايا
        case_ids = request.form.getlist('case_ids')
        document.cases = []
        if case_ids:
            for case_id in case_ids:
                case = Case.query.get(case_id)
                if case:
                    document.cases.append(case)

        # تحديث ارتباطات العملاء
        client_ids = request.form.getlist('client_ids')
        document.clients = []
        if client_ids:
            for client_id in client_ids:
                client = Client.query.get(client_id)
                if client:
                    document.clients.append(client)

        # التحقق من وجود ملف جديد للتحميل
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']

            # التحقق من نوع الملف
            allowed_extensions = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
            if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                # حذف الملف القديم إذا كان موجودًا
                if os.path.exists(document.file_path):
                    try:
                        os.remove(document.file_path)
                    except:
                        pass

                # حفظ الملف الجديد
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)

                # تحديث معلومات الملف
                document.file_path = file_path
                document.file_type = file.content_type
                document.file_size = os.path.getsize(file_path)
                document.uploaded_at = datetime.utcnow()
            else:
                flash('نوع الملف غير مسموح به', 'danger')
                return redirect(request.url)

        db.session.commit()
        flash('تم تحديث المستند بنجاح', 'success')
        return redirect(url_for('documents.view_document', document_id=document.id))

    return render_template('documents/edit.html', document=document, cases=cases, clients=clients,
                          document_case_ids=document_case_ids, document_client_ids=document_client_ids)

@documents_bp.route('/delete/<int:document_id>', methods=['POST'])
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)

    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and document.uploaded_by != session.get('user_id'):
        flash('ليس لديك صلاحية لحذف هذا المستند', 'danger')
        return redirect(url_for('documents.index'))

    # حذف الملف من نظام الملفات
    try:
        os.remove(document.file_path)
    except OSError:
        # إذا لم يتم العثور على الملف، تجاهل الخطأ
        pass

    # حذف المستند من قاعدة البيانات
    db.session.delete(document)
    db.session.commit()

    flash('تم حذف المستند بنجاح', 'success')
    return redirect(url_for('documents.index'))

@documents_bp.route('/search', methods=['GET'])
@login_required
def search_documents():
    query = request.args.get('query', '')

    if not query:
        return redirect(url_for('documents.index'))

    # البحث في المستندات
    if session.get('role') == 'admin':
        documents = Document.query.filter(
            (Document.title.like(f'%{query}%')) |
            (Document.description.like(f'%{query}%')) |
            (Document.document_type.like(f'%{query}%'))
        ).all()
    else:
        # الحصول على قضايا المحامي
        lawyer_cases = Case.query.filter_by(lawyer_id=session.get('user_id')).all()
        case_ids = [case.id for case in lawyer_cases]

        # البحث في المستندات المرتبطة بقضايا المحامي
        documents = []
        for case in lawyer_cases:
            for doc in case.documents:
                if (query.lower() in doc.title.lower() or
                    (doc.description and query.lower() in doc.description.lower()) or
                    (doc.document_type and query.lower() in doc.document_type.lower())) and doc not in documents:
                    documents.append(doc)

    return render_template('documents/search_results.html', documents=documents, query=query)
