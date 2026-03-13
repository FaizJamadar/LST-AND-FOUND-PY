from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_found = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Unclaimed')
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    claim_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    contact_info = db.Column(db.String(200))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['role'] == 'staff':
        return redirect(url_for('staff_dashboard'))
    return redirect(url_for('student_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/staff/dashboard')
def staff_dashboard():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    items = Item.query.order_by(Item.date_found.desc()).all()
    claims = db.session.query(Claim, Item, User).join(Item, Claim.item_id == Item.id).join(User, Claim.student_id == User.id).all()
    return render_template('staff_dashboard.html', items=items, claims=claims)

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    items = Item.query.filter_by(status='Unclaimed').order_by(Item.date_found.desc()).all()
    my_claims = db.session.query(Claim, Item).join(Item).filter(Claim.student_id == session['user_id']).all()
    return render_template('student_dashboard.html', items=items, my_claims=my_claims)

@app.route('/staff/add', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        date_found_str = request.form['date_found']
        date_found = datetime.fromisoformat(date_found_str).date()
        new_item = Item(name=name, description=description, location=location, date_found=date_found, reported_by=session['user_id'])
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('staff_dashboard'))
    return render_template('item_form.html', action='Add')

@app.route('/staff/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    item_to_edit = Item.query.get_or_404(id)
    if request.method == 'POST':
        item_to_edit.name = request.form['name']
        item_to_edit.description = request.form['description']
        item_to_edit.location = request.form['location']
        date_found_str = request.form['date_found']
        item_to_edit.date_found = datetime.fromisoformat(date_found_str).date()
        db.session.commit()
        return redirect(url_for('staff_dashboard'))
    return render_template('item_form.html', action='Edit', item=item_to_edit)

@app.route('/staff/delete/<int:id>')
def delete_item(id):
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    item_to_delete = Item.query.get_or_404(id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('staff_dashboard'))

@app.route('/student/claim/<int:id>', methods=['POST'])
def claim_item(id):
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    contact = request.form.get('contact_info')
    new_claim = Claim(item_id=id, student_id=session['user_id'], contact_info=contact, claim_date=datetime.now().date())
    db.session.add(new_claim)
    db.session.commit()
    return redirect(url_for('student_dashboard'))

@app.route('/staff/claim/<int:claim_id>/<action>')
def process_claim(claim_id, action):
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect(url_for('login'))
    claim = Claim.query.get_or_404(claim_id)
    if action == 'approve':
        claim.status = 'Approved'
        Item.query.get(claim.item_id).status = 'Claimed'
    else:
        claim.status = 'Rejected'
    db.session.commit()
    return redirect(url_for('staff_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='staff').first():
            staff = User(username='staff', password=generate_password_hash('staff123'), role='staff', email='staff@college.edu')
            student = User(username='student', password=generate_password_hash('student123'), role='student', email='student@college.edu')
            db.session.add(staff)
            db.session.add(student)
            db.session.commit()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')