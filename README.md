## Sample Django Web App



## Development Setup

**Step 1.** Configure development environment

Create `.dev` directory. The directory is used for developer artifacts. A rule in the `.gitignore` instructs git to ignore the `.dev` directory. By default the SQLite database is also configured to be stored in this directory.

Create a file `.dev/setenv.sh` which initializes the environment variables, used by the app. A rule in the `.gitignore` instructs git to ignore the `.dev` directory. 

```bash
export DJANGO_SECRET_KEY='DjangoSecretKey'
export APPINSIGHT_INSTRUMENTATION_KEY='<instrumentation-key>'
export APPINSIGHT_CONNECTION_STRING="InstrumentationKey=$APPINSIGHT_INSTRUMENTATION_KEY;IngestionEndpoint=https://westeurope-5.in.applicationinsights.azure.com/"
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



