from flask import Flask, render_template, request, session, url_for, redirect
import pymysql, pymysql.cursors
import hashlib, calendar
from datetime import datetime, date, timedelta

# Run App: flask --app airport run
# For Errors: chrome://net-internals/#sockets

# Initialize a Flask app
app = Flask(__name__)
app.secret_key = 'tempaweofij'


# Configure MySQL
conn = pymysql.connect(
    host = 'localhost',
    user = 'root',
    password = '',
    db = 'air-ticket-reservation-system',
    charset = 'utf8mb4',
    cursorclass = pymysql.cursors.DictCursor
)

# Define a simple route function
@app.route('/')
def index():
	# make the following code its own function later
	login = None
	account = None
	if('user' in session):
		# set up so that elements on the page can change dynamically
		login = session['user']
		account = session['account']
	return render_template('index.html', login=login, account=account)

@app.route('/results', methods=['GET', 'POST'])
def results():
	location = request.form['location']
	origin = request.form['origin']
	destination = request.form['destination']
	date_str = request.form['date']

	date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

	cursor = conn.cursor()

	login = None
	account = None
	if('user' in session):
		# set up so that elements on the page can change dynamically
		login = session['user']
		account = session['account']

	if (location == "city"):
		if ('account' in session and (session['account'] == 'staff' or session['account'] == 'admin' or session['account']=='operator' or session['account'] == 'admin-operator')):
			# retrieve airline -- filters based on staff's airline
			query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
			cursor.execute(query,(session['user']))
			airline = cursor.fetchone()['airline_name']
			
			# retrieve flights
			query = 'SELECT * FROM flight WHERE airline_name = %s AND departure_airport = (SELECT airport_name FROM airport WHERE airport_city = %s) AND arrival_airport = (SELECT airport_name FROM airport WHERE airport_city = %s) AND DATE(departure_time) = %s AND flight_status = "upcoming"'
			cursor.execute(query,(airline, origin,destination,f'{date_obj}%'))
		elif ('account' in session and (session['account'] == 'agent')):
			# retrieve airline -- fliters based on employment
			query = 'SELECT booking_agent_email FROM booking_agent WHERE booking_agent_id = %s'
			cursor.execute(query,(session['user']))
			email = cursor.fetchone()['booking_agent_email']

			# retrieve flights
			query = 'SELECT * FROM flight WHERE airline_name IN (SELECT airline_name FROM employee WHERE airline_name = %s AND booking_agent_email = %s) AND departure_airport = (SELECT airport_name FROM airport WHERE airport_city = %s) AND arrival_airport = (SELECT airport_name FROM airport WHERE airport_city = %s) AND DATE(departure_time) = %s AND flight_status = "upcoming"'
			cursor.execute(query,(airline, email, origin,destination,f'{date_obj}%'))
		else:
			# retrieve flights
			query = 'SELECT * FROM flight WHERE departure_airport = (SELECT airport_name FROM airport WHERE airport_city = %s) AND arrival_airport = (SELECT airport_name FROM airport WHERE airport_city = %s) AND DATE(departure_time) = %s AND flight_status = "upcoming"'
			cursor.execute(query,(origin,destination,f'{date_obj}%'))
	elif (location == "airport"):
		if ('account' in session and (session['account'] == 'staff' or session['account'] == 'admin' or session['account'] =='operator' or session['account'] == 'admin-operator')):
			query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
			cursor.execute(query,(session['user']))
			airline = cursor.fetchone()['airline_name']

			query = 'SELECT * FROM flight WHERE airline_name = %s AND departure_airport = %s AND arrival_airport = %s AND DATE(departure_time) = %s AND flight_status = "upcoming"'
			cursor.execute(query,(airline, origin, destination, f'{date_obj}%'))
		elif ('account' in session and (session['account'] == 'agent')):
			query = 'SELECT booking_agent_email FROM booking_agent WHERE booking_agent_id = %s'
			cursor.execute(query,(session['user']))
			email = cursor.fetchone()['booking_agent_email']

			query = 'SELECT * FROM flight WHERE airline_name IN (SELECT airline_name FROM employee WHERE booking_agent_email = %s) AND departure_airport = %s AND arrival_airport = %s AND DATE(departure_time) = %s AND flight_status = "upcoming"'
			cursor.execute(query,(email, origin, destination,f'{date_obj}%'))
		else:
			query = 'SELECT * FROM flight WHERE departure_airport = %s AND arrival_airport = %s AND DATE(departure_time) = %s AND flight_status = "upcoming"'
			cursor.execute(query,(origin, destination, f'{date_obj}%'))
			
	data = cursor.fetchall()
	
	cursor.close()

	if (data):
		return render_template('results.html', data=data, login=login, account=account)
	else:
		error = 'No Available Flights'
		return render_template('results.html', error=error, login=login, account=account)

@app.route('/check')
def check():
	login = None
	account = None
	if('user' in session):
		# set up so that elements on the page can change dynamically
		login = session['user']
		account = session['account']
	return render_template('check.html', login=login, account=account)

@app.route('/status', methods=['GET', 'POST'])
def status():
	airline = request.form["airline"]
	flight = request.form["flight"]
	time = request.form["time"]
	date_str = request.form['date']

	date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

	cursor = conn.cursor()

	if (time == "departure"):
		# retrieves
		query = 'SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND DATE(departure_time) = %s'
		cursor.execute(query,(airline,flight,f'{date_obj}%'))
	elif (time == "arrival"):
		query = 'SELECT * FROM flight WHERE airline_name = %s AND flight_num = %s AND arrival_time LIKE %s'
		cursor.execute(query,(airline, flight, f'{date_obj}%'))
	
	data = cursor.fetchall()
	cursor.close()

	if (data):
		return render_template('status.html', data=data)
	else:
		error = 'Flight Does Not Exist'
		return render_template('status.html', error=error)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
	airline = request.form['airlineName']
	flight = request.form['flightNum']
	airplane = request.form['airplaneNum']

	if ('user' in session):
		cursor = conn.cursor()

		query = 'SELECT COUNT(*) FROM ticket WHERE airline_name = %s AND flight_num = %s'
		cursor.execute(query,(airline, flight))

		tickets = cursor.fetchone()

		query = 'SELECT seats FROM airplane WHERE airline_name = %s AND airplane_id = %s'
		cursor.execute(query,(airline,airplane))

		seats = cursor.fetchone()
			
		if( not (tickets) or tickets['COUNT(*)'] < seats['seats']):
			cursor.execute('SELECT COUNT(*) FROM ticket')
			lastID = cursor.fetchone()
			currID = 0

			if (lastID):
				currID = lastID['COUNT(*)'] + 1

			if('account' in session and session['account'] == 'customer'):
				ins = 'INSERT INTO ticket VALUES (%s, %s, %s, %s, %s, %s)'
				# reformat currID into char(5) and inserting into ticket
				cursor.execute(ins,(f'{currID:05}', session['user'], airline, flight, None, datetime.today()))
			elif('account' in session and session['account'] == 'agent'):
				query = 'SELECT * FROM employee WHERE airline_name = %s AND booking_agent_email IN (SELECT booking_agent_email FROM booking_agent WHERE booking_agent_id = %s)'
				cursor.execute(query, (airline, session['user']))
				data = cursor.fetchone()

				print(data)

				custEmail = request.form['custEmail']
				query = 'SELECT * FROM customer WHERE cust_email = %s'
				cursor.execute(query,(custEmail))
				client = cursor.fetchone()

				if(data and client):
					ins = 'INSERT INTO ticket VALUES (%s, %s, %s, %s, %s, %s)'
					cursor.execute(ins,(f'{currID:05}',custEmail, airline, flight, session['user'], datetime.today()))
				elif (not(client)):
					error = 'This customer has not created an account and is ineligible to buy a ticket.'
					return render_template('index.html', error=error, login=session['user'], account=session['account'])
				else:
					error = 'You do not have the permissions to buy this ticket.'
					cursor.close()
					return render_template('index.html', error=error, login=session['user'], account=session['account'])
			
			msg = 'The ticket purchase was successful.'
			conn.commit()
			cursor.close()
			
			return render_template('index.html', msg=msg, login=session['user'], account=session['account'])
		else:
			cursor.close()
			error = 'There are no more available seats for this flight'
			return render_template('index.html', error=error, login=session['user'], account=session['account'])
	else:
		error = 'Please login before purchasing'
		return render_template('login.html', error=error)	
	
#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
	#grabs information from the forms
	email = request.form['email']
	password = request.form['password']
	hashedPass = hashlib.md5(password.encode('utf-8')).hexdigest()

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = "SELECT * FROM customer WHERE cust_email = %s and cust_password = %s"
	cursor.execute(query,(email, hashedPass))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['user'] = email
		session['account'] = 'customer'
		return render_template('index.html', login=session['user'], account=session['account'])
	else:
		#returns an error message to the html page
		error = 'Invalid email or password'
		return render_template('login.html', error=error)

@app.route('/loginAgent')
def loginAgent():
	return render_template('loginAgent.html')

@app.route('/loginAgentAuth', methods=['GET','POST'])
def loginAgentAuth():
	agentID = request.form['agentID']
	formatedID = f'{agentID:05}'
	email = request.form['email']
	password = request.form['password']
	hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()

	cursor = conn.cursor()
	query = 'SELECT * FROM booking_agent WHERE booking_agent_email = %s AND booking_agent_id = %s AND agent_password = %s'
	cursor.execute(query,(email, formatedID, hashedPassword))
	data = cursor.fetchone()
	cursor.close()

	if (data):
		session['user'] = formatedID
		session['account'] = 'agent'
		return render_template('index.html', login=session['user'], account=session['account'])
	else:
		error = 'Invalid ID, email, or password'
		return render_template('loginAgent.html', error=error)

@app.route('/loginStaff')
def loginStaff():
	return render_template('loginStaff.html')

@app.route('/loginStaffAuth', methods=['GET','POST'])
def loginStaffAuth():
	username = request.form['username']
	password = request.form['password']
	hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()

	cursor = conn.cursor()
	query = 'SELECT * FROM airline_staff WHERE staff_username = %s AND staff_password = %s'
	cursor.execute(query,(username, hashedPassword))
	data = cursor.fetchone()

	if (data):
		session['user'] = username

		# retrieve all permissions for the staff account
		query = 'SELECT permission FROM permissions WHERE staff_username = %s'
		cursor.execute(query,(username))
		data = cursor.fetchall()

		# create an account session to keep track of permissions
		if (not (data)):
			session['account'] = 'staff'
		elif (len(data) == 2):
			# if the returned array has two values, then there are two permissions
			# if a staff already has a permission, the permission will not be added
			# avoid having error trying to retrieve non-existent value
			session['account'] = 'admin-operator'
		elif (data[0]['permission'] == 'admin'):
			session['account'] = 'admin'
		elif ( data[0]['permission'] == 'operator'):
			session['account'] = 'operator'			

		start = date.today().isoformat()
		end = (date.today()+timedelta(days=30)).isoformat()

		query = 'SELECT * FROM flight WHERE airline_name = (SELECT airline_name FROM airline_staff WHERE staff_username = %s) AND flight_status = "upcoming" AND departure_time BETWEEN %s AND %s'
		cursor.execute(query,(session['user'],start,end))
		data = cursor.fetchall()

		print(data)
		
		cursor.close()
		return render_template('view.html', data=data, start=start, end=end, login=session['user'], account=session['account'])
	else:
		cursor.close()
		error = 'Invalid username or password'
		return render_template('loginStaff.html', error=error)

@app.route('/view', methods=['GET','POST'])
def view():
	cursor = conn.cursor()

	start = date.today().isoformat()
	end = (date.today()+timedelta(days=30)).isoformat()

	query = 'SELECT * FROM flight WHERE airline_name = (SELECT airline_name FROM airline_staff WHERE staff_username = %s) AND flight_status = "upcoming" AND departure_time BETWEEN %s AND %s'
	cursor.execute(query,(session['user'],start,end))
	data = cursor.fetchall()
	
	return render_template('view.html', data=data, start=start, end=end,login=session['user'], account=session['account'])

@app.route('/viewFlight', methods=['GET', 'POST'])
def viewFlight():
	airline = request.form['airlineName']
	flight = request.form['flightNum']

	cursor = conn.cursor()
	query = 'SELECT cust_name, cust_email FROM customer natural join ticket WHERE airline_name = %s AND flight_num = %s'
	cursor.execute(query,(airline,flight))
	data = cursor.fetchall()

	return render_template('viewFlight.html',data=data, flight=flight, login=session['user'], account=session['account'])

@app.route('/home', methods=['GET','POST'])
def home():
	cursor = conn.cursor()
	query = 'SELECT * FROM flight WHERE flight_status = "upcoming" AND flight_num IN (SELECT flight_num FROM ticket WHERE cust_email = %s)'
	cursor.execute(query,(session['user']))

	data = cursor.fetchall()
	print(data)

	total = None

	start = (date.today()-timedelta(days=365)).isoformat()
	end = date.today().isoformat()
	query = 'SELECT SUM(price) as sum FROM flight natural join ticket WHERE cust_email = %s'
	cursor.execute(query,(session['user']))
	sum = cursor.fetchone()
	
	if(sum):
		total = {'start': start, 'end': end, 'total': sum}

	spent = None

	if ('start' in request.form):
		start = request.form['start']
		end = request.form['end']
	else:
		start = (date.today()-timedelta(days=6*30)).isoformat()

	query = 'SELECT cust_email, MONTH(booking_date), YEAR(booking_date), SUM(price) FROM flight natural join ticket WHERE cust_email = %s AND booking_date BETWEEN %s AND %s GROUP BY cust_email, MONTH(booking_date), YEAR(booking_date)'
	cursor.execute(query,(session['user'],start,end))
	spent = cursor.fetchall()

	cursor.close()

	return render_template('home.html', data=data, total=total, spent=spent, start=start, end=end, login=session['user'], account=session['account'])

@app.route('/homeAgent', methods=['GET', 'POST'])
def homeAgent():
	cursor = conn.cursor()

	# find all tickets that the booking agent booked on behalf of customers 
	query = 'SELECT * FROM flight natural join ticket WHERE flight_status = "upcoming" AND booking_agent_id = %s'
	cursor.execute(query,(session['user']))
	data = cursor.fetchall()
	
	commission = {}

	if ('start' in request.form): # code can be optimized -- currently repetitive
		start = request.form['start']
		end = request.form['end']

		query = 'SELECT SUM(price) FROM flight natural join ticket WHERE booking_agent_id = %s AND booking_date BETWEEN %s AND %s'
		cursor.execute(query,(session['user'], start, end))
		total = cursor.fetchone()['SUM(price)']
		if (total):
			total = round(float(total) * 0.1,2)
		else:
			total = 0

		query = 'SELECT COUNT(*) FROM ticket WHERE booking_agent_id = %s AND booking_date BETWEEN %s AND %s'
		cursor.execute(query,(session['user'], start, end))
		tickets = cursor.fetchone()['COUNT(*)']
		average = 0

		if (tickets > 0):
			average = round(total / tickets,2)

		commission = {'start': start, 'end': end, 'total': '${:,.2f}'.format(total), 'average': '${:,.2f}'.format(average), 'tickets': tickets}
	else:
		start = (date.today()-timedelta(days=30)).isoformat()
		end = date.today().isoformat()
	
		query = query = 'SELECT SUM(price) FROM flight natural join ticket WHERE booking_agent_id = %s AND booking_date BETWEEN %s AND %s'
		cursor.execute(query,(session['user'], start, end))
		total = cursor.fetchone()['SUM(price)']
		if (total):
			total = round(float(total) * 0.1,2)
		else:
			total = 0

		query = 'SELECT COUNT(*) FROM ticket WHERE booking_agent_id = %s AND booking_date BETWEEN %s AND %s'
		cursor.execute(query,(session['user'], start, end))
		tickets = cursor.fetchone()['COUNT(*)']
		average = 0

		if (tickets > 0):
			average = round(total / tickets,2)

		commission = {'start': start, 'end': end, 'total': '${:,.2f}'.format(total), 'average': '${:,.2f}'.format(average), 'tickets': tickets}
		
	start = (date.today()-timedelta(days=6*30)).isoformat()
	end = date.today().isoformat()
	
	query = 'SELECT cust_email, COUNT(*) as tickets FROM ticket WHERE booking_agent_id = %s AND booking_date BETWEEN %s AND %s GROUP BY cust_email ORDER BY tickets DESC LIMIT 5'
	cursor.execute(query, (session['user'], start, end))
	tickets = cursor.fetchall()
	print(tickets)

	start = (date.today()-timedelta(days=365)).isoformat()

	# edit prev code to do the math in the SELECT
	query = 'SELECT cust_email, SUM(price)*0.1 as total FROM flight natural join ticket WHERE booking_agent_id = %s AND booking_date BETWEEN %s AND %s GROUP BY cust_email ORDER BY total DESC LIMIT 5'
	cursor.execute(query,(session['user'],start, end))
	total = cursor.fetchall()
	print(total)

	cursor.close()
	
	return render_template('homeAgent.html', data=data,tickets=tickets, total=total, commission=commission, login=session['user'], account=session['account'])

@app.route('/homeStaff')
def homeStaff():
	return render_template('homeStaff.html', login=session['user'], account=session['account'])

@app.route('/changeFlight', methods=['GET','POST'])
def changeFlight():
	flight = request.form['flight']
	status = request.form['status']

	cursor = conn.cursor()
	query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
	cursor.execute(query,(session['user']))
	airline = cursor.fetchone()

	query = 'SELECT * FROM flight WHERE flight_num = %s AND airline_name = %s'
	cursor.execute(query,(f'{flight:0>5}',airline['airline_name']))
	data = cursor.fetchone()

	if(data):
		update = 'UPDATE flight SET flight_status = %s WHERE flight_num = %s AND airline_name = %s'
		cursor.execute(update, (status,f'{flight:0>5}',airline['airline_name']))
		conn.commit()
		cursor.close()
		msgStatus = "Flight status has been successfully updated"
		return render_template('homeStaff.html', msgStatus=msgStatus, login=session['user'], account=session['account'])
	else:
		cursor.close()
		errorStatus = "No such flight exists"
		return render_template('homeStaff.html', errorStatus=errorStatus, login=session['user'], account=session['account'])

@app.route('/newFlight', methods=['GET','POST'])
def newFlight():
	price = request.form['price']
	status = request.form['status']
	departAirport = request.form['departAirport'].upper()
	departDate = request.form['departDate']
	departTime = request.form['departTime']
	arrivalAirport = request.form['arrivalAirport'].upper()
	arrivalDate = request.form['arrivalDate']
	arrivalTime = request.form['arrivalTime']
	plane = request.form['plane']

	departure = f"{departDate} {departTime}"
	departDatetime = datetime.strptime(departure, '%Y-%m-%d %H:%M:%S')
	arrival = f"{arrivalDate} {arrivalTime}"
	arrivalDatetime = datetime.strptime(arrival, '%Y-%m-%d %H:%M:%S')

	try:
		cursor = conn.cursor()
		query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
		cursor.execute(query,(session['user']))
		airline = cursor.fetchone()

		query = 'SELECT COUNT(*) FROM flight WHERE airline_name = %s'
		cursor.execute(query, (airline['airline_name']))
		flight = cursor.fetchone()['COUNT(*)'] + 1

		insert = 'INSERT INTO flight VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
		query = cursor.execute(insert, (f'{flight:0>5}',airline['airline_name'], departAirport, departDatetime, arrivalAirport, arrivalDatetime, price, status, plane))
		
		conn.commit()
		cursor.close()

		msgNew = "Flight " + str(f'{flight:0>5}') + " added into database successfully"
		return render_template('homeStaff.html', msgNew=msgNew, login=session['user'], account=session['account'])
	except:
		errorNew = "Flight could not be made, airport or airplane id does not exist"
		return render_template('homeStaff.html', errorNew=errorNew, login=session['user'], account=session['account'])

@app.route('/newPlane', methods=['GET','POST'])
def newPlane():
	seats = request.form['seats']
	
	cursor = conn.cursor()
	query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
	cursor.execute(query,(session['user']))
	airline = cursor.fetchone()['airline_name']

	query = 'SELECT COUNT(*) FROM airplane WHERE airline_name = %s'
	cursor.execute(query, (airline))
	plane = cursor.fetchone()['COUNT(*)'] + 1

	insert = 'INSERT INTO airplane VALUES (%s, %s, %s)'
	query = cursor.execute(insert,(f'{plane:0>5}', airline, seats))

	conn.commit()
	cursor.close()

	msgPlane = "Plane " + str(f'{plane:0>5}') + " added into database successfully"
	return render_template('homeStaff.html', msgPlane=msgPlane, login=session['user'], account=session['account'])

@app.route('/newAirport', methods=['GET','POST'])
def newAirport():
	airport = request.form['airport'].upper()
	city = request.form['city']

	try:
		cursor = conn.cursor()
		insert = 'INSERT INTO airport VALUES (%s,%s)'
		cursor.execute(insert,(airport,city))

		conn.commit()
		cursor.close()

		msgAirport = "Airport added into database successfully"
		return render_template('homeStaff.html', msgAirport=msgAirport, login=session['user'], account=session['account'])
	except:
		errorAirport = "Airport already exists in database"
		return render_template('homeStaff.html', errorAirport=errorAirport, login=session['user'], account=session['account'])

@app.route('/newPerms', methods=['GET','POST'])
def newPerms():
	username = request.form['username']
	permission = request.form['permission']

	try:
		cursor = conn.cursor()
		insert = 'INSERT INTO permissions VALUES (%s, %s)'
		cursor.execute(insert,(username,permission))

		conn.commit()
		cursor.close()

		msgPerms = "Permissions added successfully"
		return render_template('homeStaff.html', msgPerms=msgPerms, login=session['user'], account=session['account'])
	except:
		errorPerms = "Permissions already exist or staff does not exist"
		return render_template('homeStaff.html', errorPerms=errorPerms, login=session['user'], account=session['account'])

@app.route('/newAgent', methods=['GET','POST'])
def newAgent():
	email = request.form['email']

	try:
		# optimize getting the airline
		cursor = conn.cursor()
		query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
		cursor.execute(query,(session['user']))
		airline = cursor.fetchone()['airline_name']
		print(airline)

		insert = 'INSERT INTO employee VALUES (%s,%s)'
		cursor.execute(insert,(airline,email))
		conn.commit()

		msgAgent = "Agent is now employeed by airline"
		return render_template('homeStaff.html', msgAgent=msgAgent, login=session['user'], account=session['account'])
	except:
		errorAgent = "There does not exist an agent with this email or agent is already employeed"
		return render_template('homeStaff.html', errorAgent=errorAgent, login=session['user'], account=session['account'])


@app.route('/analytics', methods=['GET','POST'])
def analytics():

	cursor = conn.cursor()

	# retrieve airline
	query = 'SELECT airline_name FROM airline_staff WHERE staff_username = %s'
	cursor.execute(query,(session['user']))
	airline = cursor.fetchone()['airline_name']

	# retrieve top five booking agents based on past month ticket sales
	start = (date.today()-timedelta(days=30)).isoformat()
	end = date.today().isoformat()
	query = 'SELECT booking_agent_email, COUNT(*) as tickets FROM flight natural join ticket natural join booking_agent WHERE airline_name = %s AND booking_date BETWEEN %s AND %s GROUP BY booking_agent_email ORDER BY tickets DESC LIMIT 5'
	cursor.execute(query,(airline, start, end))
	ticketMonth = cursor.fetchall()
	
	# retrieve total tickets sold in the past month
	query = 'SELECT COALESCE(COUNT(*),0) as sales FROM ticket WHERE airline_name = %s AND booking_date BETWEEN %s AND %s'
	cursor.execute(query,(airline,start,end))
	soldMonth = cursor.fetchone()['sales']

	# retrieve total revenue from direct sales in past month
	query = 'SELECT COALESCE(SUM(price),0) as sales FROM ticket natural join flight WHERE airline_name = %s AND booking_date BETWEEN %s AND %s AND booking_agent_id IS NULL'
	cursor.execute(query,(airline,start,end))
	monthDirect = cursor.fetchone()['sales']
 
	# retrieve total revenue from indirect month
	query = 'SELECT COALESCE(SUM(price),0) as sales FROM ticket natural join flight WHERE airline_name = %s AND booking_date BETWEEN %s AND %s AND booking_agent_id IS NOT NULL'
	cursor.execute(query,(airline,start,end))
	monthIndirect = cursor.fetchone()['sales']

	# retrieve top destinations last month
	query = 'SELECT airport_city, COUNT(*) as trips FROM ticket natural join flight join airport WHERE airline_name = %s AND airport_name = arrival_airport AND booking_date BETWEEN %s AND %s GROUP BY airport_city ORDER BY trips DESC LIMIT 3'
	cursor.execute(query,(airline,start,end))
	oneMonth = cursor.fetchall()
	print(oneMonth)
	
	# retrieve top destinations two months ago
	cursor.execute(query,(airline,start,end))
	twoMonth = cursor.fetchall()

	# retrieve top destinations three months ago
	cursor.execute(query,(airline,start,end))
	threeMonth = cursor.fetchall()

	# retrieve top destinations last year
	query = 'SELECT airport_city, COUNT(*) as trips FROM ticket natural join flight join airport WHERE airline_name = %s AND airport_name = arrival_airport AND booking_date BETWEEN %s AND %s GROUP BY airport_city ORDER BY trips DESC LIMIT 3'
	cursor.execute(query,(airline,start,end))
	lastYear = cursor.fetchall()

	# retrieve top five booking agents based on past year ticket sales
	start = (date.today()-timedelta(days=365)).isoformat()
	query = 'SELECT booking_agent_email, COUNT(*) as tickets FROM flight natural join ticket natural join booking_agent WHERE airline_name = %s AND booking_date BETWEEN %s AND %s GROUP BY booking_agent_email ORDER BY tickets DESC LIMIT 5'
	cursor.execute(query,(airline,start,end))
	ticketYear = cursor.fetchall()

	# retrieve total tickets sold in the past year
	query = 'SELECT COALESCE(COUNT(*),0) as sales FROM ticket WHERE airline_name = %s AND booking_date BETWEEN %s AND %s'
	cursor.execute(query,(airline,start,end))
	soldYear = cursor.fetchone()['sales']

	# retrieve top five booking agents based on past year commission
	query = 'SELECT booking_agent_email, SUM(price)*0.1 as commission FROM flight natural join ticket natural join booking_agent WHERE airline_name =%s AND booking_date BETWEEN %s AND %s GROUP BY booking_agent_email ORDER BY commission DESC LIMIT 5'
	cursor.execute(query,(airline, start, end))
	commission = cursor.fetchall()
	print(commission)

	# retrieve most frequent customer
	query = 'SELECT cust_email, COUNT(*) as tickets FROM ticket WHERE airline_name = %s GROUP BY cust_email ORDER BY tickets LIMIT 1'
	cursor.execute(query,(airline))
	customer = cursor.fetchone()

	# retrieve monthly sales
	query = 'SELECT COUNT(*) as sales, MONTH(booking_date) as month, YEAR(booking_date) as year FROM ticket WHERE airline_name = %s AND booking_date BETWEEN %s AND %s GROUP BY month, year'
	cursor.execute(query,(airline,start,end))
	monthlySales = cursor.fetchall()

	# retrieve total revenue from direct sales in past year
	query = 'SELECT COALESCE(SUM(price),0) as sales FROM ticket natural join flight WHERE airline_name = %s AND booking_date BETWEEN %s AND %s AND booking_agent_id IS NULL'
	cursor.execute(query,(airline,start,end))
	yearDirect = cursor.fetchone()['sales']
 
	# retrieve total revenue from indirect sales
	query = 'SELECT COALESCE(SUM(price),0) as sales FROM ticket natural join flight WHERE airline_name = %s AND booking_date BETWEEN %s AND %s AND booking_agent_id IS NOT NULL'
	cursor.execute(query,(airline,start,end))
	yearIndirect = cursor.fetchone()['sales']	

	try:
		email = request.form['email']
		query = 'SELECT * FROM ticket natural join flight WHERE airline_name = %s AND cust_email = %s'
		cursor.execute(query,(airline,email))
		data = cursor.fetchall()
		
		cursor.close()

		if(data):
			return render_template('customerFlight.html', oneMonth=oneMonth, twoMonth=twoMonth, threeMonth=threeMonth, lastYear=lastYear, monthDirect=monthDirect, monthIndirect=monthIndirect, yearDirect=yearDirect, yearIndirect=yearIndirect, monthlySales=monthlySales, data=data, login=session['user'], account=session['account'])
		else:
			msgCust = 'This customer has not booked a flight'
			return render_template('analytics.html', oneMonth=oneMonth, twoMonth=twoMonth, threeMonth=threeMonth, lastYear=lastYear, monthDirect=monthDirect, monthIndirect=monthIndirect, yearDirect=yearDirect, yearIndirect=yearIndirect, monthlySales=monthlySales, soldMonth=soldMonth, soldYear=soldYear, ticketMonth=ticketMonth, ticketYear=ticketYear, commission=commission, customer=customer, msgCust=msgCust, login=session['user'], account=session['account'])
	except:
		try:
			start = request.form['start']
			end = request.form['end']
			query = 'SELECT COUNT(*) FROM ticket WHERE airline_name = %s AND booking_date BETWEEN %s AND %s'
			cursor.execute(query,(airline,start,end))
			soldRange = cursor.fetchone()['COUNT(*)']

			query = 'SELECT COUNT(*) as sales, MONTH(booking_date) as month, YEAR(booking_date) as year FROM ticket WHERE airline_name = %s AND booking_date BETWEEN %s AND %s GROUP BY month, year'
			cursor.execute(query,(airline,start,end))
			monthlySales = cursor.fetchall()

			cursor.close()
			return render_template('analytics.html', oneMonth=oneMonth, twoMonth=twoMonth, threeMonth=threeMonth, lastYear=lastYear, monthDirect=monthDirect, monthIndirect=monthIndirect, yearDirect=yearDirect, yearIndirect=yearIndirect, monthlySales=monthlySales, soldRange=soldRange, start=start, end=end, soldMonth=soldMonth, soldYear=soldYear, ticketMonth=ticketMonth, ticketYear=ticketYear, commission=commission, customer=customer, login=session['user'], account=session['account'])
		except:

			cursor.close()
			return render_template('analytics.html', oneMonth=oneMonth, twoMonth=twoMonth, threeMonth=threeMonth, lastYear=lastYear, monthDirect=monthDirect, monthIndirect=monthIndirect, yearDirect=yearDirect, yearIndirect=yearIndirect, monthlySales=monthlySales, soldMonth=soldMonth, soldYear=soldYear, ticketMonth=ticketMonth, ticketYear=ticketYear, commission=commission, customer=customer, login=session['user'], account=session['account'])

@app.route('/register')
def register():
	return render_template('register.html')

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	name = request.form['name']
	tel = request.form['phoneNumber']
	email = request.form['email']
	# add encryption
	password = request.form['password']
	hashedPass = hashlib.md5(password.encode('utf-8')).hexdigest()
	building = request.form['building']
	street = request.form['street']
	city = request.form['city']
	state = request.form['state']
	passportNum = request.form['passportNum']
	pE_obj = request.form['passportExpiration']
	country = request.form['country']
	dob_obj = request.form['dob']

	#cursor used to send queries
	cursor = conn.cursor()
	
	query = "SELECT * FROM customer WHERE cust_email = %s"
	cursor.execute(query,(email))

	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	
	if(data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		cursor.close()
		return render_template('register.html', error = error)
	else:
		ins = "INSERT INTO customer VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		cursor.execute(ins,(email, name, hashedPass, building, street, city, state, tel, passportNum, pE_obj, country, dob_obj))
		conn.commit()
		cursor.close()
		return render_template('login.html')
	
@app.route('/registerAgent')
def registerAgent():
	return render_template('registerAgent.html')

@app.route('/registerAgentAuth', methods=['GET','POST'])
def registerAgentAuth():
	email = request.form['email']
	password = request.form['password']
	hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()

	# to calculate which ID number to assign, count all IDs, then add one to count to create ID?
	cursor = conn.cursor()
	query = 'SELECT * FROM booking_agent WHERE booking_agent_email = %s'

	cursor.execute(query,(email))
	data = cursor.fetchone()

	print(data)

	if(data):
		error = 'This user already exists'
		cursor.close()
		return render_template('registerAgent.html', error = error)
	else:
		cursor.execute('SELECT COUNT(*) FROM booking_agent')
		lastID = cursor.fetchone()
		currID = 0

		if (lastID):
			currID = lastID['COUNT(*)'] + 1

		formated = f'{currID:05}'
		
		ins = 'INSERT INTO booking_agent VALUES (%s, %s, %s)'
		cursor.execute(ins,(email, hashedPassword, f'{currID:05}'))
		conn.commit()
		cursor.close()

		msg = 'Registration Successful. Your ID is ' + formated

		return render_template('loginAgent.html', msg=msg)
	
@app.route('/registerStaff')
def registerStaff():
	return render_template('registerStaff.html')

@app.route('/registerStaffAuth', methods=['GET','POST'])
def registerStaffAuth():
	username = request.form['username']
	password = request.form['password']
	hashedPassword = hashlib.md5(password.encode('utf-8')).hexdigest()
	first = request.form['first']
	last = request.form['last']
	dob = request.form['dob']
	airline = request.form['airline']

	#cursor used to send queries
	cursor = conn.cursor()
	
	query = "SELECT * FROM airline_staff WHERE staff_username = %s"
	cursor.execute(query,(username))

	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	
	if(data):
		#If the previous query returns data, then user exists
		error = "This user already exists"
		cursor.close()
		return render_template('registerStaff.html', error = error)
	else:
		try:
			ins = "INSERT INTO airline_staff VALUES (%s, %s, %s, %s, %s, %s)"
			cursor.execute(ins,(username, hashedPassword, first, last, dob, airline))
			conn.commit()
			cursor.close()
			msg = 'Account registration succssful.'
			return render_template('loginStaff.html', msg=msg)
		except:
			#If the previous query returns data, then user exists
			error = "This airline does not exist"
			cursor.close()
			return render_template('registerStaff.html', error = error)

@app.route('/logout')
def logout():
	session.clear()
	# change to customer / staff / agent to keep track of what type of session in active
	# add permissions in as well
	return render_template('/login.html')

# Run the app
if __name__ == '__main__':
    app.run('127.0.0.1', 5000, debug = True)
