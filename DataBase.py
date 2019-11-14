import sqlite3
from sqlite3 import Error


class DataBase:

    def __init__(self, path):
        if self.open_db(path):
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS parsers (id integer PRIMARY KEY AUTOINCREMENT,"
                " name TEXT, url TEXT, attributes TEXT, linkstype INTEGER, filepath TEXT,"
                " respath TEXT)")

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

    def add_parser(self, name, url=None, attributes=None, type=None, filepath=None, respath=None):
        self.cur.execute(
            "INSERT INTO parsers (name, url, attributes, linkstype, filepath, respath)"
            " VALUES(?, ?, ?, ?, ?, ?)",
            (name, url, attributes, type, filepath, respath,))
        self.con.commit()
        return self.get_lastrowid()

    def delete_parser(self, id):
        self.cur.execute("DELETE FROM parsers WHERE id=" + str(id))
        self.con.commit()

    def update_parser(self, id, name=None, url=None, attributes=None, type=None, filepath=None,
                      respath=None):
        self.cur.execute(
            ("UPDATE parsers SET " + ("name=?, " if name else "") + ("url=?, " if url else "") + (
                "attributes=?, " if attributes else "") + ("linkstype=?, " if type else "") + (
                 "filepath=?, " if filepath else "") + ("respath=?, " if respath else "") +
             " WHERE id=?").replace(",  WHERE", "WHERE"),
            tuple(filter(lambda x: x, (name, url, attributes, type, filepath, respath, id,))))
        self.con.commit()

    def get_lastrowid(self):
        return self.cur.lastrowid

    def execute(self, request):
        return self.cur.execute(request).fetchall()
