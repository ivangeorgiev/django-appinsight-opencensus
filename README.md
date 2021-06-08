## Sample Django Web App

### SQLite database

Database is configured to be stored in system temp directory:

* use `TMP` environment variable if not empty
* otherwise use `TEMP` environment variables if not empty
* otherwise use `/tmp` directory as default.

## Development Setup

**Step 1.** Configure development environment

Create `.dev` directory. The directory is used for developer artifacts. A rule in the `.gitignore` instructs git to ignore the `.dev` directory.

Create a file `.dev/setenv.sh` which initializes the environment variables, used by the app. A rule in the `.gitignore` instructs git to ignore the `.dev` directory. 

```bash
export DJANGO_SECRET_KEY='DjangoSecretKey'
export APPINSIGHTS_INSTRUMENTATION_KEY='<instrumentation-key>'
```

Update the environment, using the `.dev/setnenv.sh`:

```bash
$ source .dev/setenv.sh
```

**Step 2.** Create Python Virtual Environment

```bash
$ py -3.8 -m venv .venv38
$ source .venv38/Scripts/activate
```



**Step 3.** Install Python Dependencies

```bash
$ pip install -r requirements.txt
```

**Step 4.** Initialize Django Database

```bash
$ python manage.py makemigrations
$ python manage.py migrate
```

**Step 5.** Run Django web server

```bash
$ python manage.py runserver
```



## Highlights

Endpoints:

* /dt - shows current date time
  Purpose: See in App Insights
* /exc - throws unhandled exception
  Purpose: See how it is logged in App Insights



## Custom Azure App Service Startup Command

```
python manage.py makemigrations; python manage.py migrate; GUNICORN_CMD_ARGS="--timeout 600 --access-logfile '-' --error-logfile '-' --bind=0.0.0.0:8000" gunicorn mysite.wsgi
```



Create superuser from shell

```
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'password')" | python manage.py shell


```

As of Django 3.0 you can use default `createsuperuser --noinput` command and set all required fields (including password) as environment variables `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` for example. `--noinput` flag is required.

```
DJANGO_SUPERUSER_PASSWORD=password; python manage.py createsuperuser --noinput --username admin --email some.user.non.existent122@gmail.com; 
```



# Reference

* [Set up Azure Monitor for your Python application](https://docs.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python)
* opencensus-ext-django [Python package](https://pypi.org/project/opencensus-ext-django/) and [GitHub repository.](https://github.com/census-instrumentation/opencensus-python/tree/master/contrib/opencensus-ext-django)
* [OpenCensus project](https://opencensus.io/)
* [Configure a Linux Python app for Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/configure-language-python)