# Podio Synchronisation tool (psync).
The main purpose of this tool is to extract the data from Podio's application and store the data into a database for ease of use.
This help in backup data and using reporting tools.

## How it works
First, you need a user (registered in Podio) and an API key. For more info on this, please check Podio's documentation: https://developers.podio.com/api-key

Once done, you enter this information in the tool. You can then browse your organisation structure and select the application to synchronise.

After you have entered the information about the application(s) you want to synchronise, you can call a manage.py command to connect to podio and retrieve the data.

For simplicity, this tool does not include any scheduling function but you could easily achieve that by using cron or task scheduler.

On the first run, the database will be updated to replicate the structure of the Podio application. Then the data will be downloaded and entered in the DB.
If the application changes (add/remove fields), the database table will be updated accordingly.

## Setup
### settings
`PSYNC_TABLE_PREFIX = 'psync'`
This prefix will be used when creating new tables in the DB. All tables created from this tool will start with this prefix (apart from django DB).

`PSYNC_ENABLE_USERS = True` Enable users to be entered through UI (adding several users). `True` by default. If set to `False` the following settings need to be documented (`PSYNC_USER`, `PSYNC_PWD`, `PSYNC_APPLICATION_NAME`, `PSYNC_CLIENT_SECRET`,`PSYNC_CLIENT_ID`)

The following settings need to be documented if `PSYNC_ENABLE_USERS` is et to `False`:

`PSYNC_USER = ''`

`PSYNC_PWD = ''`

`PSYNC_APPLICATION_NAME = ''`

`PSYNC_CLIENT_SECRET = ''`

`PSYNC_CLIENT_ID = ''`
### logging


## Requirements
Podio API Client: https://developers.podio.com/clients/python
