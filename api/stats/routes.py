from flask import Blueprint, jsonify, request
from api.models import login_required, User, AccessLevel
from api import mysql
import pymysql

# all endpoint under stats Blueprint share common url root of /stats
stats = Blueprint('stats', __name__)

#public route
@stats.route('/league/', methods = ['GET'])
def get_standings():
	#get values from the query parameters
	league = request.args.get('leagueID', default = None, type = int)
	season = request.args.get('seasonID', default = None, type = int)

	#control to make sure both the season and league are passed as query parameters
	if season is None and league is None:
		print('error SEASON and LEAGUE parmeters not provided')
		return jsonify({'message' : 'season and league parmaeters not provided'}), 400
	elif season is None:
		print('error SEASON parameter not provided')
		return jsonify({'message' : 'season parmeter not provided'}), 400
	elif league is None:
		print('error LEAGUE parameter not privided')
		return jsonify({'message' : 'league parmeter not provided'}), 400
	
	#connect to the database
	conn = mysql.connect()
	cursor = conn.cursor()
	
	#run stored procedure and check for errors
	try:
		cursor.callproc('get_standings', [league,season])
	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1644: 
			return  jsonify ({'message': 'Not a valid league and season combination'}), 400
		


	data = cursor.fetchall()
	
	#print data to terminal to confirm values
	print(data)
	
	#generate list of results from the database
	standings_list = []
	for i in range(0, len(data)):
		items = {
			'team_id': data[i][0],
			'team_name': data[i][1],
			'games_played': data[i][2],
			'wins': data[i][3],
			'losses': data[i][4],
			'win_percentage': data[i][5],
			}
		standings_list.append(items)
	
	#put the list into a dictionary so it can be used by jsonify
	standings_dict = {
		'standings' : standings_list
	}
	return jsonify(standings_dict), 200
	
	
@stats.route('/player/', methods=['GET'])
def get_player_stat():
	# retrieve query string parameters from URL
	season_id = request.args.get('season_id', default = None, type = int)
	player_id = request.args.get('player_id', default = None, type = int)
	league_id = request.args.get('league_id',  default = None, type = int)

	# error check: ensure that player_id is provided
	if player_id is None:
		return jsonify({'message': 'The player_id must be provided'}), 400

	# connect to sql database and call get_player_stat stored procedure
	conn = mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('get_player_stat', [season_id, player_id, league_id])
	data = cursor.fetchall()

	# map procedure output to a list
	seasons_list = []
	for i in range(0, len(data)):
		items = {
			'season_id': data[i][6],
			'first_name': data[i][0],
			'last_name': data[i][1],
			'points': float(data[i][2]),
			'fouls': float(data[i][3]),
			'rebounds': float(data[i][4]),
			'assists':  float(data[i][5])
		}
		seasons_list.append(items)
	
	# store list into a dictionary
	seasons_dict = {
		"seasons" : seasons_list
	}
	return jsonify(seasons_dict)


@stats.route('/team/', methods=['GET'])
def get_team_stat():
	# retrieve query string parameters from URL
	season_id = request.args.get('season_id', default = None, type = int)
	league_id = request.args.get('league_id',  default = None, type = int)
	team_id = request.args.get('team_id', default = None, type = int)

	# error check: ensure that player_id is provided
	if team_id is None:
		return jsonify({'message': 'The team_id must be provided'}), 400

	# connect to the database
	conn = mysql.connect()
	cursor = conn.cursor()

	try:
		cursor.callproc('get_team_stat', [season_id, league_id, team_id])
		data = cursor.fetchall()

		# map procedure output to a list
		seasons_list = []
		for i in range(0, len(data)):
			items = {
				'season_id': data[i][0],
				'wins': float(data[i][1]),
				'losses': float(data[i][2]),
				'win_percentage': float(data[i][3]),
			}
			seasons_list.append(items)				
		
		seasons_dict = {
			"seasons" : seasons_list
		}

		return jsonify(seasons_dict)

	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1644: 
			return  jsonify ({'message': 'Team does not play specified with league and season'}), 400

	


@stats.route('/player/', methods=['PUT'])
@login_required
def update_player_stat(current_user):
    # retrieve query string parameters from URL and player id from current_user
	player_id = current_user.user_id
	game_id = request.args.get('game_id', default = None, type = int)
	points = request.args.get('points', default = None, type = int)
	fouls = request.args.get('fouls',  default = None, type = int)
	rebounds = request.args.get('rebounds',  default = None, type = int)
	assists = request.args.get('assists',  default = None, type = int)

	# error check: ensure that game_id is not null
	if (game_id is None):
		return jsonify({'message': 'The game_id must be provided'}), 400

	# error check: ensure that player_id is indeed a player
	if current_user.access is not AccessLevel.player:
		return jsonify({'message' : 'Invalid access level, needs a player'}), 401
			
	# connects to the database
	conn = mysql.connect()
	cursor = conn.cursor()

	# calls for the update_ref_schedule procedure
	try: 
		cursor.callproc('update_player_stat',[player_id, game_id, points,fouls, rebounds, assists])
	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1644: 
			return  jsonify ({'message': 'You do not play in a game specified with game_id'}), 400
	
	return jsonify({'message': 'Successfully updated the player stats'}), 201


@stats.route('/game/', methods=['PUT'])
@login_required
def update_game_stat(current_user):
    # retrieve query string parameters from URL and ref id from current_user
	ref_id = current_user.user_id
	game_id = request.args.get('game_id', default = None, type = int)
	home_score = request.args.get('home_score', default = None, type = int)
	away_score = request.args.get('away_score',  default = None, type = int)

	# error check: ensure that game_id is not null
	if (game_id is None):
		return jsonify({'message': 'The game_id must be provided'}), 400

	# error check: ensure person inputting is indeed a referee
	if current_user.access is not AccessLevel.referee:
		return jsonify({'message': 'Invalid access level, needs a referee'}), 401
 
	# connects to the database
	conn = mysql.connect()
	cursor = conn.cursor()

    # calls for the update_game_stat procedure
	try: 
		cursor.callproc('update_game_stat',[ref_id, game_id, home_score, away_score])
	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1644:
			return  jsonify ({'message': 'You are not scheduled to the game specified with gameID'}), 400
    
	return jsonify({'message': 'Successfully updated the game stats'}), 201


@stats.route('/game/', methods=['GET'])
def get_game_stats():
	game_id = request.args.get('gameID', default = None, type = int)
	
	#error check: ensure the gameID is provided
	if game_id is None:
		return jsonify({'message': 'The game_id must be provided'}), 400
	
	# connect to database
	conn = mysql.connect()
	cursor = conn.cursor()

	# check for sql errors
	try:
		cursor.callproc('get_game_stats', [game_id])
		
	except pymysql.MySQLError as err:
		errno = err.args[0]
		print(f'Error number: {errno}')
		if errno == 1644: 
			return  jsonify ({'message': err.args[1]}), 400

	# retrieve data from the sql query
	data = cursor.fetchall()
	
	stats_list = []
	
	#iterate through data and populate stats_list
	for i in range(0, len(data)):
		items = {
			'home_team_name': data[i][0],
			'home_team_id': data[i][1],
			'home_team_score': data[i][2],
			'away_team_name': data[i][3],
			'away_team_id': data[i][4],
			'away_team_score': data[i][5]
		}
		stats_list.append(items)

	#put the data into a dictionary to be turned into json
	game_stats_dict = {
		'stats': stats_list
	}

	return jsonify(game_stats_dict)