import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from models import db, User, Vulnerability

# Config paths
basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(basedir, 'templates')
static_dir = os.path.join(basedir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'vulnerabilities.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home'

# In-memory storage for text assigned to each user on the SAL page
assigned_texts = {}

# Create tables and default admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
        admin.set_password(admin_password)
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
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(LoginUser(user))
            return redirect(url_for('wapt_editor'))
        flash('Credenziali errate', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        if user and user.check_password(request.form['old_password']):
            user.set_password(request.form['new_password'])
            db.session.commit()
            flash('Password aggiornata', 'success')
            return redirect(url_for('wapt_editor'))
        flash('Password corrente sbagliata', 'danger')
    return render_template('change_password.html')

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username già esistente', 'danger')
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Utente creato', 'success')
            return redirect(url_for('wapt_editor'))
    return render_template('add_user.html')

@app.route('/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def users():
    show_user_id = None
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        admin = User.query.get(current_user.id)
        if admin and admin.check_password(request.form.get('admin_password', '')):
            show_user_id = int(user_id or 0)
        else:
            flash('Password amministratore non valida', 'danger')
    all_users = User.query.all()
    return render_template('users.html', users=all_users,
                           show_user_id=show_user_id)

@app.route('/')
def root():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/wapt_editor')
@login_required
def wapt_editor():
    vulns = Vulnerability.query.all()
    types = sorted({v.severity for v in vulns if v.severity})
    return render_template('index.html', vulns=vulns, types=types)

@app.route('/sal', methods=['GET', 'POST'])
def sal():
    users = User.query.all()
    if request.method == 'POST':
        user_id = int(request.form.get('user_id', 0))
        text = request.form.get('text', '')
        if user_id:
            assigned_texts[user_id] = text
    return render_template('sal.html', users=users, assignments=assigned_texts,
                           users_map={u.id: u for u in users})

@app.route('/generate_eml', methods=['POST'])
def generate_eml():
    import io, zipfile
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        for uid, text in assigned_texts.items():
            user = User.query.get(uid)
            if user:
                zf.writestr(f"{user.username}.eml", f"{user.username}\n\n{text}")
    mem.seek(0)
    return send_file(mem, download_name='emails.zip', as_attachment=True)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'editor']:
        flash('Permessi insufficienti', 'danger')
        return redirect(url_for('wapt_editor'))
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
        return redirect(url_for('wapt_editor'))
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
        return redirect(url_for('wapt_editor'))
    return render_template('form.html', action='Edit', vuln=vuln)

@app.route('/delete/<int:vuln_id>', methods=['POST'])
@login_required
@role_required('admin', 'editor')
def delete(vuln_id):
    vuln = Vulnerability.query.get_or_404(vuln_id)
    db.session.delete(vuln)
    db.session.commit()
    return redirect(url_for('home'))

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
    return redirect(url_for('wapt_editor'))

if __name__ == '__main__':
    app.run(debug=True)