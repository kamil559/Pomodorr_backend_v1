Basic setup
===========

In order to recreate the structure of .envs directory that the project uses, start with creating the .envs directory in
the root of the project, as it is done below.

::

    pomodorr
    ├── .envs
    │   ├── .local
    │       ├── .django
    │       ├── .postgres
    │   └── .production
    │       ├── .django
    │       ├── .postgres

Configure environment variables
-------------------------------
The configurations listed below resemble the default environment setting files needed to set the project up:

- | **local envs**:
  ``pomodorr/.envs/.local/.django``
    | # General
    | USE_DOCKER=yes
    | IPYTHONDIR=/app/.ipython
    | DJANGO_SETTINGS_MODULE=config.settings.local

    | # Redis
    | REDIS_URL=redis://redis:6379/0

    | # Celery / Flower
    | CELERY_FLOWER_USER=<your_celery_flower_user>
    | CELERY_FLOWER_PASSWORD=<your_celery_flower_password>

  ``pomodorr/.envs/.local/.postgres``
    | # PostgreSQL
    | POSTGRES_HOST=postgres
    | POSTGRES_PORT=5432
    | POSTGRES_DB=pomodorr
    | POSTGRES_USER=<your_postgres_user>
    | POSTGRES_PASSWORD=<your_postgres_password>

- | **production envs**:
  ``pomodorr/.envs/.production/.django``
    | # General
    | # DJANGO_READ_DOT_ENV_FILE=True
    | DJANGO_SETTINGS_MODULE=config.settings.production
    | DJANGO_SECRET_KEY=<your_secret_key>
    | DJANGO_ADMIN_URL=<your_admin_url>
    | DJANGO_ALLOWED_HOSTS=<your_hosting_domain>

    | # Security
    | # TIP: better off using DNS, however, redirect is OK too
    | DJANGO_SECURE_SSL_REDIRECT=False

    | # Email
    | MAILGUN_API_KEY=<your_mailgun_api_key>
    | DJANGO_SERVER_EMAIL=<your_server_email>
    | MAILGUN_DOMAIN=<your_mailgun_domain>

    | # AWS
    | DJANGO_AWS_ACCESS_KEY_ID=<your_aws_access_key_id>
    | DJANGO_AWS_SECRET_ACCESS_KEY=<your_aws_secret_access_key>
    | DJANGO_AWS_STORAGE_BUCKET_NAME=<your_aws_storage_bucket_name>

    | # Gunicorn
    | WEB_CONCURRENCY=4

    | # Sentry
    | SENTRY_DSN=<your_sentry_dsn>


    | # Redis
    | REDIS_URL=redis://redis:6379/0


    | # Celery / Flower
    | CELERY_FLOWER_USER=<your_celery_flower_user>
    | CELERY_FLOWER_PASSWORD=<your_celery_flower_password>
  ``pomodorr/.envs/.production/.postgres``
    | # PostgreSQL
    | POSTGRES_HOST=postgres
    | POSTGRES_PORT=5432
    | POSTGRES_DB=pomodorr
    | POSTGRES_USER=<your_postgres_user>
    | POSTGRES_PASSWORD=<your_postgres_password>


Building and running containers
-------------------------------

The details about getting the project up and running is described on the official django-cookiecutter `documentation <https://cookiecutter-django.readthedocs.io/en/latest/developing-locally-docker.html>`_.

Having configured the environment variables all there is left to do is to build the docker containers and run them.
Assuming your current directory is the root directory of the project, type:

.. code-block:: bash

   $ docker-compose -f local.yml build

The last step is to get the containers up.

.. code-block:: bash

    $ docker-compose -f local.yml up

.. note::
   | You may encounter some problems with already used ports. In that situation, check the ``pomodorr/local.yml`` configuration file and change the clashing ports.
   | Likewise, in case of having troubles with setting the project up, please consider having a look at the `troubleshooting <https://cookiecutter-django.readthedocs.io/en/latest/troubleshooting.html>`_ page of the official django-cookiecutter documentation.
   | Otherwise feel free to send an email message or report an issue on the `github <https://github.com/kamil559/pomodorr>`_ if there is an evidence of a bug.


Building documentation with sphinx and sphinx-apidoc
----------------------------------------------------

Assuming your current directory is ``pomodorr/docs``, in order to generate the apidoc out of your docstrings, execute:

.. code-block:: bash

   $ sh apidoc.sh

Having done that, in order to generate the html pages, type:

.. code-block:: bash

   $ make html