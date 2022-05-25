"""Converts the Image type to a File-type Image"""

import sqlite3

from app import app
from teknologkoren_se import models

conn = sqlite3.connect('instance/db.sqlite')
conn.row_factory = sqlite3.Row
c = conn.cursor()


def migrate():
    c.execute('SELECT id, filename, portrait FROM image')
    images = c.fetchall()

    c.execute('DROP TABLE image')
    conn.commit()
    conn.close()

    with app.app_context():
        models.db.create_all()

        for image in images:
            im = models.Image(
                id=image['id'],
                filename=image['filename'],
                portrait=image['portrait']
            )
            models.db.session.add(im)
            models.db.session.commit()


if __name__ == "__main__":
    migrate()
