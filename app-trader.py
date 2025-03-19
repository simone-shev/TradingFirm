import sys  # to print error messages to sys.stderr
import matplotlib.pyplot as plt
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mysql.connector
import mysql.connector.errorcode as errorcode

#new ivy code
import numpy as np

today = date.today()

# Debugging flag to print errors when debugging that shouldn't be visible
# to an actual client.
DEBUG = False


# ----------------------------------------------------------------------
# SQL Utility Functions
# ----------------------------------------------------------------------
def get_conn():
    """"
    Returns a connected MySQL connector instance, if connection is successful.
    If unsuccessful, exits.
    """
    try:
        conn = mysql.connector.connect(
          host='localhost',
          user='trader456',
          port='3306', 
          password='password',
          database='final' 
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

# ----------------------------------------------------------------------
# Functions for Command-Line Options/Query Execution
# ----------------------------------------------------------------------

def select_assets_fund():
    '''
    Prompts the user for a fund that they want to see the assets and their 
    respective quantities, which will be ordered by quantitiy in decreasing order
    Streth goal will be to include a pie chart of this 
    Also displays the funds assets under management, so the funds total value.
    Streth goal will be to include a pie chart of this

    Inputs:
    The fund that the user wants to see the composition of 

    Output:
    The asset SYMBOLS not their id and the quantity 
    '''
    fund = input('What fund do you want to look at? Enter the fund id ')
    sql = """
SELECT assets.symbol, asset_qty
FROM composition JOIN assets on composition.asset_id=assets.asset_id
WHERE fund_id = '%s' 
ORDER BY asset_qty DESC;
""" % (fund)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            print("No results found for that fund.")
        for i in range(len(rows)):
            row = rows[i]
            (symbol, asset_qty) = (row) # tuple unpacking!
            print(f"Asset Name: {symbol:<10}  Quantity: {asset_qty}")   
        cursor.close()     
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            sys.stderr.write('An error occurred, while finding the compositon information in your fund')
    
    sql = "SELECT calculate_fund_aum(%s);" % (fund)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        aum = row[0]
        if row:
            print(f"Fund {fund} AUM: {aum}")  
        else:
            print("AUM not found")         
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            sys.stderr.write('An error occurred, while finding the aum in your fund')

def last_month_asset():
    """
    Retrieve the last month's prices for a particular asset and display it as a line
    graph 

    Inputs:
    Asset symbol to search for

    Ouput:
    Line chart showing the previous month's close prices
    """
    asset = input('What asset do you want to look at the previous months performace for? Please input as symbol ')
    month_prior = today - relativedelta(months=1)
    sql = """
SELECT close_price, eval_date
FROM market_data_historical
JOIN assets on market_data_historical.asset_id=assets.asset_id
WHERE assets.symbol= '%s' AND eval_date>'%s'
ORDER BY eval_date ASC;
""" % (asset, month_prior)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            print("No results found.")
        prices = []
        dates = []
        for row in rows:
            (price, date) = (row) # tuple unpacking!
            print(f"Date: {date}, Price: {price}")
            month_day = date.strftime("%m-%d")
            prices.append(price)
            dates.append(month_day)
        plt.plot(dates, prices)
        plt.xticks(rotation=90) 
        plt.title("Price vs Dates")
        plt.xlabel("Dates")
        plt.ylabel("Prices")
        plt.show()
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            sys.stderr.write('An error occurred, while finding the price information for your asset')


def make_trade():
    """
    Allows a trader to insert a new row of data, a trade into the trades table. 
    In reality, this would be done automated, but we allow a trader to manually do 
    this if something goes wrong. No outputs

    Inputs: trade_id, fund_id, asset_id, trade_type, quantity, purchase_price,
    exec_ts, clearinghouse_id 
    """
    ans = input('Do you want to manually insert a trade? [y/n]')
    fund = None
    if ans and ans.lower()[0] == 'y':
        trade_id, fund_id, asset_id, trade_type, qty, price, time, clearing = input("""Please input the trade ID, fund_id, asset_id, trade type, quantity, purchase price, time of trade, and clearinghouse all separated by commas""").split(',')
    fund_id = int(fund_id)
    asset_id = int(asset_id)
    qty = float(qty)
    price = float(price)
    clearing = int(clearing)
    sql = " CALL make_trade (%s, %s, %s, %s, %s, %s, %s, %s) " 
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (trade_id, fund_id, asset_id, trade_type, qty, price, time, clearing))
        conn.commit()
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            sys.stderr.write('An error occurred, while trying to insert this trade')

def calculate_risk_metrics():
    """
    Calculates risk metrics (volatility, Sharpe ratio, or Value at Risk)
    for a given asset based on historical price data.
    
    The function prompts the user for the asset symbol and risk type,
    fetches historical data using a global connection (conn),
    and computes the chosen risk metric.
    """
    risk_free_rate = 0.02  # Default annual risk-free rate
    debug = False

    # Prompt for asset symbol and risk type.
    asset_symbol = input("What is the symbol of the asset you want? ").strip()
    risk_type_ans = input("What type of risk do you want to calculate: (A) volatility, (B) sharpe, (C) var:  ").strip().upper()

    if risk_type_ans == 'A':
        risk_type = 'volatility'
    elif risk_type_ans == 'B':
        risk_type = 'sharpe'
    elif risk_type_ans == 'C':
        risk_type = 'var'
    else:
        print("Invalid risk type input. Please choose A, B, or C.")
        return

    # SQL query to fetch historical closing prices for the asset.
    sql = ("""
        SELECT m.close_price, m.eval_date
        FROM market_data_historical AS m
        JOIN assets AS a ON m.asset_id = a.asset_id
        WHERE a.symbol = %s
        ORDER BY m.eval_date ASC;
    """)

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (asset_symbol,))
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            raise ValueError(f"No historical data found for asset symbol: {asset_symbol}")
        
        # Extract closing prices.
        prices = [row[0] for row in rows]

    except mysql.connector.Error as err:
        if debug:
            sys.stderr.write(f"Database error: {err}\n")
        else:
            sys.stderr.write("An error occurred while fetching data.\n")
        return

    if len(prices) < 2:
        raise ValueError("Not enough historical data to calculate risk metrics.")

    # Calculate daily returns as percentage changes.
    prices_array = np.array(prices, dtype=float)
    returns = np.diff(prices_array) / prices_array[:-1]

    # Compute risk metrics based on the chosen type.
    if risk_type == "volatility":
        volatility = np.std(returns) * np.sqrt(252)
        print(f"Annualized volatility for {asset_symbol}: {volatility:.4f}")
        return volatility

    elif risk_type == "sharpe":
        daily_risk_free = risk_free_rate / 252
        daily_mean_return = np.mean(returns)
        daily_volatility = np.std(returns)
        if daily_volatility == 0:
            raise ValueError("Zero volatility encountered; cannot compute Sharpe ratio.")
        sharpe_ratio = (daily_mean_return - daily_risk_free) / daily_volatility
        sharpe_ratio_annualized = sharpe_ratio * np.sqrt(252)
        print(f"Annualized Sharpe ratio for {asset_symbol}: {sharpe_ratio_annualized:.4f}")
        return sharpe_ratio_annualized

    elif risk_type == "var":
        var_95 = np.percentile(returns, 5)
        print(f"Value at Risk (5th percentile) for {asset_symbol}: {var_95:.4f}")
        return var_95

    else:
        raise ValueError("Invalid risk_type specified. Choose 'volatility', 'sharpe', or 'var'.")
    

def cancel_trade():
    """
    Cancels a trade by calling the stored procedure 'cancel_trade' in the database.
    
    The function prompts the user for the trade ID of the trade to cancel, calls the stored
    procedure, and commits the change. It prints a confirmation message if successful.
    """
    ans = input("Do you want to cancel a trade? [y/n]: ").strip().lower()
    if not ans or ans[0] != 'y':
        print("Cancel trade aborted.")
        return

    trade_id = input("Enter the trade ID to cancel: ").strip()
    sql = "CALL cancel_trade(%s);"
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (trade_id,))
        conn.commit()
        print(f"Trade {trade_id} has been cancelled successfully.")
        cursor.close()
    except mysql.connector.Error as err:
        if DEBUG:
            sys.stderr.write(f"Database error: {err}\n")
            sys.exit(1)
        else:
            sys.stderr.write("An error occurred while cancelling the trade.\n")

# ----------------------------------------------------------------------
# Functions for Command-Line Options/Query Execution
# ----------------------------------------------------------------------

def create_new_user():
    user = input('Please enter a username: ').strip().lower()
    pwd = input('Please enter a password: ').strip().lower()
    
    if user == "" or pwd == "":
        sys.stderr.write("Please do not input an empty username or password\n")
        sys.exit(1)

    sql = "CALL sp_add_user('%s', '%s');" % (user, pwd)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print(f"User added successfully.")
    except mysql.connector.Error as err:
        if DEBUG:
            sys.stderr.write(f"Database error: {err}\n")
            sys.exit(1)
        else:
            sys.stderr.write("An error occurred while adding the user. User may already exists. Try again.\n")
            sys.exit(1)

def log_in():
    new_user = input("Do you need to create an account? [y/n]")
    if new_user and new_user.lower()[0] == 'y':
        create_new_user()
        return
    else:
        user = input('Please enter your username: ').lower()
        pwd = input('Please enter your password: ').lower()

        if user == "" or pwd == "":
            sys.stderr.write("Please do not input an empty username or password\n")
            sys.exit(1)

        sql = "SELECT authenticate('%s', '%s');" % (user, pwd)
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
            valid = row[0]
            if valid==1:
                return
            else:
                print("Invalid username or password, reload to re-enter")
                sys.exit(1)
        except mysql.connector.Error as err:
            if DEBUG:
                sys.stderr.write(f"Database error: {err}\n")
                sys.exit(1)
            else:
                sys.stderr.write("An error occurred while trying to authenticate.\n")
                sys.exit(1)

# ----------------------------------------------------------------------
# Command-Line Functionality
# ----------------------------------------------------------------------
def show_options():
    """
    Displays options users can choose in the application, such as
    viewing <x>, filtering results with a flag (e.g. -s to sort),
    sending a request to do <x>, etc.
    """
    print('What would you like to do? ')
    print('  (f) - get a funds asset composition')
    print('  (p) - get last month\'s prices for an asset')
    print('  (t) - make a trade')
    print('  (r) - calculate risk metrics')
    print('  (c) - cancel a trade')
    print('  (q) - quit')
    print()
    ans = input('Enter an option: ').lower()
    if ans == 'q':
        quit_ui()
    elif ans == 'f':
        select_assets_fund()
    elif ans == 'p':
        last_month_asset()
    elif ans == 't':
        make_trade()
    elif ans == 'r':
        calculate_risk_metrics()
    elif ans == 'c':
        cancel_trade()


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
    log_in()
    show_options()


if __name__ == '__main__':
    # This conn is a global object that other functions can access.
    # You'll need to use cursor = conn.cursor() each time you are
    # about to execute a query with cursor.execute(<sqlquery>)
    conn = get_conn()
    main()
