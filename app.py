import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from models import db, User, Vulnerability

# Config paths
basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(basedir, 'templates')
static_dir = os.path.join(basedir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'vulnerabilities.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create tables and default admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

# Flask-Login user loader
class LoginUser(UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.username = user.username
        self.role = user.role

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    return LoginUser(u) if u else None

# Role-required decorator
def role_required(*roles):
    def wrapper(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Accesso negato', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(LoginUser(user))
            return redirect(url_for('index'))
        flash('Credenziali errate', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        if current_user.check_password(request.form['old_password']):
            u = User.query.get(current_user.id)
            u.set_password(request.form['new_password'])
            db.session.commit()
            flash('Password aggiornata', 'success')
            return redirect(url_for('index'))
        flash('Password corrente sbagliata', 'danger')
    return render_template('change_password.html')

@app.route('/')
@login_required
def index():
    vulns = Vulnerability.query.all()
    types = sorted({v.severity for v in vulns if v.severity})
    return render_template('index.html', vulns=vulns, types=types)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'editor']:
        flash('Permessi insufficienti', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        repo = request.form['repo_name']
        title = request.form['title']
        severity = request.form.get('severity', '')
        desc = request.form.get('description', '')
        extras = {}
        for key, val in request.form.items():
            if key.startswith('extra_key_') and val.strip():
                idx = key.split('_')[-1]
                extras[val] = request.form.get(f'extra_val_{idx}', '')
        vuln = Vulnerability(repo_name=repo, title=title, severity=severity, description=desc)
        vuln.set_extra(extras)
        db.session.add(vuln)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('form.html', action='Add', vuln=None)

@app.route('/edit/<int:vuln_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'editor')
def edit(vuln_id):
    vuln = Vulnerability.query.get_or_404(vuln_id)
    if request.method == 'POST':
        vuln.repo_name = request.form['repo_name']
        vuln.title = request.form['title']
        vuln.severity = request.form.get('severity', '')
        vuln.description = request.form.get('description', '')
        extras = {}
        for key, val in request.form.items():
            if key.startswith('extra_key_') and val.strip():
                idx = key.split('_')[-1]
                extras[val] = request.form.get(f'extra_val_{idx}', '')
        vuln.set_extra(extras)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('form.html', action='Edit', vuln=vuln)

@app.route('/delete/<int:vuln_id>', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def delete(vuln_id):
    vuln = Vulnerability.query.get_or_404(vuln_id)
    db.session.delete(vuln)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/duplicate/<int:vuln_id>', methods=['POST'])
@login_required
def duplicate(vuln_id):
    orig = Vulnerability.query.get_or_404(vuln_id)
    dup = Vulnerability(
        repo_name=orig.repo_name,
        title=orig.title + ' (Copy)',
        severity=orig.severity,
        description=orig.description,
        extra=orig.extra
    )
    db.session.add(dup)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)