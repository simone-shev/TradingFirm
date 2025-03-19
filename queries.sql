-- Get the asset symbol and quantity from the composition table for a certain
-- fund, and order it by decreasing value for the asset_qty]
SELECT assets.symbol, asset_qty
FROM composition JOIN assets on composition.asset_id=assets.asset_id
WHERE fund_id = 1
ORDER BY asset_qty DESC;

-- Get the close price and evaulation date from the market_data_historical 
-- table for a certain asset when the evaluation date is greater than a certain
-- date, then order it for increasing evalutation date
SELECT close_price, eval_date
FROM market_data_historical
JOIN assets on market_data_historical.asset_id=assets.asset_id
WHERE assets.symbol= 'AAPL' AND eval_date>'2025-02-17'
ORDER BY eval_date ASC;

-- Get the total quantity of trades that are flowing through a certain
-- clearing house
SELECT 
    SUM(trades.quantity) AS total_qty
FROM trades
JOIN clearinghouses ON trades.clearinghouse_id = clearinghouses.clearinghouse_id
WHERE trades.trade_type IN ('BUY', 'SELL')
AND clearinghouses.clearinghouse_id = 301;

-- Get the total quantity of trades that are going through each fund as well as
-- the volume being traded, which is the qunatity of assets being traded
SELECT 
    t.fund_id,
    f.fund_name,
    COUNT(t.trade_id) AS total_trades,
    SUM(t.quantity) AS total_volume
FROM trades t
JOIN funds f ON t.fund_id = f.fund_id
GROUP BY t.fund_id, f.fund_name
ORDER BY total_volume DESC;