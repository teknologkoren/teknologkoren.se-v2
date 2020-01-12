# teknologkoren.se-v2
## Setup a development environment
Create a virtual environment:

```sh
python3 -m venv venv
```

Activate the environment:

```sh
. venv/bin/activate
```

Now you may either use `pip` directly to install the dependencies, or
you can install `pip-tools`. The latter is recommended.

### pip

```sh
pip install -r requirements.txt
```


### pip-tools
[pip-tools](https://github.com/jazzband/pip-tools) can keep your virtual
environment in sync with the `requirements.txt` file, as well as compiling a
new `requirements.txt` when adding/removing a dependency in `requirements.in`.

```sh
pip install pip-tools
pip-compile  # only necessary when adding/removing a dependency
pip-sync
```


### Populating a mock database
```sh
flask populatetestdb
```
This will populate the database with some mock data. Posts, events and pages
are generated from some paragraphs of "lorem ipsum" and a bit of random
"logic".


### Create an admin user
```sh
flask createadmin
```
You will be prompted for a username and password.


## Migrations
From the root directory, run
```sh
python3 -m migrations.<name_of_migration>
```
As it is run as a module, do not include the file extension (`.py`).
