from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# جدول العلاقة بين القضايا والمستندات
case_documents = db.Table('case_documents',
    db.Column('case_id', db.Integer, db.ForeignKey('case.id'), primary_key=True),
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'), primary_key=True)
)

# جدول العلاقة بين العملاء والمستندات
client_documents = db.Table('client_documents',
    db.Column('client_id', db.Integer, db.ForeignKey('client.id'), primary_key=True),
    db.Column('document_id', db.Integer, db.ForeignKey('document.id'), primary_key=True)
)

class User(db.Model):
    """نموذج المستخدم (المحامي أو الموظف)"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='staff')  # admin, lawyer, staff
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # العلاقات
    cases = db.relationship('Case', backref='lawyer', lazy=True)
    appointments = db.relationship('Appointment', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Client(db.Model):
    """نموذج العميل"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    id_number = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    # العلاقات
    cases = db.relationship('Case', backref='client', lazy=True)
    invoices = db.relationship('Invoice', backref='client', lazy=True)
    documents = db.relationship('Document', secondary=client_documents, lazy='subquery',
                               backref=db.backref('clients', lazy=True))

    def __repr__(self):
        return f'<Client {self.first_name} {self.last_name}>'

class Case(db.Model):
    """نموذج القضية"""
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    case_type = db.Column(db.String(50), nullable=False)
    court = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open')  # open, closed, pending, postponed
    opponent_name = db.Column(db.String(100))
    opened_date = db.Column(db.DateTime, default=datetime.utcnow)
    closed_date = db.Column(db.DateTime)

    # العلاقات - المفاتيح الخارجية
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    lawyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # العلاقات
    appointments = db.relationship('Appointment', backref='case', lazy=True)
    invoices = db.relationship('Invoice', backref='case', lazy=True)
    documents = db.relationship('Document', secondary=case_documents, lazy='subquery',
                               backref=db.backref('cases', lazy=True))

    def __repr__(self):
        return f'<Case {self.case_number}>'

class Appointment(db.Model):
    """نموذج المواعيد والجلسات"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(100))
    appointment_type = db.Column(db.String(20), default='hearing')  # hearing, meeting, reminder
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, postponed
    notes = db.Column(db.Text)

    # العلاقات - المفاتيح الخارجية
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Appointment {self.title} on {self.date}>'

class Document(db.Model):
    """نموذج المستندات"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20))
    file_size = db.Column(db.Integer)  # بالبايت
    document_type = db.Column(db.String(50))  # contract, court_document, id, etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات - المفاتيح الخارجية
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # العلاقات مع القضايا والعملاء تم تعريفها في جداول العلاقات

    def __repr__(self):
        return f'<Document {self.title}>'

class Invoice(db.Model):
    """نموذج الفواتير"""
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, partial, cancelled

    # العلاقات - المفاتيح الخارجية
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))

    # العلاقات
    payments = db.relationship('Payment', backref='invoice', lazy=True)

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'

class Payment(db.Model):
    """نموذج المدفوعات"""
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), default='cash')  # cash, bank_transfer, credit_card, etc.
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)

    # العلاقات - المفاتيح الخارجية
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    received_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Payment {self.id} for Invoice {self.invoice_id}>'
