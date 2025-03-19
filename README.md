# TradingFirmDB

## Install
Please have the following installed as well as mySQL, see online documentation
for how to install mySQL for your system.

```
pip install matplotlib
pip install polygon
pip install -U polygon-api-client
```

## Getting Started
In mysql, you can use the terminal, run `source start.sql;`

To automatically run the pull-data.py file you will need to do some setup.

## Setup for Linux/MacOS
1. Make an executable `chmos +x pull-data.py`
2. Edit the crontab, command-line utility used to schedule tasks `crontab -e`
3. Add a cron job so that we can run the script at a specific time 
`0 23 * * 1-5 /usr/bin/python3 /path/pull-data.py`
Here we add a job 11:00 PM local time for Monday-Friday, verify the python3 location as well as where the script is stored.
The two stars here indicate that it can run any day and any month.

## Setup for Windows
1. Open the Task Scheduler
2. Go to "Create Basic Task"
3. Select "Daily" then set the time to 11:00 PM
4. Choose "Start a program" 
5. Under "Program/script" Put the path to your python executable. This is likely under "C:\Users\YourUser\AppData\Local\Programs\Python\Python*your version*\python.exe"
6. Under "Arguments" (optional) put the path to the pull_data.py 
7. Then just click finish setup

## Starting the database
In your commandline, launch mysql with the following command to ensure you can load in data properly:
`mysql --local-infile=1 -u your-user -p`

Then type in `source start.sql;`

This will create the database, set it up and load in data.

## Running the ptyhon apps
To run the trader app, run "python3 app-trader.py"
This app is meant to mimic how a trader would interact with a trading database, they can see how a fund is perfomring, make or cancel trades, and view market data.
You will be prompted to either create a new username and password or you can login

To run the compliance app, run "python3 app-compliance.py"
This app is meant to mimic how someone in compliance would interact with a trading database, they can also see a fund's performace, but cannot edit the tables at all (aside from via the functions and procedures needed for logging in). They also have specialized options such as being able to see how much of an asset is held across the firm and how many trades go through a certain clearinhouse. 
You will be prompted to either create a new username and password or you can login