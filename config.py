from pathlib import Path

DEBUG = True
SECRET_KEY = 'super secret secret'

SERVER_NAME = 'localhost.localdomain:5000'

BASEDIR = Path(__file__).parent.resolve()

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASEDIR.joinpath('db.sqlite'))

# FSADeprecationWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant
# overhead and will be disabled by default in the future. Set it to
# True or False to suppress this warning.
SQLALCHEMY_TRACK_MODIFICATIONS = False

UPLOADS_DEFAULT_DEST = BASEDIR.joinpath('teknologkoren_se/static/uploads')
UPLOADS_DEFAULT_URL = '/static/uploads/'

WTF_CSRF_TIME_LIMIT = 21600  # 6 hours
