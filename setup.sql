DROP VIEW IF EXISTS firm_wide_asset_summary;
DROP TABLE IF EXISTS market_data_real;
DROP TABLE IF EXISTS market_data_historical;
DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS composition;
DROP TABLE IF EXISTS clearinghouses;
DROP TABLE IF EXISTS assets;
DROP TABLE IF EXISTS funds;

-- Represents investment vehicles (e.g., hedge funds, quant funds) 
-- managed by the firm.
CREATE TABLE funds (
    fund_id             INTEGER           AUTO_INCREMENT,
    -- Fund name that describes the type of fund broadly or maybe its inception
    -- this is just used coloquially mainly so people within the company don't 
    -- have to remember ids, can be null if there is no name and can just use id
    fund_name           VARCHAR(50),
    inception_date      DATE              NOT NULL,
    -- Assets Under Management, a fund can hold up to 100,000,000, but not 
    -- including it.
    -- Note I am confused here on exactly how this would operate like should it 
    -- be referential to the current value of all the assets in a fund?
    aum                 NUMERIC(10, 2)    NOT NULL,
    PRIMARY KEY(fund_id) 
);

-- Stores details about tradable assets, such as equities, derivatives, 
-- and cryptocurrencies.
CREATE TABLE assets (
    asset_id     INTEGER      AUTO_INCREMENT,
    asset_name   VARCHAR(30)  NOT NULL,
    -- ticker for a stock 
    symbol       VARCHAR(10)  NOT NULL UNIQUE,
    -- type such as 'Equity, Futures, Options, FX, Crypto, etc.'
    type         VARCHAR(20)  NOT NULL,
    PRIMARY KEY(asset_id)
);

-- Stores the different clearinghouses that trades are executed through,
-- clearinghouses act as an intermediary for brokers and hold a stock
CREATE TABLE clearinghouses (
    clearinghouse_id   INTEGER     AUTO_INCREMENT,
    clearing_name      VARCHAR(30) NOT NULL,
    -- The exchange that the clearinghouse mainly operates on such as the New York
    -- stock exchange
    exchange           VARCHAR(30) NOT NULL,
    PRIMARY KEY(clearinghouse_id)
);

-- Maps funds to the assets it has and the quantity that it holds
CREATE TABLE composition (
    fund_id       INTEGER,
    asset_id      INTEGER,
    -- quantity of asset in a particular fund, which cannot exceed 10,000,000
    -- shares
    asset_qty     NUMERIC(9, 2)   NOT NULL,
    PRIMARY KEY(fund_id, asset_id),
    FOREIGN KEY (fund_id) REFERENCES funds(fund_id)
    ON UPDATE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
    ON UPDATE CASCADE
);

-- Logs each executed trade for a fund
CREATE TABLE trades (
    -- trade_id unlike others is alphanumerical, since a much higher volume of 
    -- these can occur 
    trade_id          VARCHAR(20),
    fund_id           INTEGER       NOT NULL,
    asset_id          INTEGER       NOT NULL,
    -- Examples of trade types are BUY, SELL, SHORT, COVER
    trade_type        VARCHAR(15)   NOT NULL,
    -- same as above trades can be executed in quantities of up to 10,000,000
    quantity          NUMERIC(9, 2) NOT NULL,
    -- The price of a stock cannot exceed 100,000
    purchase_price    NUMERIC(7, 2) NOT NULL,
    exec_ts           TIMESTAMP     NOT NULL,
    -- The clearinghouse from which the trade was executed could be self
    clearinghouse_id  INTEGER       NOT NULL,
    PRIMARY KEY(trade_id),
    FOREIGN KEY (fund_id) REFERENCES funds(fund_id),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- Maintains historical market prices.
CREATE TABLE market_data_historical (
    asset_id      INTEGER,
    eval_date     DATE,
    -- The price of a stock cannot exceed 100,000
    open_price    NUMERIC(7, 2) NOT NULL,
    close_price   NUMERIC(7, 2) NOT NULL,
    high_price    NUMERIC(7, 2) NOT NULL,
    low_price     NUMERIC(7, 2) NOT NULL,
    PRIMARY KEY(asset_id, eval_date),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- Maintains real-time market prices.
CREATE TABLE market_data_real (
    asset_id      INTEGER,
    price         NUMERIC(7, 2) NOT NULL,
    ts            TIMESTAMP,
    PRIMARY KEY(asset_id, ts),
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);


-- Stores the firm-wide exposure of a trading firm's assets. The firm-wide 
-- exposure is the total value of an asset held across the firm, as recall a 
-- firm is composed of different funds. We use market data real so that it is a 
-- completley updated value at a singular momrnt
CREATE VIEW firm_wide_asset_summary AS
SELECT 
    a.symbol,
    SUM(c.asset_qty) AS total_quantity,
    SUM(c.asset_qty * md1.close_price) AS total_value
FROM composition c
JOIN assets a ON c.asset_id = a.asset_id
LEFT JOIN (
    SELECT md1.asset_id, md1.close_price
    FROM market_data_historical md1
    WHERE md1.eval_date = (
        SELECT MAX(md2.eval_date) 
        FROM market_data_historical md2 
        WHERE md2.asset_id = md1.asset_id
    )
) md1 ON c.asset_id = md1.asset_id
GROUP BY a.symbol;

CREATE INDEX idx_market_dates
ON market_data_historical (eval_date, asset_id);

