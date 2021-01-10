from flask import Blueprint, jsonify, request
from api.models import login_required, User, AccessLevel
from api import mysql
import pymysql

# all endpoints under team will start with /team
teams = Blueprint('teams', __name__)

# implements the POST register team endpoint as documented in the Postman collection
@teams.route('/', methods = ['POST'])
@login_required
def register_team(current_user: User):
    req = request.json

    # retrieve JSON body fields
    team_name = req.get('team_name')
    league_id = req.get('league_id')

    #check access level
    if current_user.access is not AccessLevel.player:
        return jsonify({'message' : 'This end point is for players'}), 400
    
    conn = mysql.connect()
    cursor = conn.cursor()

    # call register_team stored proc and error handle
    try: 
        cursor.callproc('register_team', [team_name, current_user.user_id, league_id])
        data = cursor.fetchall()
        print(f'Got: {data}')
    except pymysql.MySQLError as err:
        errno = err.args[0]
        
        if errno == 1452:
            return  jsonify ({'message': 'Provided league_id or player_id does not exist'}), 400
        if errno == 1062: 
            if ("unique_player_per_season" in err.args[1]):
                return  jsonify ({'message': 'The team captain is already registered in this league so they can not register in it again.'}), 400
            
            return  jsonify ({'message': 'That team name is already taken'}), 400
        else: 
            print(f'Error number: {errno}, Error: {err.args[1]}')
            return  jsonify ({'message': 'Something went wrong'}), 500
        
    return jsonify({'message' : 'Team registered OK'}), 201


#implements PUT update team end point as documented in Postman collection
@teams.route('/', methods = ['PUT'])
@login_required
def update_team(current_user: User):
    req = request.json

    # ensure appropriate user level
    if current_user.access is not AccessLevel.admin:
        return jsonify({'message' : 'You dont have valid access level, only admin can do this'}), 401
    
    conn = mysql.connect()
    cursor = conn.cursor()

    # call update_team stored proc that updates fee payments and changing captains and duplicaiton error handle
    try: 
        cursor.callproc('update_team', [req.get('team_id'), req.get('captain_id'), req.get('fee_payment', {}).get('league_id'), req.get('fee_payment', {}).get('season_id'), req.get('fee_payment', {}).get('date_paid', None)])
    except pymysql.MySQLError as err:
        errno = err.args[0]
        
        if errno == 1452: 
            return  jsonify ({'message': 'Provided league_id or player_id does not exist'}), 400
        if errno == 1062: 
            return  jsonify ({'message': 'That team name is already taken'}), 400
        else: 
            print(f'Error number: {errno}, Error: {err.args[1]}')
            return  jsonify ({'message': 'Something went wrong'}), 500
    
    # retrieve list of league to be registered for from the body of the request this way even the team is not allowed 
    # to register in one of the leagues, the others in the list will still be attempted
    new_leagues = req.get('league')
    if new_leagues:
        failed_leagues = []

        #handle each league in the list individually
        for new_league in new_leagues:
            print(f'Adding: {new_league}')

            # call register_for_league stored proc that register a team in the league provided and error duplicate errors
            try:
                cursor.callproc('register_for_league', [new_league.get('league_id'), req.get('team_id'), None])
            except pymysql.MySQLError as err: 
                errno = err.args[0]

                if errno == 1062:
                    failed_leagues.append(new_league.get('league_id'))
                else:
                    print(f'Error number: {errno}, Error: {err.args[1]}')
                    return  jsonify ({'message': 'Something went wrong'}), 500
        
        #if any league failed return appropriate error message
        if failed_leagues:
            return  jsonify ({'message': f'That team is already registered in the following leagues: {failed_leagues}, otherwise OK.'}), 200
    return jsonify({'message' : 'Everything was OK.'}), 201    


#implements PUT update team roster endpoint for captains as documented in the Postman collection
@teams.route('/roster/', methods = ['PUT'])
@login_required
def update_team_roster(current_user: User):
    req = request.json
    
    conn = mysql.connect()
    cursor = conn.cursor()

    # check with the db that the user editing the team is actually the team captain. Unlike other access information, this info
    # is not contained in the JWT so a call to the db must be made
    cursor.callproc('get_team_captain', [req.get('team_id')])
    data = cursor.fetchall()

    if len(data) != 1:
        return jsonify({'message' : 'Invalid team ID'}), 400

    if data[0][0] != current_user.user_id:   #if current use is not a captain deny access
        return jsonify({'message' : f'Only a captain can do this. Contact {data[0][1]} {data[0][2]} at {data[0][3]}'}), 401
    
    # call update_team_by_captain stored proc which is able to change team captain as well as the team name. Erro handle duplicates
    try:
        cursor.callproc('update_team_by_captain', [req.get('team_id'), req.get('captain_id'), req.get('team_name')])
    except pymysql.MySQLError as err: 
        errno = err.args[0]
        print(f'Error number {errno}, Error: {err.args[1]}')


    # only perform roster change if a new roster list was provided
    if req.get('roster'): 

        # keep track of player id's that couldn't be placed on the team due to roster constaints
        players_failed = []

        # handle each new player individually so that a failure to register one player doesnt cause a failure in the whole proc call
        for new_player in req.get('roster'):

            # call update_team_roster proc that put a  giver player on the team, in case of SQL error add the player to this list of failed player updater
            try:
                cursor.callproc('update_team_roster', [req.get('team_id'), new_player.get('player_id')])
            except pymysql.MySQLError as err:
                errno = err.args[0]

                if errno == 1062:
                    players_failed.append(new_player.get('player_id'))
                
                elif errno == 1452:
                    players_failed.append(new_player.get('player_id'))
                else:
                    print(f'Error number {errno}, Error: {err.args[1]}')
                    return jsonify({'message' : 'Something went wrong...'}), 500
        
        # notify caller of any failed updates
        if players_failed:
            return  jsonify ({'message': f'Players are already registered in this league, maybe on a different team: {players_failed} (they may not be players), otherwise OK.'}), 200
    
    return jsonify({'message' : 'Updates successful'}), 201  