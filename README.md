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
new `requirements.txt` when adding a new dependency.

```sh
pip install pip-tools
pip-tools sync
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
