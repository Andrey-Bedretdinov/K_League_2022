import sqlite3


class DB:

    def __init__(self, file='server.db'):
        self.db = sqlite3.connect(file)
        self.cur = self.db.cursor()

    def check(self, table, columns=None):
        if columns is None:
            columns = ['id INT']

        s = ''
        for column in columns:
            s += column + ', '
        s = s.strip(', ')

        self.cur.execute(f'CREATE TABLE IF NOT EXISTS {table} ({s})')
        self.db.commit()

    def get_data(self, table):
        result = []
        columns = []
        for i in self.cur.execute(f'PRAGMA table_info({table})'):
            columns.append(i[1])

        data = list(self.cur.execute(f'SELECT * FROM {table}'))
        if type(data) == list:
            for i in data:
                string = {}
                for j in range(len(i)):
                    string[columns[j]] = i[j]
                result.append(string)
            return result

    def add_elem(self, table, strings: list = None, values: list = None):
        if values:
            s = ""
            for value in values:
                if type(value) == str:
                    s += f"'{value}', "
                else:
                    s += f'{value}, '
            s = s.strip(', ')
            self.cur.execute(f'INSERT INTO {table} VALUES ({s})')
        if strings:
            for string in strings:
                s = ""
                for value in string:
                    if type(value) == str:
                        s += f"'{value}', "
                    else:
                        s += f'{value}, '
                s = s.strip(', ')
                self.cur.execute(f'INSERT INTO {table} VALUES ({s})')
        self.db.commit()

    def del_elem(self, table, key, value):
        if type(value) is str:
            value = f"'{value}'"
        self.cur.execute(f"DELETE FROM {table} WHERE {key} = {value}")
        self.db.commit()

    def del_table(self, table):
        self.cur.execute(f'DROP TABLE {table}')
        self.db.commit()

    def __del__(self):
        self.db.close()
