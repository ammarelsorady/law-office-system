from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash
from datetime import datetime
from functools import wraps

from models import db, User

# دالة للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'info')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# دالة للحصول على المستخدم الحالي
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('هذا الحساب غير نشط. يرجى الاتصال بالمسؤول', 'warning')
            return redirect(url_for('auth.login'))

        # تسجيل الدخول باستخدام الجلسة
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['first_name'] = user.first_name
        session['last_name'] = user.last_name

        user.last_login = datetime.utcnow()
        db.session.commit()

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard.index')

        flash(f'مرحبًا بك {user.first_name}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # تسجيل الخروج بإزالة بيانات الجلسة
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('first_name', None)
    session.pop('last_name', None)
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')

        # تحديث كلمة المرور إذا تم إدخالها
        password = request.form.get('password')
        if password and password.strip():
            user.set_password(password)

        # تحديث بيانات الجلسة
        session['first_name'] = user.first_name
        session['last_name'] = user.last_name

        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=user)

@auth_bp.route('/users')
@login_required
def users_list():
    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.all()
    return render_template('auth/users_list.html', users=users)

@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin':
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        role = request.form.get('role')

        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('auth.add_user'))

        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return redirect(url_for('auth.add_user'))

        # إنشاء مستخدم جديد
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role,
            is_active=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('تم إضافة المستخدم بنجاح', 'success')
        return redirect(url_for('auth.users_list'))

    return render_template('auth/add_user.html')

@auth_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # التحقق من صلاحيات المستخدم
    if session.get('role') != 'admin' and session.get('user_id') != user_id:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')

        # فقط المسؤول يمكنه تغيير الدور والحالة
        if session.get('role') == 'admin':
            user.role = request.form.get('role')
            user.is_active = True if request.form.get('is_active') else False

        # تحديث كلمة المرور إذا تم إدخالها
        password = request.form.get('password')
        if password and password.strip():
            user.set_password(password)

        db.session.commit()
        flash('تم تحديث المستخدم بنجاح', 'success')

        if session.get('role') == 'admin':
            return redirect(url_for('auth.users_list'))
        else:
            return redirect(url_for('auth.profile'))

    return render_template('auth/edit_user.html', user=user)
