import sqlite3


class DataBase:
    def __init__(self):
        try:
            self.__conn = sqlite3.connect('data/db.sqlite')
        except Exception:
            print('Connection error.')

# Run a SQL query
    def query_one(self, query_statement, parameters = ()):
        rows = self.__conn.execute(query_statement, parameters)
        self.__conn.commit()
        return rows.fetchone()

# Run a SQL query
    def query_all(self, query_statement, parameters = ()):
        rows = self.__conn.execute(query_statement, parameters)
        self.__conn.commit()
        return rows.fetchall()