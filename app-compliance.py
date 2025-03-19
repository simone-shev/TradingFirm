import sys  # to print error messages to sys.stderr
import matplotlib as plt
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mysql.connector
import mysql.connector.errorcode as errorcode

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
          user='compliance123',
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
            sys.stderr.write('Incorrect username or password when connecting to DB.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR and DEBUG:
            sys.stderr.write('Database does not exist.')
        elif DEBUG:
            sys.stderr(err)
        else:
            # A fine catchall client-facing message.
            sys.stderr.write('An error occurred, please contact the administrator.')
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


def get_firm_wide_asset_summary():
    """
    Retrieve the asset value for a asset across the firm so how much is owned 
    across the firm in all funds 

    Inputs:
    Asset symbol to search for 

    Outputs:
    Its firmwide asset summary
    """
    asset = input('What asset do you want to look at?, input as a symbol ')
    sql = """
    SELECT total_value
    FROM firm_wide_asset_summary
    WHERE symbol= '%s';
""" % (asset)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        value = row[0]
        if row:
            print(f"Asset: {asset} Total Value: {value}")  
        else:
            print("Value not found")         
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            sys.stderr.write('An error occurred, while finding the total value of your asset')
   

def value_in_clearinghouse():
    """
    Get the total quantity of assets that go through a particular clearing house, 
    this is useful for compliance 

    Inputs:
    Clearing house id to search for

    Outputs: 
    Total quantity that has gone through the clearinghouse 
    """
    clearing = input('What clearing house do you want to look at?, input as ID ')
    sql = """
    SELECT 
        SUM(trades.quantity) AS total_qty
    FROM trades
    JOIN clearinghouses ON trades.clearinghouse_id = clearinghouses.clearinghouse_id
    WHERE trades.trade_type IN ('BUY', 'SELL')
    AND clearinghouses.clearinghouse_id = %s ;
""" % (clearing)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        qty = row[0]
        if row:
            print(f"Clearinghouse: {clearing} Total Quantity: {qty}")  
        else:
            print("Value not found")         
    except mysql.connector.Error as err:
        # If you're testing, it's helpful to see more details printed.
        if DEBUG:
            sys.stderr(err)
            sys.exit(1)
        else:
            sys.stderr.write('An error occurred, while finding the total quantity through this clearinghouse')

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
    Displays options specific for admins, such as adding new data <x>,
    modifying <x> based on a given id, removing <x>, etc.
    """
    print('What would you like to do? ')
    print('  (f) - get a funds asset composition')
    print('  (v) - get the net asset value')
    print('  (c) - get the value held in a clearinghouse')
    print('  (q) - quit')
    print()
    ans = input('Enter an option: ').lower()
    if ans == 'q':
        quit_ui()
    elif ans == 'f':
        select_assets_fund()
    elif ans == 'v':
        get_firm_wide_asset_summary()
    elif ans == 'c':
        value_in_clearinghouse()


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
