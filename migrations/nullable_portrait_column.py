"""Converts the Image type to a File-type Image"""

import sqlite3

from app import app
from teknologkoren_se import models

conn = sqlite3.connect('instance/db.sqlite')
conn.row_factory = sqlite3.Row
c = conn.cursor()


def migrate():
    c.execute('SELECT id, filename, portrait, type FROM file')
    files = c.fetchall()

    c.execute('DROP TABLE file')
    conn.commit()
    conn.close()

    with app.app_context():
        models.db.create_all()

        for file in files:
            if file['type'] == 'image':
                im = models.Image(
                    id=file['id'],
                    filename=file['filename'],
                    portrait=file['portrait']
                )
                models.db.session.add(im)
            else:
                f = models.File(
                    id=file['id'],
                    filename=file['filename']
                )
                models.db.session.add(f)

            models.db.session.commit()


if __name__ == "__main__":
    migrate()
