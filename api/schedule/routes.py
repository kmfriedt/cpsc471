from flask import Blueprint, jsonify, request
from api.models import login_required, User, AccessLevel
from api import mysql
import pymysql

# all endpoint under schedule Blueprint share common url root of /schedule
schedule = Blueprint('schedule', __name__)


@schedule.route('/game/', methods = ['POST'])
@login_required
def record_game(current_user):
	req = request.json
	
	#check access level
	if current_user.access is not AccessLevel.admin:
		return jsonify({'message' : 'Invlaid access level, requires admin token'}), 401
	conn = mysql.connect()
	cursor = conn.cursor()


	#validate body, check all the games to make sure all the fields have been filled out
	for i in range(0,len(req['games'])):
		if req['games'][i]['home'] is None:
			return jsonify({'message' : 'The home team Id must be provided, error at index: ' + str(i)}), 400
		if req['games'][i]['away'] is None:
			return jsonify({'message' : 'The away team Id must be provided, error at index: ' + str(i)}), 400
		if req['games'][i]['date'] is None:
			return jsonify({'message' : 'The date of the game must be provided, error at index: ' + str(i)}), 400
		if req['games'][i]['location'] is None:
			return jsonify({'message' : 'The location Id of the game must be provided, error at index: ' + str(i)}), 400
		if req['games'][i]['season'] is None:
			return jsonify({'message' : 'The season Id for the teams must be provided, error at index: ' + str(i)}), 400
		
	#iterate through the games list
	for i in range(0,len(req['games'])):

		#call stored procedure for each game
		try:
			cursor.callproc('post_game_schedule',[req['games'][i]['home'], req['games'][i]['away'], req['games'][i]['date'], req['games'][i]['location'], req['games'][i]['season']])
		except pymysql.MySQLError as err:
			errno = err.args[0]
			print(f'Error number: {errno}')
			#get errors for if the body is invalid
			if errno == 1644:
				return jsonify({'message' : err.args[1],
								'index': i }), 409
				
	return jsonify({'message' : 'Updated the game schedule in the Data Base'}), 201


@schedule.route('/referee/', methods = ['POST'])
@login_required
def post_ref_schedule(current_user):
	# retrieve query string parameters from URL
	ref_id = current_user.user_id
	game_id = request.args.get('game_id', default = None, type = int)

	# error check: ensure that both ref_id and game_id are not null
	if (ref_id is None or game_id is None):
		return jsonify({'message': 'The game_id must be provided'}), 400

	# error check: ensure that ref_id is indeed a referee
	if current_user.access is not AccessLevel.referee:
		return jsonify({'message' : 'Invalid access level, needs a referee'}), 401
			
	# connects to the database
	conn = mysql.connect()
	cursor = conn.cursor()

	# calls for the update_ref_schedule procedure
	try: 
		cursor.callproc('post_ref_schedule',[ref_id, game_id])
	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1452: 
			return  jsonify ({'message': 'game_id or referee_id does not exist'}), 400
		if errno == 1062: 
			return  jsonify ({'message': 'That referee_id is already scheduled to that game_id'}), 400
		
	return jsonify({'message': 'Successfully scheduled a referee to a game'}), 201 #created


@schedule.route('/league/', methods=['GET'])
def get_league_schedule():
	# retrieve query string parameters from URL
	league_id = request.args.get('leagueID', default = None, type = int)
	season_id = request.args.get('seasonID', default = None, type = int)
	

	# error check: ensure that league_id is provided
	if league_id is None and season_id is None:
		return jsonify({'message': 'The leagueID and seasonID must be provided'}), 400 #bad request
	if league_id is None:
		return jsonify({'message': 'The leagueID must be provided'}), 400
	if season_id is None:
		return jsonify({'message': 'The seasonID must be provided'}), 400

	# connect to sql database and call get_player_stat stored procedure
	conn = mysql.connect()
	cursor = conn.cursor()
	
	#make sure the request is valid
	try:
		cursor.callproc('get_league_schedule', [league_id, season_id])
	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1644:
			return  jsonify ({'message': err.args[1]}), 400
		if errno == 1054:
			return  jsonify ({'message': 'No games scheduled for that League and Season'}), 400

	data = cursor.fetchall()

	#make sure data is not empty
	if not data:
		return jsonify({'message' : 'No games scheduled for that league and season'}), 404 #url not found
	
	games_list = []

	#iterate through data and populate games_list
	for i in range(0, len(data)):
		items = {
			'date_time':data[i][1],
			'away_team': {
				'team_id': data[i][2],
				'score': data[i][3]
			},
			'home_team': {
				'team_id': data[i][4],
				'score': data[i][5]
			},
			'game_id': data[i][6],
			'location': data[i][7]
		}
		games_list.append(items)
	
	#create dictionary to be jsonified
	schedule_dict = {
		"league_name": data[0][0],
		"games": games_list
	}
	
	return jsonify(schedule_dict), 200
