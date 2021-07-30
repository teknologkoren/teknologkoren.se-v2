"""Sets a unique constraint on AdminUser.username"""

import sqlite3

conn = sqlite3.connect('instance/db.sqlite')
conn.row_factory = sqlite3.Row
c = conn.cursor()


def migrate():
    c.execute(
        'CREATE UNIQUE INDEX adminuser_unique_username ON admin_user(username)'
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
