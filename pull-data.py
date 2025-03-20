from polygon import RESTClient
from datetime import datetime
import sys
import mysql.connector
import mysql.connector.errorcode as errorcode
import json
import time

API_KEY = "YOUR API KEY"
client = RESTClient(api_key=API_KEY)
# Assume this is being run in pacific time, and we give time for ater 
# hours trading
MARKET_CLOSE = datetime.strptime("20:00", "%H:%M").time()
DEBUG = True

def get_conn():
    """"
    Returns a connected MySQL connector instance, if connection is successful.
    If unsuccessful, exits.
    """
    try:
        conn = mysql.connector.connect(
          host='localhost',
          user='data789',
          # Find port in MAMP or MySQL Workbench GUI or with
          # SHOW VARIABLES WHERE variable_name LIKE 'port';
          port='3306',  # this may change!
          password='password',
          database='final' # replace this with your database name
        )
        print('Successfully connected.')
        return conn
    except mysql.connector.Error as err:
        # Remember that this is specific to _database_ users, not
        # application users. So is probably irrelevant to a client in your
        # simulated program. Their user information would be in a users table
        # specific to your database; hence the DEBUG use.
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR and DEBUG:
            sys.stderr('Incorrect username or password when connecting to DB.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR and DEBUG:
            sys.stderr('Database does not exist.')
        elif DEBUG:
            sys.stderr(err)
        else:
            # A fine catchall client-facing message.
            sys.stderr('An error occurred, please contact the administrator.')
        sys.exit(1)

def get_tickers():
    sql = "SELECT symbol FROM assets;"
    tickers = []
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            print("No results found.")
        for row in rows:
            ticker = row[0]
            tickers.append(ticker)
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            # TODO: Please actually replace this :) 
            sys.stderr('An error occurred, while finding the symbols for all assetts')
    return tickers


def get_eod(tickers):
    # date = datetime.today().strftime("%Y-%m-%d")
    # hard code in a previous date to test it, try one after 3/14!
    date = '2025-03-17'
    eod_data = {}
    for ticker in tickers:
        ticker = str(ticker)
        try:
            response = client.get_daily_open_close_agg(ticker, date)
            eod_data[ticker] = {
                "eval_date": date,
                "open": response.open,
                "high": response.high,
                "low": response.low,
                "close": response.close
            }
        except Exception as e:
            print(f"Error fetching EOD data for {ticker}: {e}")
    return eod_data

def insert_eod_data(data):
    for key in data:
        asset_id = None
        sql = "SELECT asset_id FROM assets WHERE symbol='" + key + "'"
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            asset_id = cursor.fetchone()[0]
            if not asset_id:
                print("No corresponding id found.")
            cursor.close()
        except mysql.connector.Error as err:
            # If you're testing, it's helpful to see more details printed.
            if DEBUG:
                sys.stderr(err)
                sys.exit(1)
            else:
                # TODO: Please actually replace this :) 
                sys.stderr('An error occurred, while finding the ID for this asset {key}')
        sql = """
            INSERT INTO market_data_historical 
            (asset_id,eval_date,open_price,close_price,high_price,low_price)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        eval_date = data[key]['eval_date']
        open_price = float(data[key]['open'])
        close_price = float(data[key]['close'])
        high_price = float(data[key]['high'])
        low_price = float(data[key]['low'])
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (asset_id, eval_date, open_price, close_price, high_price, low_price))
            conn.commit()
            cursor.close()
        except mysql.connector.Error as err:
            # If you're testing, it's helpful to see more details printed.
            if DEBUG:
                sys.stderr(err)
                sys.exit(1)
            else:
                # TODO: Please actually replace this :) 
                sys.stderr('An error occurred, while finding the ID for this asset {key}')

def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    print('Good bye!')
    exit()


def main():
    """
    Main function for starting things up.
    """
    tickers = get_tickers()
    while True:
        #now = datetime.now().time()
        
        # if running manually comment out this if statement and just make sure
        # you are pulling data from a previous day 
        #if now > MARKET_CLOSE:
        eod_prices = get_eod(tickers)
        insert_eod_data(eod_prices)
        break  # Exit script after EOD data retrieval


if __name__ == '__main__':
    # This conn is a global object that other functions can access.
    # You'll need to use cursor = conn.cursor() each time you are
    # about to execute a query with cursor.execute(<sqlquery>)
    conn = get_conn()
    main()
