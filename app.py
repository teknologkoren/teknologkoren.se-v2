from pathlib import Path
from teknologkoren_se import factory

path = Path(__file__).parent.resolve()

instance_dir_name = 'instance'
instance_config_name = 'config.py'

# Create /instance and /instance/config.py if they do not exist
path.joinpath(instance_dir_name).mkdir(exist_ok=True)
instance_config = path.joinpath(instance_dir_name, instance_config_name)

if not instance_config.is_file():
    instance_config.touch()
    instance_config.write_text("""\
from pathlib import Path

DEBUG = True
SECRET_KEY = 'not the default secret!'

BASEDIR = Path(__file__).parent.resolve() # is now `instance/`

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASEDIR.joinpath('db.sqlite'))
""")

app = factory.create_app(instance_config='config.py')
