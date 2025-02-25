from flask import Flask, request, render_template, flash, session, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime, timedelta
import json
import hashlib

app = Flask(__name__)
app.secret_key = 'allen'

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='project',
)

@app.template_filter()
def check_if_purchased(customer_email, flight_num):
    # Assuming you have a database connection established
    cursor = conn.cursor()
    customer_email = session.get('username')
    query = """
    SELECT count(1)
    FROM purchase p
    JOIN ticket t ON p.ticket_id = t.ticket_id
    WHERE p.customer_email = %s AND t.flight_num = %s
    """
    cursor.execute(query, (customer_email, flight_num))
    result = cursor.fetchone()
    cursor.close()
    return result[0] > 0

@app.template_filter()
def check_if_full(flight_num):
    # Assuming you have a database connection established
    cursor = conn.cursor()
    query = f"""
    SELECT COUNT(t.ticket_id), a.seat
    FROM ticket t
    JOIN flight f ON t.flight_num = f.flight_num
    JOIN airplane a ON a.id = f.plane_id
    WHERE f.flight_num = '{flight_num}'
    """
    cursor.execute(query)
    result = cursor.fetchone()
    print(result)
    cursor.close()
    return result[0] >= result[1]

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/public_upcoming_flights')
def public_upcoming_flights():
    cursor = conn.cursor()
    query = "SELECT * FROM flight WHERE status = 'upcoming'"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = "SELECT DISTINCT depart_airport, arrive_airport FROM flight WHERE status = 'upcoming'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('public_upcoming_flights.html', flights=flights, airports=airports)

@app.route('/search_public_upcoming_flights', methods=['POST'])
def search_public_upcoming_flights():
    departure_airport = request.form.get('departure_airport')
    departure_time = request.form.get('departure_time')
    arrival_airport = request.form.get('arrival_airport')
    query = "SELECT * FROM flight WHERE 1=1"
    if departure_airport:
        query += f" AND depart_airport = '{departure_airport}'"
    if departure_time:
        query += f" AND depart_time LIKE '%{departure_time}%'"
    if arrival_airport:
        query += f" AND arrive_airport = '{arrival_airport}'"
    query += " AND status = 'upcoming'"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = "SELECT DISTINCT depart_airport, arrive_airport FROM flight WHERE status = 'upcoming'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('public_upcoming_flights.html', flights=flights, airports=airports)

@app.route('/public_flights_status')
def public_flights_status():
    cursor = conn.cursor()
    query = "SELECT * FROM flight"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    return render_template('public_flights_status.html', flights=flights)

@app.route('/search_public_flights_status', methods=['POST'])
def search_public_flights_status():
    flight_number = request.form.get('flight_number')
    departure_time = request.form.get('departure_time')
    arrival_time = request.form.get('arrival_time')
    query = "SELECT * FROM flight WHERE 1=1"
    if flight_number:
        query += f" AND flight_num LIKE '%{flight_number}%'"
    if departure_time:
        query += f" AND depart_time LIKE '%{departure_time}%'"
    if arrival_time:
        query += f" AND arrive_time LIKE '%{arrival_time}%'"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    return render_template('public_flights_status.html', flights=flights)

@app.route('/register_page')
def register_page():
	return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    role = request.form.get('role')
    if role == "customer":
        password = request.form.get('customer_password')
        password_confirm = request.form.get('customer_password_confirm')
        print(password)
        if password != password_confirm:
            return render_template('register.html',message='Passwords do not match. Please try again.')
        password = hashlib.md5(password.encode()).hexdigest()
        data = (
            request.form.get('customer_email'),
            request.form.get('customer_name'),
            password,
            request.form.get('building_number'),
            request.form.get('street'),
            request.form.get('city'),
            request.form.get('state'),
            request.form.get('phone_number'),
            request.form.get('passport_number'),
            request.form.get('passport_expiration'),
            request.form.get('passport_country'),
            request.form.get('customer_date_of_birth')
        )
        query = '''
        INSERT INTO customer 
        (email, name, password, building_number, street, city, state, phone_number, passport_number, passport_expiration, passport_country, date_of_birth) 
        VALUES ( %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s)
        '''
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()
        flash('Registration successful!')
        cursor.close()
        return render_template('index.html', message='Registration successful!')
    
    elif role == 'agent':
        password = request.form.get('agent_password')
        password_confirm = request.form.get('agent_password_confirm')
        print(password)
        if password != password_confirm:
            return render_template('register.html',message='Passwords do not match. Please try again.')
        password = hashlib.md5(password.encode()).hexdigest()
        cursor = conn.cursor()
        query = 'SELECT MAX(booking_agent_id) FROM agent'
        cursor.execute(query)
        agent_id = cursor.fetchone()
        data = (
            request.form.get('agent_email'),
            password,
            int(agent_id[0]) + 1
        )
        query = 'INSERT INTO agent (email, password, booking_agent_id) VALUES (%s, %s, %s)'
        cursor.execute(query, data)
        conn.commit()
        cursor.close()
        return render_template('index.html', message='Registration successful!')

    elif role == 'staff':
        password = request.form.get('staff_password')
        password_confirm = request.form.get('staff_password_confirm')
        print(password)
        if password != password_confirm:
            return render_template('register.html',message='Passwords do not match. Please try again.')
        password = hashlib.md5(password.encode()).hexdigest()
        data = (
            request.form.get('staff_username'),
            password,
            request.form.get('first_name'),
            request.form.get('last_name'),
            request.form.get('staff_date_of_birth'),
            0,
            request.form.get('name_airline')
        )
        query = '''
        INSERT INTO airline_staff 
        (email, password, first_name, last_name, date_of_birth, permission_id, name_airline) 
        VALUES ( %s,  %s,  %s,  %s,  %s,  %s,  %s)
        '''
        cursor = conn.cursor()
        cursor.execute(query, data)
        conn.commit()
        flash('Registration successful!')
        cursor.close()
        return render_template('index.html', message='Registration successful!')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password = hashlib.md5(password.encode()).hexdigest()
        cursor = conn.cursor()
        for role in ['customer', 'agent', 'airline_staff']:
            if role == 'customer':
                name_column = 'name'
                query = f"SELECT email, password, {name_column} FROM {role} WHERE email = '{username}'"
            elif role == 'agent':
                name_column = 'booking_agent_id'
                query = f"SELECT email, password, {name_column} FROM {role} WHERE email = '{username}'"
            elif role == 'airline_staff':
                name_column = 'last_name'
                query = f"SELECT email, password, {name_column}, permission_id, name_airline FROM {role} WHERE email = '{username}'"
            cursor.execute(query)
            user = cursor.fetchone()
            if user:
                # User exists, check password
                if user[1] == password:
                    session['username'] = user[0]
                    session['name'] = user[2]
                    session['role'] = role
                    if role == 'airline_staff':
                        session['permission'] = user[3]
                        session['airline'] = user[4]
                    # Redirect to the homepage based on the user's role
                    cursor.close()
                    return redirect(f'/{role}_home')
                else:
                    cursor.close()
                    return render_template('index.html', message='Wrong Password!')
        else:
            # No user found in any table
            cursor.close()
            return render_template('index.html', message='User Not Exist!')

@app.route('/customer_home')
def customer_home():
    if session.get('role') != 'customer':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    customer_name = session.get('name')
    customer_email = session.get('username')
    cursor = conn.cursor()
    query = f"SELECT f.* FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.customer_email = '{customer_email}' AND f.status = 'upcoming'"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT f.depart_airport, f.arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.customer_email = '{customer_email}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('customer_homepage.html',customer_name = customer_name, flights = flights, airports = airports)

@app.route('/search_customer_home', methods=['POST'])
def search_customer_home():
    if session.get('role') != 'customer':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    departure_airport = request.form.get('departure_airport')
    departure_time = request.form.get('departure_time')
    arrival_airport = request.form.get('arrival_airport')
    customer_name = session.get('name')
    customer_email = session.get('username')
    query = "SELECT f.* FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE 1=1"
    if departure_airport:
        query += f" AND depart_airport = '{departure_airport}'"
    if departure_time:
        query += f" AND depart_time LIKE '%{departure_time}%'"
    if arrival_airport:
        query += f" AND arrive_airport = '{arrival_airport}'"
    query += f" AND p.customer_email = '{customer_email}'"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT f.depart_airport, f.arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.customer_email = '{customer_email}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('customer_homepage.html', customer_name = customer_name, flights=flights, airports=airports)

@app.route('/customer_purchase')
def customer_purchase():
    if session.get('role') != 'customer':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    customer_name = session.get('name')
    cursor = conn.cursor()
    query = "SELECT * FROM flight WHERE status = 'upcoming'"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = "SELECT DISTINCT depart_airport, arrive_airport FROM flight WHERE status = 'upcoming'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('customer_purchase.html', customer_name = customer_name, flights=flights, airports=airports)

@app.route('/search_customer_purchase', methods=['POST'])
def search_customer_purchase():
    if session.get('role') != 'customer':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    customer_name = session.get('name')
    departure_airport = request.form.get('departure_airport')
    departure_time = request.form.get('departure_time')
    arrival_airport = request.form.get('arrival_airport')
    query = "SELECT * FROM flight WHERE 1=1"
    if departure_airport:
        query += f" AND depart_airport = '{departure_airport}'"
    if departure_time:
        query += f" AND depart_time LIKE '%{departure_time}%'"
    if arrival_airport:
        query += f" AND arrive_airport = '{arrival_airport}'"
    query += f" AND status = 'upcoming'"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight WHERE status = 'upcoming'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('customer_purchase.html', customer_name = customer_name, flights=flights, airports=airports)

@app.route('/customer_purchase_ticket', methods=['POST'])
def purchase_ticket():
    data = request.get_json()
    flight_number = data['flight_number']
    customer_email = session.get('username')  # Assuming customer is logged in and you have their email
    purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(ticket_id) FROM ticket')
    max_id_result = cursor.fetchone()[0]
    ticket_id = int(max_id_result) + 1
    cursor.execute('INSERT INTO ticket (ticket_id, flight_num) VALUES (%s, %s)', (ticket_id, flight_number))
    cursor.execute('INSERT INTO purchase (ticket_id, customer_email, agent_email, date) VALUES (%s, %s, NULL, %s)', (ticket_id, customer_email, purchase_date))
    conn.commit()
    cursor.close()
    return jsonify({'success': True})

@app.route('/customer_spending', methods=['GET', 'POST'])
def customer_spending():
    if session.get('role') != 'customer':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    customer_email = session.get('username')
    cursor = conn.cursor()
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not start_date and not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    query = """
    SELECT DATE_FORMAT(date, '%Y-%m') as month, SUM(flight.price) as total_spent
    FROM purchase
    JOIN ticket ON purchase.ticket_id = ticket.ticket_id
    JOIN flight ON ticket.flight_num = flight.flight_num
    WHERE purchase.customer_email = %s AND purchase.date BETWEEN %s AND %s
    GROUP BY DATE_FORMAT(date, '%Y-%m')
    ORDER BY month
    """
    cursor.execute(query, (customer_email, start_date, end_date))
    results = cursor.fetchall()
    # Prepare data for the bar chart
    months = [result[0] for result in results]
    spending = [float(result[1]) for result in results]
    total_spent = sum(spending)

    chart_data = {
        'labels': months,
        'datasets': [{
            'label': 'Spending Over Time',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'data': spending
        }]
    }
    cursor.close()
    return render_template('customer_spending.html', total_spent=total_spent, chart_data=json.dumps(chart_data))

@app.route('/agent_home')
def agent_home():
    if session.get('role') != 'agent':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    agent_name = session.get('name')
    agent_email = session.get('username')
    cursor = conn.cursor()
    query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.agent_email = '{agent_email}' AND f.status = 'upcoming'"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.agent_email = '{agent_email}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('agent_homepage.html',agent_name = agent_name, flights = flights, airports = airports)

@app.route('/search_agent_home', methods=['POST'])
def search_agent_home():
    if session.get('role') != 'agent':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    departure_airport = request.form.get('departure_airport')
    departure_time = request.form.get('departure_time')
    arrival_airport = request.form.get('arrival_airport')
    agent_name = session.get('name')
    agent_email = session.get('username')
    query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.agent_email = '{agent_email}'"
    if departure_airport:
        query += f" AND depart_airport = '{departure_airport}'"
    if departure_time:
        query += f" AND depart_time LIKE '%{departure_time}%'"
    if arrival_airport:
        query += f" AND arrive_airport = '{arrival_airport}'"
    query += f" AND p.agent_email = '{agent_email}'"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.agent_email = '{agent_email}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('agent_homepage.html', agent_name = agent_name, flights=flights, airports=airports)

@app.route('/agent_purchase')
def agent_purchase():
    if session.get('role') != 'agent':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    agent_name = session.get('booking_agent_id')
    agent_email = session.get('username')
    cursor = conn.cursor()
    query = f"SELECT airline_name FROM works_for WHERE agent_email = '{agent_email}'"
    cursor.execute(query)
    agent_airline = cursor.fetchone()[0]
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT f.* FROM flight f WHERE f.name_airline = '{agent_airline}' AND f.status = 'upcoming'"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f WHERE f.status = 'upcoming' AND f.name_airline = '{agent_airline}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('agent_purchase.html', agent_name = agent_name, flights=flights, airports=airports)

@app.route('/search_agent_purchase', methods=['POST'])
def search_agent_purchase():
    if session.get('role') != 'agent':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    agent_email = session.get('username')
    agent_name = session.get('booking_agent_id')
    departure_airport = request.form.get('departure_airport')
    departure_time = request.form.get('departure_time')
    arrival_airport = request.form.get('arrival_airport')
    cursor = conn.cursor()
    query = f"SELECT airline_name FROM works_for WHERE agent_email = '{agent_email}'"
    cursor.execute(query)
    agent_airline = cursor.fetchone()[0]
    cursor.close()
    query = "SELECT * FROM flight WHERE 1=1"
    if departure_airport:
        query += f" AND depart_airport = '{departure_airport}'"
    if departure_time:
        query += f" AND depart_time LIKE '%{departure_time}%'"
    if arrival_airport:
        query += f" AND arrive_airport = '{arrival_airport}'"
    query += f" AND status = 'upcoming' AND name_airline = '{agent_airline}'"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight WHERE status = 'upcoming' AND name_airline = '{agent_airline}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('agent_purchase.html', agent_name = agent_name, flights=flights, airports=airports)

@app.route('/agent_search_emails')
def agent_search_emails():
    if request.args.get('email'):
        email = f"%{request.args.get('email')}%"
        flightNum = f"{request.args.get('flightNum')}"
        query = """
        SELECT c.email FROM customer c
        WHERE c.email LIKE %s AND NOT EXISTS (
            SELECT 1 FROM purchase p
            JOIN ticket t ON p.ticket_id = t.ticket_id
            WHERE p.customer_email = c.email AND t.flight_num = %s
        )
        """
        cursor = conn.cursor()
        cursor.execute(query, (email, flightNum))
        emails = cursor.fetchall()
        cursor.close()
        return jsonify([email[0] for email in emails])
    else:
        return jsonify([])

@app.route('/agent_check_purchase')
def agent_check_purchase():
    email = request.args.get('email')
    flight_num = request.args.get('flightNum')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM purchase p NATURAL JOIN ticket t WHERE p.customer_email = %s AND t.flight_num = %s", (email, flight_num))
    count = cursor.fetchone()[0]
    cursor.close()
    return jsonify({'exists': count > 0})

@app.route('/agent_make_purchase', methods=['POST'])
def agent_make_purchase():
    data = request.get_json()
    agent_email = session.get('username')
    email = data['customer_email']
    flight_num = data['flight_num']
    purchase_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(ticket_id) FROM ticket')
    max_id_result = cursor.fetchone()[0]
    ticket_id = int(max_id_result) + 1
    cursor.execute('INSERT INTO ticket (ticket_id, flight_num) VALUES (%s, %s)', (ticket_id, flight_num))
    cursor.execute('INSERT INTO purchase (ticket_id, customer_email, agent_email, date) VALUES (%s, %s, %s, %s)', (ticket_id, email, agent_email, purchase_date))
    conn.commit()
    cursor.close()
    return jsonify({'success': cursor.rowcount > 0})

@app.route('/agent_commission', methods=['GET', 'POST'])
def agent_commission():
    if session.get('role') != 'agent':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    agent_email = session.get('username')
    cursor = conn.cursor()
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not start_date and not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    query = """
    SELECT SUM(flight.price), AVG(flight.price), COUNT(ticket.ticket_id) as total_commission
    FROM purchase
    JOIN ticket ON purchase.ticket_id = ticket.ticket_id
    JOIN flight ON ticket.flight_num = flight.flight_num
    WHERE purchase.agent_email = %s AND purchase.date BETWEEN %s AND %s
    """
    cursor.execute(query, (agent_email, start_date, end_date))
    results = cursor.fetchone()
    # Prepare data for the bar chart
    total_commission = results[0]
    average_commission = results[1]
    total_ticket = results[2]
    cursor.close()
    return render_template('agent_commission.html', total_commission=total_commission, average_commission=average_commission, total_ticket=total_ticket)

@app.route('/agent_customer', methods=['GET', 'POST'])
def agent_customer():
    if session.get('role') != 'agent':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    agent_email = session.get('username')
    cursor = conn.cursor()
    if request.method == 'POST':
        start_date1 = request.form.get('start_date1')
        end_date1 = request.form.get('end_date1')
        start_date2 = request.form.get('start_date2')
        end_date2 = request.form.get('end_date2')
    else:
        end_date1 = datetime.now().strftime('%Y-%m-%d')
        start_date1 = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date2 = datetime.now().strftime('%Y-%m-%d')
        start_date2 = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not start_date1 and not end_date1:
        end_date1 = datetime.now().strftime('%Y-%m-%d')
        start_date1 = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date1:
        end_date1 = datetime.now().strftime('%Y-%m-%d')
    if not start_date2 and not end_date2:
        end_date2 = datetime.now().strftime('%Y-%m-%d')
        start_date2 = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if not end_date2:
        end_date2 = datetime.now().strftime('%Y-%m-%d')
    query1 = """
    SELECT purchase.customer_email, COUNT(ticket.ticket_id) as total_ticket
    FROM purchase
    JOIN ticket ON purchase.ticket_id = ticket.ticket_id
    JOIN flight ON ticket.flight_num = flight.flight_num
    WHERE purchase.agent_email = %s AND purchase.date BETWEEN %s AND %s
    GROUP BY purchase.customer_email
    ORDER BY total_ticket DESC LIMIT 5
    """
    cursor.execute(query1, (agent_email, start_date1, end_date1))
    results = cursor.fetchall()
    # Prepare data for the bar chart
    customer = [result[0] for result in results]
    total_ticket = [result[1] for result in results]

    chart_data1 = {
        'labels': customer,
        'datasets': [{
            'label': 'Tickets Over Time',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'data': total_ticket
        }]
    }
    query2 = """
    SELECT purchase.customer_email, SUM(flight.price) as total_commission
    FROM purchase
    JOIN ticket ON purchase.ticket_id = ticket.ticket_id
    JOIN flight ON ticket.flight_num = flight.flight_num
    WHERE purchase.agent_email = %s AND purchase.date BETWEEN %s AND %s
    GROUP BY purchase.customer_email
    ORDER BY total_commission DESC LIMIT 5
    """
    cursor.execute(query2, (agent_email, start_date2, end_date2))
    results = cursor.fetchall()
    # Prepare data for the bar chart
    customer = [result[0] for result in results]
    total_commission = [result[1] for result in results]

    chart_data2 = {
        'labels': customer,
        'datasets': [{
            'label': 'Commission Over Time',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'data': total_commission
        }]
    }
    cursor.close()
    return render_template('agent_customer.html', chart_data1=json.dumps(chart_data1), chart_data2=json.dumps(chart_data2))

@app.route('/airline_staff_home')
def staff_home():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    staff_name = session.get('name')
    staff_airline = session.get('airline')
    today = datetime.now().date()
    date_30_days_later = today + timedelta(days=30)
    cursor = conn.cursor()
    query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}' ORDER BY f.flight_num"
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports)

@app.route('/search_staff_home', methods=['POST'])
def search_staff_home():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    departure_airport = request.form.get('departure_airport')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    arrival_airport = request.form.get('arrival_airport')
    staff_name = session.get('name')
    staff_airline = session.get('airline')
    query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
    if departure_airport:
        query += f" AND depart_airport = '{departure_airport}'"
    if start_date:
        query += f" AND depart_time >= '{start_date}'"
    if end_date:
        query += f" AND depart_time <= '{end_date}'"
    if arrival_airport:
        query += f" AND arrive_airport = '{arrival_airport}'"
    query += " ORDER BY f.flight_num"
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    return render_template('staff_homepage.html', staff_name = staff_name, flights=flights, airports=airports)

@app.route('/to_staff_create')
def to_staff_create():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    permission = session.get('permission')
    name_airline = session.get('airline')
    if permission > 1:
        cursor = conn.cursor()
        query = f"SELECT name FROM airport"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT id FROM airplane WHERE name_airline = '{name_airline}'"
        cursor.execute(query)
        planes = cursor.fetchall()
        cursor.close()
        return render_template('staff_create.html', airports = airports, planes = planes)
    else:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        today = datetime.now().date()
        date_30_days_later = today + timedelta(days=30)
        cursor = conn.cursor()
        query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
        cursor.execute(query)
        flights = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports, message = 'You Have No Permission!')

@app.route('/staff_create', methods=['GET', 'POST'])
def staff_create():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    name_airline = session.get('airline')
    cursor = conn.cursor()
    query = f"SELECT name FROM airport"
    cursor.execute(query)
    airports = cursor.fetchall()
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT id FROM airplane WHERE name_airline = '{name_airline}'"
    cursor.execute(query)
    planes = cursor.fetchall()
    cursor.close()
    query = "SELECT flight_num FROM flight"
    cursor = conn.cursor()
    cursor.execute(query)
    flight_numbers = cursor.fetchall()
    if request.form.get('flight_num') in flight_numbers:
        return render_template('staff_create.html', message='Fail!',airports = airports, planes = planes)
    data = (
        request.form.get('flight_num'),
        request.form.get('depart_time'),
        request.form.get('arrive_time'),
        request.form.get('price'),
        request.form.get('status'),
        name_airline,
        request.form.get('plane_id'),
        request.form.get('depart_airport'),
        request.form.get('arrive_airport'),
    )
    query = '''
    INSERT INTO flight 
    (flight_num, depart_time, arrive_time, price, status, name_airline, plane_id, depart_airport, arrive_airport) 
    VALUES ( %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s, %s)
    '''
    cursor = conn.cursor()
    cursor.execute(query, data)
    conn.commit()
    flash('Adding Succeed!')
    cursor.close()
    return render_template('staff_create.html', message='Adding Succeed!',airports = airports, planes = planes)
    
@app.route('/to_staff_change')
def to_staff_change():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    permission = session.get('permission')
    if permission == 1 or permission == 3:
        name_airline = session.get('airline')
        query = f'SELECT flight_num FROM flight WHERE name_airline = "{name_airline}"'
        cursor = conn.cursor()
        cursor.execute(query)
        flights = cursor.fetchall()
        return render_template('staff_change.html', flights = flights)
    else:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        today = datetime.now().date()
        date_30_days_later = today + timedelta(days=30)
        cursor = conn.cursor()
        query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
        cursor.execute(query)
        flights = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports, message = 'You Have No Permission!')
      
@app.route('/staff_change', methods=['GET', 'POST'])
def staff_change():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    name_airline = session.get('airline')
    query = f'SELECT flight_num FROM flight WHERE name_airline = "{name_airline}"'
    cursor = conn.cursor()
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    status = request.form.get('status')
    flight_num = request.form.get('flight_num')
    query = f'''
    UPDATE flight 
    SET status = "{status}"
    WHERE flight_num = "{flight_num}"
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    flash('Change Succeed!')
    cursor.close()
    return render_template('staff_change.html', message='Change Succeed!', flights = flights)
    
@app.route('/to_staff_plane')
def to_staff_plane():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    permission = session.get('permission')
    if permission > 1:
        name_airline = session.get('airline')
        cursor = conn.cursor()
        query = f"SELECT id, seat FROM airplane WHERE name_airline = '{name_airline}'"
        cursor.execute(query)
        planes = cursor.fetchall()
        cursor.close()
        return render_template('staff_plane.html', planes = planes)
    else:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        today = datetime.now().date()
        date_30_days_later = today + timedelta(days=30)
        cursor = conn.cursor()
        query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
        cursor.execute(query)
        flights = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports, message = 'You Have No Permission!')
      
@app.route('/staff_plane', methods=['GET', 'POST'])
def staff_plane():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    name_airline = session.get('airline')
    data = (
        request.form.get('plane_id'),
        name_airline,
        request.form.get('seat')
    )
    query = '''
    INSERT INTO airplane 
    (id, name_airline, seat)
    VALUES (%s, %s, %s)
    '''
    cursor = conn.cursor()
    cursor.execute(query, data)
    conn.commit()
    flash('Adding Succeed!')
    cursor.close()
    cursor = conn.cursor()
    query = f"SELECT id, seat FROM airplane WHERE name_airline = '{name_airline}'"
    cursor.execute(query)
    planes = cursor.fetchall()
    cursor.close()
    return render_template('staff_plane.html', message='Adding Succeed!', planes = planes)

@app.route('/to_staff_airport')
def to_staff_airport():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    permission = session.get('permission')
    if permission > 1:
        return render_template('staff_airport.html')
    else:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        today = datetime.now().date()
        date_30_days_later = today + timedelta(days=30)
        cursor = conn.cursor()
        query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
        cursor.execute(query)
        flights = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports, message = 'You Have No Permission!')
      
@app.route('/staff_airport', methods=['GET', 'POST'])
def staff_airport():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    data = (
        request.form.get('name'),
        request.form.get('city')
    )
    query = '''
    INSERT INTO airport 
    (name, city)
    VALUES (%s, %s)
    '''
    cursor = conn.cursor()
    cursor.execute(query, data)
    conn.commit()
    flash('Adding Succeed!')
    cursor.close()
    return render_template('staff_airport.html', message='Adding Succeed!')

@app.route('/staff_agent', methods=['GET'])
def staff_agent():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    today = datetime.now().date()
    date_30_before = today - timedelta(days=30)
    date_365_before = today - timedelta(days=365)
    name_airline = session.get('airline')
    query = f'''
    SELECT agent_email, COUNT(ticket_id) FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    NATURAL JOIN works_for w
    WHERE airline_name = "{name_airline}" AND date >= "{date_30_before}"
    GROUP BY agent_email
    ORDER BY COUNT(ticket_id) DESC LIMIT 5
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    agents1 = cursor.fetchall()
    cursor.close()

    query = f'''
    SELECT agent_email, COUNT(ticket_id) FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    NATURAL JOIN works_for w
    WHERE airline_name = "{name_airline}" AND date >= "{date_365_before}"
    GROUP BY agent_email
    ORDER BY COUNT(ticket_id) DESC LIMIT 5
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    agents2 = cursor.fetchall()
    cursor.close()

    query = f'''
    SELECT agent_email, SUM(Price) FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    NATURAL JOIN works_for w
    WHERE airline_name = "{name_airline}" AND date >= "{date_365_before}"
    GROUP BY agent_email
    ORDER BY SUM(Price) DESC LIMIT 5
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    agents3 = cursor.fetchall()
    cursor.close()
    return render_template('staff_agent.html', agents1 = agents1, agents2 = agents2, agents3 = agents3)

@app.route('/staff_customer', methods=['GET'])
def staff_customer():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    today = datetime.now().date()
    date_365_before = today - timedelta(days=365)
    name_airline = session.get('airline')

    query = f'''
    SELECT customer_email, COUNT(ticket_id) FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    WHERE name_airline = "{name_airline}" AND date >= "{date_365_before}"
    GROUP BY customer_email
    ORDER BY COUNT(ticket_id) DESC LIMIT 1
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    top_customer = cursor.fetchone()
    cursor.close()

    query = f'''
    SELECT customer_email, flight_num FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    WHERE name_airline = "{name_airline}"
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    customers = cursor.fetchall()
    cursor.close()
    return render_template('staff_customer.html', top_customer = top_customer, customers = customers)

@app.route('/staff_report', methods=['GET', 'POST'])
def staff_report():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    name_airline = session.get('airline')
    cursor = conn.cursor()
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not start_date and not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    query = """
    SELECT COUNT(ticket.ticket_id)
    FROM purchase
    JOIN ticket ON purchase.ticket_id = ticket.ticket_id
    JOIN flight ON ticket.flight_num = flight.flight_num
    WHERE flight.name_airline = %s AND purchase.date BETWEEN %s AND %s
    """
    cursor.execute(query, (name_airline, start_date, end_date))
    amount = cursor.fetchone()
    # Prepare data for the bar chart
    cursor.close()

    cursor = conn.cursor()
    query = """
    SELECT DATE_FORMAT(date, '%Y-%m') as month, COUNT(ticket.ticket_id) as total_spent
    FROM purchase
    JOIN ticket ON purchase.ticket_id = ticket.ticket_id
    JOIN flight ON ticket.flight_num = flight.flight_num
    WHERE flight.name_airline = %s AND purchase.date BETWEEN %s AND %s
    GROUP BY DATE_FORMAT(date, '%Y-%m')
    ORDER BY month
    """
    cursor.execute(query, (name_airline, start_date, end_date))
    results = cursor.fetchall()
    # Prepare data for the bar chart
    months = [result[0] for result in results]
    count = [result[1] for result in results]

    chart_data = {
        'labels': months,
        'datasets': [{
            'label': 'Tickets Over Time',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'data': count
        }]
    }
    cursor.close()
    return render_template('staff_report.html', amount = amount, chart_data=json.dumps(chart_data))

@app.route('/staff_revenue', methods=['GET'])
def staff_revenue():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    today = datetime.now().date()
    date_30_before = today - timedelta(days=30)
    date_365_before = today - timedelta(days=365)
    name_airline = session.get('airline')

    query = f'''
    SELECT 
        SUM(CASE WHEN agent_email IS NULL THEN price ELSE 0 END) AS Direct_Sales_Revenue,
        SUM(CASE WHEN agent_email IS NOT NULL THEN price ELSE 0 END) AS Indirect_Sales_Revenue
    FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    WHERE name_airline = "{name_airline}" AND date >= "{date_30_before}"
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    month_revenue = cursor.fetchall()
    cursor.close()

    query = f'''
    SELECT 
        SUM(CASE WHEN agent_email IS NULL THEN price ELSE 0 END) AS Direct_Sales_Revenue,
        SUM(CASE WHEN agent_email IS NOT NULL THEN price ELSE 0 END) AS Indirect_Sales_Revenue
    FROM purchase p
    NATURAL JOIN ticket t
    NATURAL JOIN flight f
    WHERE name_airline = "{name_airline}" AND date >= "{date_365_before}"
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    year_revenue = cursor.fetchall()
    cursor.close()
    return render_template('staff_revenue.html', month_revenue = month_revenue, year_revenue = year_revenue)

@app.route('/staff_destination', methods=['GET'])
def staff_destination():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    today = datetime.now().date()
    date_30_before = today - timedelta(days=30)
    date_365_before = today - timedelta(days=365)
    name_airline = session.get('airline')
    query = f'''
    SELECT a.city, COUNT(t.ticket_id) FROM ticket t
    JOIN flight f ON t.flight_num = f.flight_num
    JOIN airport a ON f.arrive_airport = a.name
    WHERE name_airline = "{name_airline}" AND depart_time >= "{date_30_before}"
    GROUP BY a.city
    ORDER BY COUNT(t.ticket_id) DESC LIMIT 3
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    month_destination = cursor.fetchall()
    cursor.close()

    query = f'''
    SELECT a.city, COUNT(t.ticket_id) FROM ticket t
    JOIN flight f ON t.flight_num = f.flight_num
    JOIN airport a ON f.arrive_airport = a.name
    WHERE name_airline = "{name_airline}" AND depart_time >= "{date_365_before}"
    GROUP BY a.city
    ORDER BY COUNT(t.ticket_id) DESC LIMIT 3
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    year_destination = cursor.fetchall()
    cursor.close()

    return render_template('staff_destination.html', month_destination = month_destination, year_destination = year_destination)

@app.route('/to_staff_permission')
def to_staff_permission():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    permission = session.get('permission')
    if permission > 1:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        query = f'''
        SELECT a.email, p.is_operator, p.is_admin
        FROM airline_staff a
        NATURAL JOIN permission p
        WHERE a.name_airline = '{staff_airline}'
        AND a.last_name != '{staff_name}'
        '''
        cursor = conn.cursor()
        cursor.execute(query)
        staffs = cursor.fetchall()
        cursor.close()
        return render_template('staff_permission.html', staffs = staffs)
    else:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        today = datetime.now().date()
        date_30_days_later = today + timedelta(days=30)
        cursor = conn.cursor()
        query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
        cursor.execute(query)
        flights = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports, message = 'You Have No Permission!')
      
@app.route('/staff_permission', methods=['GET', 'POST'])
def staff_permission():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    email = request.form.get('airline_staff')
    operator = request.form.get('is_operator')
    admin = request.form.get('is_admin')
    if operator == '1' and admin == '1':
        permission = 3
    elif operator == '0' and admin == '1':
        permission = 2
    elif operator == '1' and admin == '0':
        permission = 1
    else:
        permission = 0
    query = f'''
    UPDATE airline_staff 
    SET permission_id = "{permission}"
    WHERE email = "{email}"
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    flash('Update Succeed!')
    cursor.close()
    staff_airline = session.get('airline')
    staff_name = session.get('name')
    query = f'''
    SELECT a.email, p.is_operator, p.is_admin
    FROM airline_staff a
    NATURAL JOIN permission p
    WHERE a.name_airline = '{staff_airline}'
    AND a.last_name != '{staff_name}'
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    staffs = cursor.fetchall()
    cursor.close()
    return render_template('staff_permission.html', message='Grant Succeed!', staffs = staffs)

@app.route('/to_staff_new')
def to_staff_new():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    permission = session.get('permission')
    if permission > 1:
        query = f'''
            SELECT a.email
            FROM agent a
            LEFT JOIN works_for w ON a.email = w.agent_email
            WHERE w.agent_email IS NULL;
        '''
        cursor = conn.cursor()
        cursor.execute(query)
        agents = cursor.fetchall()
        cursor.close()
        return render_template('staff_new.html', agents = agents)
    else:
        staff_name = session.get('name')
        staff_airline = session.get('airline')
        today = datetime.now().date()
        date_30_days_later = today + timedelta(days=30)
        cursor = conn.cursor()
        query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
        cursor.execute(query)
        flights = cursor.fetchall()
        cursor.close()
        cursor = conn.cursor()
        query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
        cursor.execute(query)
        airports = cursor.fetchall()
        cursor.close()
        return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports, message = 'You Have No Permission!')
      
@app.route('/staff_new', methods=['GET', 'POST'])
def staff_new():
    if session.get('role') != 'airline_staff':
        return render_template('index.html', message='Oops! You seem lost out there some where :(')
    email = request.form.get('email')
    staff_airline = session.get('airline')
    query = f'''
    INSERT INTO works_for 
    (agent_email, airline_name)
    VALUES ('{email}','{staff_airline}')
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    cursor.close()

    query = f'''
    SELECT a.email
    FROM agent a
    LEFT JOIN works_for w ON a.email = w.agent_email
    WHERE w.agent_email IS NULL;
    '''
    cursor = conn.cursor()
    cursor.execute(query)
    agents = cursor.fetchall()
    cursor.close()
    return render_template('staff_new.html', message='Adding Succeed!', agents = agents)

@app.route('/back')
def back():
    if session.get('role'):
        role = session.get('role')
        if role == 'customer':
            customer_name = session.get('name')
            customer_email = session.get('username')
            cursor = conn.cursor()
            query = f"SELECT f.* FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.customer_email = '{customer_email}' AND f.status = 'upcoming'"
            cursor.execute(query)
            flights = cursor.fetchall()
            cursor.close()
            cursor = conn.cursor()
            query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.customer_email = '{customer_email}' AND f.status = 'upcoming'"
            cursor.execute(query)
            airports = cursor.fetchall()
            cursor.close()
            return render_template('customer_homepage.html', customer_name = customer_name, flights=flights, airports=airports)
        elif role == 'agent':
            agent_name = session.get('name')
            agent_email = session.get('username')
            cursor = conn.cursor()
            query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.agent_email = '{agent_email}' AND f.status = 'upcoming'"
            cursor.execute(query)
            flights = cursor.fetchall()
            cursor.close()
            cursor = conn.cursor()
            query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE p.agent_email = '{agent_email}'"
            cursor.execute(query)
            airports = cursor.fetchall()
            cursor.close()
            return render_template('agent_homepage.html',agent_name = agent_name, flights = flights, airports = airports)
        elif role == 'airline_staff':
            staff_name = session.get('name')
            staff_airline = session.get('airline')
            today = datetime.now().date()
            date_30_days_later = today + timedelta(days=30)
            cursor = conn.cursor()
            query = f"SELECT f.*,p.customer_email FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}' AND f.status = 'upcoming' AND f.depart_time >= '{today}' AND f.depart_time <= '{date_30_days_later}'"
            cursor.execute(query)
            flights = cursor.fetchall()
            cursor.close()
            cursor = conn.cursor()
            query = f"SELECT DISTINCT depart_airport, arrive_airport FROM flight f NATURAL JOIN purchase p NATURAL JOIN ticket t WHERE f.name_airline = '{staff_airline}'"
            cursor.execute(query)
            airports = cursor.fetchall()
            cursor.close()
            return render_template('staff_homepage.html',staff_name = staff_name, flights = flights, airports = airports)
    else:
        return render_template('index.html')
    
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    message = 'See you next time! :D'
    return render_template('index.html',message = message)

if __name__ == '__main__':
    app.run(debug=True)