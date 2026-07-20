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
