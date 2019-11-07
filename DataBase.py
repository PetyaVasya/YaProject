import sqlite3
from sqlite3 import Error


class DataBase:

    def __init__(self, path):
        if self.open_db(path):
            self.cur.execute(
                "CREATE TABLE IF NOT EXIST parsers (id AUTOINCREMENT name TEXT attributes TEXT)")

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
        return self.cur.execute("SELECT * FROM parsers")

    def get_parser(self, id):
        return self.cur.execute("SELECT * FROM parsers WHERE id=?", (id,))

    def add_parser(self, name, attributes=None):
        self.cur.execute("INSERT INTO parsers (name, attributes) VALUES(?, ?)", (name, attributes,))
        self.con.commit()

    def delete_parser(self, id):
        self.cur.execute("DELETE FROM parsers WHERE id=" + str(id))
        self.con.commit()

    def update_parser(self, id, name, attributes="?"):
        self.cur.execute("UPDATE parsers SET name=?, attributes=? WHERE id=?", (name, attributes, id,))
        self.con.commit()
