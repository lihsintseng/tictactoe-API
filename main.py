from flask import Flask, jsonify
from db import DataBase
import datetime, json, math
import numpy as np
from flask import request

app = Flask(__name__)


# Initializes the database.
def init_db():
    '''
    Check if 'games' and 'movements' table exist
    If the tables do not exist, they will be created. 
    '''
    db = DataBase()
    db.query_one("CREATE TABLE IF NOT EXISTS `games` ( "
             "`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
             "`size` INTEGER NOT NULL DEFAULT '3', "
             "`winner` INTEGER DEFAULT NULL, "
             "`create_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
             "`update_at` DATETIME DEFAULT NULL, "
             "`delete_at` DATETIME DEFAULT NULL) ")

    db.query_one("CREATE TABLE IF NOT EXISTS `movements` ( "
             "`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
             "`game_id` INTEGER NOT NULL, "
             "`position` INTEGER NOT NULL, "
             "`mark` INTEGER NOT NULL DEFAULT '2', "
             "`create_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "
             "`update_at` DATETIME DEFAULT NULL, "
             "`delete_at` DATETIME DEFAULT NULL) ")


# This method will create a new game with specified game size
@app.route('/game/new/', methods = ['POST'])
def create_new_game(game_size = 3):
    db = DataBase()
    game_size = request.args['game_size']
    if game_size == '':
        return jsonify({"status": "fail", "msg": "Game_size not specified.", "error_code": 4})
    game_size = int(game_size)
    # Game size must exceed 2
    if game_size < 2:
        return jsonify({"status": "fail", "msg": "Defined game size too small.", "error_code": 9})
    # Check if "game" table exists
    if db.query_one("SELECT COUNT(*) FROM `sqlite_master` WHERE type = 'table' AND name = 'games'")[0] != 1:
        return jsonify({"status": "fail", "msg": "Game table not found.", "error_code": 1})
    # create a new row in "game"
    db.query_one("INSERT INTO `games` (size) VALUES (?)", (game_size,))
    game_id = db.query_one("SELECT last_insert_rowid() FROM `games`")[0]
    return jsonify({"status": "success", "game_id": game_id})


# This method will delete the game with the specified game_id
@app.route('/game/', methods = ['DELETE'])
def delete_game(game_id = ''):
    db = DataBase()
    game_id = request.args['game_id']
    # return failure when the game_id is not specified
    if game_id == '':
        return jsonify({"status": "fail", "msg": "Game_id not specified.", "error_code": 3})
    #game_id = int(game_id)
    # return failure when there is not exist in the `games` table with the specified game_id
    if db.query_one("SELECT COUNT(*) FROM `games` WHERE id = ? AND delete_at IS NULL", (game_id,))[0] != 1 :
        return jsonify({"status": "fail", "msg": "Game with id (" + str(game_id) + ") is not found or has already been deleted.", "error_code": 2})
    datetime_now = datetime.datetime.now()
    db.query_one("UPDATE `games` SET update_at = ?, delete_at = ? WHERE id = ?", (datetime_now, datetime_now, game_id))
    return jsonify({"status": "success", "msg": "Specified game is deleted."})


# This method will return the informations of all existing games 
@app.route('/game/lists/all', methods = ['GET'])
def get_existing_games():
    db = DataBase()
    rows = db.query_all("SELECT id as game_id, size, winner, create_at FROM `games` ORDER BY id DESC")
    if len(rows) == 0:
        return jsonify({"status": "fail", "msg": "No existing games in `games` table.", "game": "NULL"})
    return json.dumps({"status": "success", "msg": "Successfully retrieved.", "games": rows})


# This method will return the informations of the game with a specific game_id
@app.route('/game/lists/', methods = ['GET'])
def get_game_status(game_id = ''):
    db = DataBase()
    game_id = request.args['game_id']
    # return failure when the game_id is not specified
    if game_id == '':
        return jsonify({"status": "fail", "msg": "Game_id not specified.", "game": "NULL", "error_code": 3})
    game_id = int(game_id)
    row = db.query_one("SELECT COUNT(*), id as game_id, size, winner, create_at FROM `games` WHERE id = ?", (game_id,))
    # return failure when there is not exist in the `games` table with the specific game_id
    if row[0] != 1:
        return jsonify({"status": "fail", "msg": "Game with id (" + str(game_id) + ") not found or has already been deleted.", "game": "NULL", "error_code": 2})
    return json.dumps({"status": "success", "msg": "Successfully retrieved.", "game": row})


# This method will record the moves in the "moves" table (o -> mark:1, x -> mark:0) and check if the game has come to an end
@app.route('/game/move/', methods = ['POST'])
def put_move(game_id = '', row = '', col = '', mark = ''):
    datetime_now = datetime.datetime.now()
    db = DataBase()
    game_id = request.args['game_id']
    row = request.args['row']
    col = request.args['col']
    mark = request.args['mark']
    # return failure when the game_id is not specified
    if game_id == '':
        return jsonify({"status": "fail", "msg": "Game_id not specified.", "error_code": 3})
    # return failure when the position is not specified
    if row == '' or col == '':
        return jsonify({"status": "fail", "msg": "Position not specified.", "error_code": 5})
    # return failure when the mark is not specified
    if mark == '' or not str(mark) in {'0', '1'}:
        return jsonify({"status": "fail", "msg": "Mark type not specified.", "error_code": 6})
    game_id = int(game_id)
    row = int(row)
    col = int(col)
    mark = int(mark)
    # Get the information of the specific game_id
    game = db.query_one("SELECT COUNT(*), id, size, winner FROM `games` WHERE id = ?", (game_id,))
    # return failure when there's no game in games table with the specified id
    if game[0] == 0:
        return jsonify({"status": "fail", "msg": "Game with id " + str(game_id) + " not found or has already been deleted.", "error_code": 2})
    # return failure when the position is larger or smaller than the created matrix
    if row > game[2] or col > game[2] or row < 1 or col < 1:
        return jsonify({"status": "fail", "msg": "Unqualified placement.", "error_code": 7})
    # covert 2 dimension position to 1 dimension position
    position_1dim = (row - 1) * game[2] + col;  
    # check whether the position is taken
    check_position_status = db.query_one("SELECT COUNT(*) FROM `movements` WHERE game_id = ? AND position = ?", (game_id, position_1dim))[0]
    if check_position_status == 1:
        return jsonify({"status": "fail", "msg": "Position already taken.", "error_code": 10})
    # add move operation into movements table
    db.query_one("INSERT INTO `movements` (game_id, position, mark, create_at) VALUES (?, ?, ?, ?)", (game_id, position_1dim, mark, datetime_now))
    db.query_one("UPDATE `games` SET update_at = ? WHERE id = ?", (datetime_now, game_id))
    # return jsonify({"status": "success", "msg": "Successfully inserted."})

    moves_in_game = db.query_all("SELECT position, mark FROM `movements` WHERE `game_id` = ?", (game_id,))
    # record the game (In board, x -> 0, o -> 1, null -> 2)
    board = [[2 for i in range(game[2])] for j in range(game[2])]
    for iterator in moves_in_game:
        r = int((iterator[0] - 1) / game[2]) + 1
        c = (iterator[0] - 1) % game[2]
        board[r - 1][c - 1] = iterator[1]
    board = np.array(board)
    # check if someone wins
    winner = ''
    if np.any(np.all(board == mark, axis = 0)) or np.any(np.all(board == mark, axis = 1)) \
    or np.all(np.array([board[x][x] for x in range(game[2])]) == 1, axis = 0): # check column
        winner = mark
    # check if it is a draw case
    if len(moves_in_game) == game[2]**2:
        winner = 2

    if winner != '':
        db.query_one("UPDATE `games` SET winner = ?, update_at = ? WHERE id = ?", (winner, datetime_now, game_id))
        if winner == 2:
            return jsonify({"status": "success", "msg": "Game end, draw.", "mark": mark})
        else:
            return jsonify({"status": "success", "msg": "Game end, winner side's mark is " + str(winner), "mark": mark})
    else:
        return jsonify({"status": "success", "msg": "Game continue.", "mark": mark})

if __name__ == '__main__':
    init_db() # Check whether the tables are not created. If not, create it.
    app.run(debug = True, use_evalex = False)
