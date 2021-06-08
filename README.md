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



