# -*- coding: utf-8 -*-
"""
Created on Tue Dec 24 16:39:07 2024

@author: r_61
"""
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import xml.etree.ElementTree as ET
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    street = db.Column(db.String(200))
    number = db.Column(db.String(10))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(100))
    birth_date = db.Column(db.String(20))
    illness = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))

class Therapy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    therapy_id = db.Column(db.Integer, db.ForeignKey('therapy.id'), nullable=False)
    date = db.Column(db.String(100))
    description = db.Column(db.Text)
    price_factor = db.Column(db.Float, default=1.0)

# Base HTML template
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        /* Basic styles for the application */
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f9f9f9; }
        header { background-color: #007bff; color: white; padding: 15px; text-align: center; }
        nav { margin: 10px 0; }
        nav button { margin: 0 10px; }
        main { padding: 20px; }
        h1, h2 { color: #333; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 5px 0; }
        form { margin-bottom: 20px; }
        input, select, textarea { width: 100%; padding: 8px; margin: 5px 0; }
        button { background-color: #007bff; color: white; border: none; padding: 10px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        a { text-decoration: none; color: #007bff; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    {% if show_header %}
    <header>
        <h1>Therapy Management System</h1>
        <nav>
            <a href="/dashboard"><button>Dashboard</button></a>
            <a href="/logout"><button>Logout</button></a>
        </nav>
    </header>
    {% endif %}
    <main>
        {{ content|safe }}
    </main>
</body>
</html>
'''

@app.route('/')
def login():
    content = '''
    <h1>Login</h1>
    <form action="/login" method="post">
        <label for="username">Benutzername:</label><br>
        <input type="text" id="username" name="username" required><br><br>
        <label for="password">Passwort:</label><br>
        <input type="password" id="password" name="password" required><br><br>
        <button type="submit">Login</button>
    </form>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{% if show_header %}", "").replace("{% endif %}", "")

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form['username']
    password = request.form['password']
    if username == 'Elvan' and password == 'ElvanMuhammed':
        session['user'] = username
        return redirect('/dashboard')
    return 'Invalid credentials!'

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    
    content = '''
    <h1>Dashboard</h1>
    <nav>
        <button onclick="window.location.href='/customers';">Kunden Anlegen</button>
        <button onclick="window.location.href='/therapies';">Vorgang Definieren</button>
        <button onclick="window.location.href='/treatments';">Behandlung</button>
    </nav>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{% if show_header %}", "true").replace("{{ user }}", session['user'])

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if 'user' not in session:
        return redirect('/')
    
    search_query = request.args.get('search', '')
    customers = Customer.query.filter(
        Customer.first_name.contains(search_query) | Customer.last_name.contains(search_query)
    ).all()
    
    customer_list = ''.join([
        f'<li><a href="/treatments/{customer.id}">{customer.first_name} {customer.last_name} - {customer.street} {customer.number}, {customer.postal_code} {customer.city} - {customer.illness} - {customer.phone} - {customer.email}</a> | <a href="/edit_customer/{customer.id}">Bearbeiten</a></li>'
        for customer in customers
    ])
    
    content = f'''
    <h1>Kunden</h1>
    <form action="/customers" method="get">
        <input type="text" name="search" placeholder="Suche nach Kunden..." value="{search_query}">
        <button type="submit">Suchen</button>
    </form>
    <h2>Liste der Kunden</h2>
    <ul>
        {customer_list}
    </ul>
    <button onclick="window.location.href='/add_customer';">Neuen Kunden anlegen</button>
    <button onclick="window.location.href='/dashboard';">Zurück</button>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{{ user }}", session['user'])

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if 'user' not in session:
        return redirect('/')
    
    if request.method == 'POST':
        new_customer = Customer(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            street=request.form['street'],
            number=request.form['number'],
            postal_code=request.form['postal_code'],
            city=request.form['city'],
            birth_date=request.form['birth_date'],
            illness=', '.join(request.form.getlist('illnesses')),
            phone=request.form['phone'],
            email=request.form['email']
        )
        db.session.add(new_customer)
        db.session.commit()
        return redirect('/customers')
    
    content = '''
    <h1>Kunden Anlegen</h1>
    <form action="/add_customer" method="post">
        <label for="first_name">Vorname:</label><br>
        <input type="text" id="first_name" name="first_name" required><br>
        <label for="last_name">Nachname:</label><br>
        <input type="text" id="last_name" name="last_name" required><br>
        <label for="street">Straße:</label><br>
        <input type="text" id="street" name="street"><br>
        <label for="number">Nummer:</label><br>
        <input type="text" id="number" name="number"><br>
        <label for="postal_code">PLZ:</label><br>
        <input type="text" id="postal_code" name="postal_code"><br>
        <label for="city">Ort:</label><br>
        <input type="text" id="city" name="city"><br>
        <label for="birth_date">Geburtsdatum:</label><br>
        <input type="text" id="birth_date" name="birth_date"><br>
        <label>Krankheiten:</label><br>
        <input type="checkbox" name="illnesses" value="Krankheit 1"> Krankheit 1<br>
        <input type="checkbox" name="illnesses" value="Krankheit 2"> Krankheit 2<br>
        <input type="checkbox" name="illnesses" value="Krankheit 3"> Krankheit 3<br>
        <label for="phone">Telefon:</label><br>
        <input type="text" id="phone" name="phone"><br>
        <label for="email">E-Mail:</label><br>
        <input type="email" id="email" name="email"><br>
        <button type="submit">Kunden Anlegen</button>
    </form>
    <button onclick="window.location.href='/customers';">Zurück</button>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{{ user }}", session['user'])

@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    if 'user' not in session:
        return redirect('/')
    
    customer = Customer.query.get(customer_id)
    
    if customer is None:
        return 'Kunde nicht gefunden!', 404
    
    if request.method == 'POST':
        customer.first_name = request.form['first_name']
        customer.last_name = request.form['last_name']
        customer.street = request.form['street']
        customer.number = request.form['number']
        customer.postal_code = request.form['postal_code']
        customer.city = request.form['city']
        customer.birth_date = request.form['birth_date']
        customer.illness = ', '.join(request.form.getlist('illnesses'))
        customer.phone = request.form['phone']
        customer.email = request.form['email']
        db.session.commit()
        return redirect('/customers')

    content = f'''
    <h1>Kunden Bearbeiten</h1>
    <form action="/edit_customer/{customer_id}" method="post">
        <label for="first_name">Vorname:</label><br>
        <input type="text" id="first_name" name="first_name" value="{customer.first_name}" required><br>
        <label for="last_name">Nachname:</label><br>
        <input type="text" id="last_name" name="last_name" value="{customer.last_name}" required><br>
        <label for="street">Straße:</label><br>
        <input type="text" id="street" name="street" value="{customer.street}"><br>
        <label for="number">Nummer:</label><br>
        <input type="text" id="number" name="number" value="{customer.number}"><br>
        <label for="postal_code">PLZ:</label><br>
        <input type="text" id="postal_code" name="postal_code" value="{customer.postal_code}"><br>
        <label for="city">Ort:</label><br>
        <input type="text" id="city" name="city" value="{customer.city}"><br>
        <label for="birth_date">Geburtsdatum:</label><br>
        <input type="text" id="birth_date" name="birth_date" value="{customer.birth_date}"><br>
        <label>Krankheiten:</label><br>
        <input type="checkbox" name="illnesses" value="Krankheit 1" {'checked' if 'Krankheit 1' in customer.illness else ''}> Krankheit 1<br>
        <input type="checkbox" name="illnesses" value="Krankheit 2" {'checked' if 'Krankheit 2' in customer.illness else ''}> Krankheit 2<br>
        <input type="checkbox" name="illnesses" value="Krankheit 3" {'checked' if 'Krankheit 3' in customer.illness else ''}> Krankheit 3<br>
        <label for="phone">Telefon:</label><br>
        <input type="text" id="phone" name="phone" value="{customer.phone}"><br>
        <label for="email">E-Mail:</label><br>
        <input type="email" id="email" name="email" value="{customer.email}"><br>
        <button type="submit">Kunden Aktualisieren</button>
    </form>
    <button onclick="window.location.href='/customers';">Zurück</button>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{{ user }}", session['user'])

@app.route('/therapies', methods=['GET', 'POST'])
def therapies():
    if 'user' not in session:
        return redirect('/')
    
    if request.method == 'POST':
        new_therapy = Therapy(
            name=request.form['name'],
            price=request.form['price']
        )
        db.session.add(new_therapy)
        db.session.commit()
        return redirect('/therapies')
    
    therapies = Therapy.query.all()
    therapy_list = ''.join([f'<li>{therapy.name} - {therapy.price:.2f} €</li>' for therapy in therapies])
    
    content = f'''
    <h1>Therapien</h1>
    <form action="/therapies" method="post">
        <label for="name">Therapie:</label><br>
        <input type="text" id="name" name="name" required><br>
        <label for="price">Preis:</label><br>
        <input type="number" step="0.01" id="price" name="price" required><br>
        <button type="submit">Therapie hinzufügen</button>
    </form>
    <h2>Liste der Therapien</h2>
    <ul>
        {therapy_list}
    </ul>
    <button onclick="window.location.href='/dashboard';">Zurück</button>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{{ user }}", session['user'])

@app.route('/treatments/<int:customer_id>', methods=['GET', 'POST'])
def treatments(customer_id):
    if 'user' not in session:
        return redirect('/')
    
    customer = Customer.query.get(customer_id)
    if customer is None:
        return 'Kunde nicht gefunden!', 404
    
    therapies = Therapy.query.all()
    
    if request.method == 'POST':
        new_treatment = Treatment(
            customer_id=customer_id,
            therapy_id=request.form['therapy_id'],
            date=request.form['date'],
            description=request.form['description'],
            price_factor=request.form['price_factor']
        )
        db.session.add(new_treatment)
        db.session.commit()
        return redirect(f'/treatments/{customer_id}')
    
    treatments = Treatment.query.filter_by(customer_id=customer_id).all()
    treatment_list = ''.join([
        f'<li><a href="/treatment_detail/{treatment.id}">Therapie: {treatment.therapy_id} - Datum: {treatment.date} - Beschreibung: {treatment.description} - Preis: {treatment.price_factor * Therapy.query.get(treatment.therapy_id).price:.2f} €</a></li>'
        for treatment in treatments
    ])
    
    therapy_options = ''.join([f'<option value="{therapy.id}">{therapy.name}</option>' for therapy in therapies])
    
    content = f'''
    <h1>Behandlungen für {customer.first_name} {customer.last_name}</h1>
    <form action="/treatments/{customer_id}" method="post">
        <label for="therapy_id">Therapie:</label><br>
        <select id="therapy_id" name="therapy_id">{therapy_options}</select><br>
        <label for="date">Datum:</label><br>
        <input type="text" id="date" name="date" required><br>
        <label for="description">Behandlung Beschreibung:</label><br>
        <textarea id="description" name="description" required></textarea><br>
        <label for="price_factor">Preis Faktor:</label><br>
        <input type="number" step="0.1" id="price_factor" name="price_factor" value="1.0"><br>
        <button type="submit">Behandlung hinzufügen</button>
    </form>
    
    <h2>Liste der Behandlungen</h2>
    <ul>{treatment_list}</ul>
    
    <h2>Behandlungsverlauf Exportieren</h2>
    <form action="/export_treatments/{customer_id}" method="post">
        <label for="start_date">Startdatum:</label><br>
        <input type="date" id="start_date" name="start_date" required><br>
        <label for="end_date">Enddatum:</label><br>
        <input type="date" id="end_date" name="end_date" required><br>
        <button type="submit">Exportieren als XML</button>
        <button formaction="/export_treatments_pdf/{customer_id}" method="post">Exportieren als PDF</button>
    </form>
    
    <button onclick="window.location.href='/customers';">Zurück</button>
    '''
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{{ user }}", session['user'])

@app.route('/treatment_detail/<int:treatment_id>', methods=['GET'])
def treatment_detail(treatment_id):
    if 'user' not in session:
        return redirect('/')

    treatment = Treatment.query.get(treatment_id)
    if treatment is None:
        return 'Behandlung nicht gefunden!', 404
    
    therapy = Therapy.query.get(treatment.therapy_id)
    
    content = f'''
    <h1>Behandlungsdetails</h1>
    <p><strong>Therapie:</strong> {therapy.name}</p>
    <p><strong>Datum:</strong> {treatment.date}</p>
    <p><strong>Beschreibung:</strong> {treatment.description}</p>
    <p><strong>Preis:</strong> {treatment.price_factor * therapy.price:.2f} €</p>
    <button onclick="window.location.href='/treatments/{treatment.customer_id}';">Zurück</button>
    '''
    
    return BASE_TEMPLATE.replace("{{ content|safe }}", content).replace("{{ user }}", session['user'])

@app.route('/export_treatments/<int:customer_id>', methods=['POST'])
def export_treatments(customer_id):
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    start_date_str = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
    end_date_str = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    treatments = Treatment.query.filter(
        Treatment.customer_id == customer_id,
        Treatment.date >= start_date_str,
        Treatment.date <= end_date_str
    ).all()

    root = ET.Element("Treatments")
    for treatment in treatments:
        therapy = Therapy.query.get(treatment.therapy_id)
        treatment_elem = ET.SubElement(root, "Treatment")
        ET.SubElement(treatment_elem, "Date").text = treatment.date
        ET.SubElement(treatment_elem, "Description").text = treatment.description
        ET.SubElement(treatment_elem, "Price").text = str(treatment.price_factor * therapy.price)

    xml_file = f"treatments_{customer_id}.xml"
    tree = ET.ElementTree(root)
    tree.write(xml_file)

    return send_file(xml_file, as_attachment=True)

@app.route('/export_treatments_pdf/<int:customer_id>', methods=['POST'])
def export_treatments_pdf(customer_id):
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    start_date_str = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
    end_date_str = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')

    treatments = Treatment.query.filter(
        Treatment.customer_id == customer_id,
        Treatment.date >= start_date_str,
        Treatment.date <= end_date_str
    ).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Behandlungsverlauf für Kunde ID {customer_id}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Von: {start_date} Bis: {end_date}", ln=True, align='C')
    pdf.cell(200, 10, txt='', ln=True)

    for treatment in treatments:
        therapy = Therapy.query.get(treatment.therapy_id)
        pdf.cell(200, 10, txt=f'Datum: {treatment.date}, Therapie: {therapy.name}, Beschreibung: {treatment.description}, Preis: {treatment.price_factor * therapy.price:.2f} €', ln=True)

    pdf_file = f"treatments_{customer_id}.pdf"
    pdf.output(pdf_file)

    return send_file(pdf_file, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/create_db')
def create_db():
    db.create_all()
    return 'Database created!'

@app.route('/drop_db')
def drop_db():
    db.drop_all()
    return 'Database dropped! You can recreate it using /create_db.'

@app.route('/register')
def register():
    return 'Registration Page (not implemented)'

@app.route('/password_recovery')
def password_recovery():
    return 'Password Recovery Page (not implemented)'

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
    app.run(debug=True)
