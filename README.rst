lineage_app
===========

a `Django <https://www.djangoproject.com>`_ web app interface for `lineage <https://github.com/apriha/lineage>`_

Requirements
------------
- `Python 3 <https://www.python.org>`_
- `SQLite <https://www.sqlite.org/index.html>`_
- `Redis <https://redis.io>`_

Quick Start
-----------
Follow these steps to get ``lineage_app`` up and running locally for development and/or debugging:

- Clone or download this repository
- Install `Pipenv <https://github.com/pypa/pipenv>`_
- ``cd`` to the top level of the repository (i.e., the top most ``lineage_app`` directory)
- Install the requirements for local development

  - ``$ pipenv install --dev``

- Make the migrations

  - ``$ pipenv run python manage.py migrate``
  - ``db.sqlite3`` will be created and used for the database

- Run ``celery`` in a Terminal

  - ``$ pipenv run celery worker --workdir="$PWD" --app=lineage_app.taskapp --loglevel=info``
  - ``celery`` handles the long-running tasks

- Run the web server in a different Terminal

  - ``$ pipenv run python manage.py runserver``
  - ``lineage_app`` will be available at http://127.0.0.1:8000/

- Click the "Debug Login" link to start using the web app

Acknowledgements
----------------
This web app was made possible thanks to a project grant from `Open Humans <https://www.openhumans.org>`_.
🎉

License
-------
Copyright (C) 2019 Scedastic Software, LLC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
