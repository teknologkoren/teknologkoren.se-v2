# teknologkoren.se-v2
## Setup a development environment
Dependencies are managed with [uv](https://docs.astral.sh/uv/), which
also installs a suitable Python and creates the virtual environment
for you:

```sh
uv sync
```

Prefix commands with `uv run` to run them inside the environment (or
activate it with `. .venv/bin/activate`). Add or remove dependencies
with `uv add <package>` / `uv remove <package>`; the resolved versions
are pinned in `uv.lock`.

### Running the tests
```sh
uv run pytest
uv run ruff check .
```


### Populating a mock database
```sh
uv run flask initdb
uv run flask populatetestdb
```
This will create the database and populate it with some mock data. Posts,
events and pages are generated from some paragraphs of "lorem ipsum" and
a bit of random "logic".


### Running a test instance
```sh
FLASK_DEBUG=1 uv run flask run
```

Alternatively, you can run the app in Docker against your working tree
(gunicorn with live reload) using the development compose override:

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```
This is reachable on `http://127.0.0.1:8001/`.


### Create an admin user
```sh
uv run flask createadmin
```
You will be prompted for a username and password.


## Migrations
From the root directory, run
```sh
uv run python -m migrations.<name_of_migration>
```
As it is run as a module, do not include the file extension (`.py`).


## Deployment
In production the site runs with gunicorn (`gunicorn -w 3 app:app`) as a
systemd service, from a virtual environment created by uv. Docker is not
used in production. On the server, put the production configuration in
`instance/config.py` (`DEBUG = False`, secret key, `SERVER_NAME`,
`SESSION_COOKIE_SECURE = True`, database path under `instance/` — note
the checked-in default config sets `DEBUG = True`). To deploy a new
version:

```sh
git pull
uv sync --locked --no-dev
```

and then restart the service.

nginx on the host terminates TLS, proxies to gunicorn, and serves
`teknologkoren_se/static/` (including the `img<width>/` resizing
locations) directly from the repository checkout. The database
(`instance/`) and uploads (`teknologkoren_se/static/uploads/`) are plain
files in the checkout.

Run one-off commands (e.g. a migration or `flask createadmin`) from the
checkout with the environment's executables:

```sh
.venv/bin/flask createadmin
.venv/bin/python -m migrations.<name_of_migration>
```
