import sqlite3
from sqlite3 import Error


class DataBase:

    def __init__(self, path):
        if self.open_db(path):
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS parsers (id integer PRIMARY KEY AUTOINCREMENT, name TEXT, url TEXT, attributes TEXT)")

    def open_db(self, path):
        self.db_path = path
        self.con = None
        try:
            self.con = sqlite3.connect(self.db_path)
            self.cur = self.con.cursor()
            return True
        except Error as e:
            print(e)
            return False

    def close(self):
        self.con.close()

    def get_parsers(self):
        return self.cur.execute("SELECT * FROM parsers").fetchall()

    def get_parser(self, id):
        return self.cur.execute("SELECT * FROM parsers WHERE id=?", (id,)).fetchone()

    def add_parser(self, name, url=None, attributes=None):
        self.cur.execute("INSERT INTO parsers (name, url, attributes) VALUES(?, ?, ?)", (name, url, attributes,))
        self.con.commit()
        return self.get_lastrowid()

    def delete_parser(self, id):
        self.cur.execute("DELETE FROM parsers WHERE id=" + str(id))
        self.con.commit()

    def update_parser(self, id, name, url=None, attributes=None):
        self.cur.execute("UPDATE parsers SET name=?, url=?, attributes=? WHERE id=?", (name, url, attributes, id,))
        self.con.commit()

    def get_lastrowid(self):
        return self.cur.lastrowid
