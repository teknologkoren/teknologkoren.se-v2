"""Adds multiple languages to flashes"""

import datetime
import sqlite3

from app import app
from teknologkoren_se import models

conn = sqlite3.connect('instance/db.sqlite')
conn.row_factory = sqlite3.Row
c = conn.cursor()


def migrate():
    c.execute('SELECT * FROM config')
    config = c.fetchone()

    c.execute('DROP TABLE config')
    conn.commit()  # commit before sqlalchemy creates table

    with app.app_context():
        models.db.create_all()

    c.execute(
        'INSERT INTO config VALUES (?, ?, ?, ?, ?)',
        (config[0], config[1], config[2], config[2], config[3])
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
