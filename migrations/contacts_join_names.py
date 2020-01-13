"""This migrates the contacts table from having first_name and last_name
(last commit 6354614) to only having name."""

import datetime
import sqlite3

from app import app
from teknologkoren_se import models

conn = sqlite3.connect('instance/db.sqlite')
conn.row_factory = sqlite3.Row
c = conn.cursor()


def migration():
    c.execute('SELECT * FROM contact')
    contacts = c.fetchall()

    c.execute('DROP TABLE contact')
    conn.commit()  # commit before sqlalchemy creates table

    models.db.create_all()

    for contact in contacts:
        name = "{} {}".format(contact[2], contact[3])
        c.execute(
            'INSERT INTO contact VALUES (?, ?, ?, ?, ?, ?)',
            (contact[0], contact[1], name, contact[4], contact[5], contact[6])
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    with app.app_context():
        migration()
