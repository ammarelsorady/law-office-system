from flask import Flask, render_template
from datetime import timedelta
import os

from config import Config
from models import db
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.clients import clients_bp
from routes.cases import cases_bp
from routes.appointments import appointments_bp
from routes.documents import documents_bp
from routes.invoices import invoices_bp
from routes.reports import reports_bp
from routes.activity_log import activity_log_bp

from activity_logger import init_app as init_activity_logger
from data_manager import init_app as init_data_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # تهيئة قاعدة البيانات
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # تهيئة مكونات النظام
    init_activity_logger(app)
    init_data_manager(app)

    # تسجيل المسارات
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(activity_log_bp)

    @app.route('/')
    def index():
        return render_template('dashboard/index.html')

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
