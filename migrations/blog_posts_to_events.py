"""Converts four concert blog posts to events.

The concerts "95-årsjubileum: Biljettsläpp!" (2025), "Julkonsert - nu
finns biljetter att köpa!" (2025), "Solnedgång i öst" and "Civilization"
(2026) were added as blog posts, but they are concerts and belong on
/konserter with a start time and location.

The times in the post texts are Stockholm local time; start_time is
stored in UTC, the same way the admin interface saves it. Note that the
28 March 2026 concert takes place the day before the DST transition and
is therefore UTC+1, unlike the May concert (UTC+2). The jubilee post
does not mention the concert date itself; it comes from the preceding
save-the-date post (id 68).
"""

import sqlite3

conn = sqlite3.connect('instance/db.sqlite')
conn.row_factory = sqlite3.Row
c = conn.cursor()

EVENTS = [
    (
        70,
        '95-årsjubileum: Biljettsläpp!',
        '2025-10-11 14:00:00.000000',  # 11 okt 2025 16:00 CEST
        'Adolf Fredriks kyrka',
        'https://maps.app.goo.gl/vjGDE4Zhivir9BLf6',
    ),
    (
        72,
        'Julkonsert - nu finns biljetter att köpa!',
        '2025-12-07 17:00:00.000000',  # 7 dec 2025 18:00 CET
        'Adolf Fredriks kyrka',
        'https://maps.app.goo.gl/vjGDE4Zhivir9BLf6',
    ),
    (
        74,
        'Solnedgång i öst',
        '2026-03-28 18:00:00.000000',  # 28 mars 2026 19:00 CET
        'S:t Peters kyrka',
        'https://maps.app.goo.gl/vBL3EZkWdziNNLMAA',
    ),
    (
        75,
        'Civilization – Kongl. Teknologkören',
        '2026-05-23 17:00:00.000000',  # 23 maj 2026 19:00 CEST
        'Kungsholms kyrka',
        'https://maps.google.com/?q=Kungsholms+kyrka,+Stockholm',
    ),
]


def migrate():
    for post_id, title_sv, start_time, location, location_link in EVENTS:
        c.execute('SELECT type, title_sv FROM post WHERE id = ?', (post_id,))
        post = c.fetchone()

        if post is None:
            raise SystemExit(f'Post {post_id} does not exist, aborting.')
        if post['title_sv'] != title_sv:
            raise SystemExit(
                f'Post {post_id} is "{post["title_sv"]}", expected '
                f'"{title_sv}", aborting.'
            )
        if post['type'] != 'blog_post':
            raise SystemExit(
                f'Post {post_id} has type "{post["type"]}", expected '
                '"blog_post" — already migrated? Aborting.'
            )

        c.execute(
            'UPDATE post SET type = ? WHERE id = ?',
            ('event', post_id)
        )
        c.execute('DELETE FROM blog_post WHERE id = ?', (post_id,))
        c.execute(
            'INSERT INTO event (id, start_time, time_text_sv, time_text_en,'
            ' location_sv, location_en, location_link)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?)',
            (post_id, start_time, '', '', location, location, location_link)
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    migrate()
