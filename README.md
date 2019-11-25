* Develop: [ ![Codeship Status for sevenpark/gotham](https://codeship.com/projects/4ac8bef0-1bdc-0134-8c85-22fb94432a98/status?branch=develop)](https://codeship.com/projects/159773)
* Master: [ ![Codeship Status for sevenpark/gotham](https://codeship.com/projects/4ac8bef0-1bdc-0134-8c85-22fb94432a98/status?branch=master)](https://codeship.com/projects/159773)

# Running Gotham locally for the first time

## Dependencies

First, make sure you have the following dependencies on your machine:

1. AWS CLI (**Must have defaults configured**)
2. Python 2.x environment
    1. Python 2.x
    2. Pip
    3. Virtualenv

**You are not yet finished setting up Gotham,** please keep reading.

## Setting up your environment

1. Set up your virtual environment in the standard way:
    1. `pip install virtualenv`
    2. `virtualenv venv`
    3. `source venv/bin/activate`
2. Install required packages:
    > `pip install -r requirements.txt`
3. Change paths in `cont_int/config/airflow_local.cfg` to be local, like:
    > `/Users/mmac/git/gotham/airflow` -> `/PATH/TO/THIS/REPO/airflow`.
    **Note that this path appears in multiple locations in the file.**
4. Set AIRFLOW_HOME environment variable:
    > `export AIRFLOW_HOME=/PATH/TO/THIS/REPO/airflow`
5. Initialize a local (SQL lite) database:
    > `airflow initdb`
6. Run local Airflow server (preferably in background or separate shell):
    > `airflow webserver`
    Ignore all warnings about missing connection definitions and variables. We
    will set these through the web interface in a second.
7. Go to `http://localhost:8080` to interact with local instance
8. Navigate to Admin > Connections to add the following connections.
   Set the values to be equal to the values of these connections in the
   production airflow server at http://airflow.7parkdata.com:8080/.
     1. `s3incoming`
     2. `s3`
     3. `company_dimensions`
     4. `redshift`
9. Repeat (8) but for Admin > Variables:
     1. `airflow_host` (**This should be set to `http://localhost:8080`**)
     2. `slack_access_token`
     3. `slack_channel_failed`
     4. `slack_channel_succeeded`

Note: when finished with development, remember to run command:
> `deactivate`

# Developing Gotham

## Runing Airflow tasks locally

To test run an individual task, use the `test` command:

`airflow test <DAG_ID> <TASK_ID> <START_DATE>`

Use a value of `-1` for `<START_DATE>` to run immediately.

Dag_ids and Task_ids are strings, not integers.

The name of the dag is what is displayed in the DAG column on on the DAGs page,
but when in doubt it is also passed as a querystring in the url for that DAG's
view page. For example, if I click on the DAG "Alfred2", the url of the page I
am taken to is
`http://airflow.7parkdata.com:8080/admin/airflow/graph?dag_id=Alfred2`, so the
DAG_ID is `Alfred2`.

You can get task_ids from the details tab of a DAG.

## Airflow gotchas

Using None as a schedule interval is not recommended. Instead use @once. When using None you are unable to mark tasks as succeeding.

## How to manually restart the service


```pkill -f webserver
pkill -f scheduler
pkill -f flower

screen -S webserver
source ~/.bash_profile
airflow webserver
Ctrl A + D

screen -S scheduler
source ~/.bash_profile
airflow scheduler
Ctrl A + D

screen -S flower
source ~/.bash_profile
airflow flower
Ctrl A + D

screen -S worker
source ~/.bash_profile
airflow worker --queue special
Ctrl A + D

# Security
