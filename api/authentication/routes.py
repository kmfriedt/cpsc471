from flask import Blueprint, request, jsonify, json, make_response, render_template
import jwt
from api.models import User, login_required, AccessLevel
from api import app, bcrypt, mysql
import datetime
import pymysql

# all endpoint under authentication Blueprint share common url root of /authentication
authentication = Blueprint('authentication', __name__)

# implement check token validity GET endpoint
@authentication.route('/', methods = ['GET'])
@login_required
def check_token(current_user):
	return jsonify({'message': f'Token is valid for use {current_user.user_id} with acccess {current_user.access.name}'}), 201


# implements user login POST endpoint as documented in the Postman Collection
@authentication.route('/login', methods = ['POST'])
def login_user():

	#check authorization header used by Basic Auth schema
	auth = request.authorization

	#check that login info was sent
	if not auth or not auth.username or not auth.password:
		return make_response('Login Information Incomplete', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})
	

	conn = mysql.connect()
	cursor = conn.cursor()

	#check the db for the user password
	cursor.callproc('get_password', [auth.username])
	data = cursor.fetchall()

	# compare entered password with the stored password. We did not hash passwords for simplicty and readability purpose but this is where we'd used bcrypt library to compared
	# the hash of the stored and entered password
	if (len(data) != 1) or (data[0][0] != auth.password):
		return make_response('Invalid Credentials', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

	# user User constructor to verify valid user details
	user = User(data[0][1], AccessLevel[data[0][2]])

	#create and return a new token. Token timeout length in the config files.
	token = jwt.encode({'user_id' : user.user_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=app.config['TOKEN_TIMEOUT']), 'access' : user.access.value}, app.config['SECRET_KEY'])
	return jsonify({'token' : token.decode('UTF-8')}), 201



@authentication.route('/register', methods = ['POST'])
def register_user():
	user = request.json 
	conn = mysql.connect()
	cursor = conn.cursor()

	try:
		AccessLevel[user['type']]
	except Exception as err:
		return jsonify({'message' : 'Please send a valid user type'}), 400
	
	try:
		cursor.callproc('register_user', list(user.values()))
	except pymysql.MySQLError as err:
		errno = err.args[0]

		if errno == 1062:
			return jsonify({'message' : 'That email is already used'}), 400
		else:
			print(f'SQL error number: {err.args[0]}')
			print(f'SQL error: {err.args[1]}')
			return jsonify({'message' : 'Something went wrong with DB'}), 400
	
	return jsonify({'message' : 'User registered successfully'}), 201