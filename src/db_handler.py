import sqlite3


class DatabaseHandler:
    def __init__(self):
        self.con = sqlite3.connect("parking.db")

    def get_current_occupation(self):
        pass

    def write_occupation(self, id, occupation):
        pass


if __name__ == "__main__":
    DatabaseHandler().get_current_occupation()
