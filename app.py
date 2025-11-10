from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_found = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Unclaimed')

    def __repr__(self):
        return f'<Item {self.name}>'

@app.route('/')
def index():
    items = Item.query.order_by(Item.date_found.desc()).all()
    return render_template('index.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        location = request.form['location']
        date_found_str = request.form['date_found']
        date_found = datetime.strptime(date_found_str, '%Y-%m-%d').date()

        new_item = Item(name=name, description=description, location=location, date_found=date_found)
        db.session.add(new_item)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('item_form.html', action='Add')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item_to_edit = Item.query.get_or_404(id)
    
    if request.method == 'POST':
        item_to_edit.name = request.form['name']
        item_to_edit.description = request.form['description']
        item_to_edit.location = request.form['location']
        date_found_str = request.form['date_found']
        item_to_edit.date_found = datetime.strptime(date_found_str, '%Y-%m-%d').date()
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('item_form.html', action='Edit', item=item_to_edit)

@app.route('/delete/<int:id>')
def delete_item(id):
    item_to_delete = Item.query.get_or_404(id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/claim/<int:id>')
def claim_item(id):
    item_to_claim = Item.query.get_or_404(id)
    item_to_claim.status = 'Claimed'
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)