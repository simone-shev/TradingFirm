DROP FUNCTION IF EXISTS calculate_fund_aum;
DROP PROCEDURE IF EXISTS make_trade;
DROP TRIGGER IF EXISTS update_fund_aum;


-- Function to calculate a funds assets under management and this is what we 
-- will use to populate the aum attribute for fund. Assets under management
-- is the total value of all assets held in a fund.
DELIMITER !
CREATE FUNCTION calculate_fund_aum(fund_id_param INT)
RETURNS DECIMAL(15,2) DETERMINISTIC
BEGIN
    DECLARE iterate_asset_id INT;
    DECLARE iterate_asset_qty INT;
    DECLARE latest_price DECIMAL(7,2);
    DECLARE sum DECIMAL(15,2);
    DECLARE done INT DEFAULT 0;

    -- Declare our cursor for the quantity of an asset in composition that 
    -- matches the given fund_id
    DECLARE cur CURSOR FOR 
        SELECT asset_id, asset_qty FROM composition
        WHERE fund_id = fund_id_param;

    -- When fetch is complete, handler sets flag
    -- 02000 is MySQL error for "zero rows fetched"
    DECLARE CONTINUE HANDLER FOR SQLSTATE '02000'
        SET done = 1;

    SET sum = 0;
    
    OPEN cur;
    SET done = 0; -- Ensure done is reset before fetching
    WHILE NOT done DO
    -- get the asset quantity and id row by row from a fund's composition
        FETCH cur INTO iterate_asset_id, iterate_asset_qty;
        IF NOT done THEN
        -- Select the latest close price available so we can calculate the value
            SELECT close_price INTO latest_price
            FROM market_data_historical
            WHERE market_data_historical.asset_id = iterate_asset_id
            ORDER BY eval_date DESC
            LIMIT 1;

            -- update the sum to add in the value of the asset in the fund
            -- in case there is no price then we treat it as 0 with the coalesce
            SET sum = sum + iterate_asset_qty * COALESCE(latest_price, 0);
        END IF;
    END WHILE;
    CLOSE cur;

    RETURN sum;
END!
DELIMITER ;


-- This will modify the trades table (insert and delete) as well as 
-- update any other tables that mut be changed like the funds table. So, if 
-- the trade type passed in is "buy" then the trade is interted into the trade 
-- table and then the fund composition table is also updated to represet more
-- asset being added into that fund. Then for "sell" it would check if there 
-- are enough of an asset for that before inserting into the trades table.
DELIMITER !
CREATE PROCEDURE make_trade(
    trade_id          VARCHAR(20),
    fund_id           INTEGER,
    asset_id          INTEGER,
    trade_type        VARCHAR(15),
    quantity         DECIMAL(9,2),
    purchase_price    DECIMAL(7,2),
    exec_ts           TIMESTAMP,
    clearinghouse_id  INTEGER
)
BEGIN 
    DECLARE curr_fund_qty DECIMAL(9,2); 

    -- if we have a buy type order we can just update the composition table so 
    -- that the fund composition now accurateley represents the trades
    IF trade_type = 'BUY' THEN
        INSERT INTO composition (fund_id, asset_id, asset_qty)
        VALUES (fund_id, asset_id, quantity)
        ON DUPLICATE KEY UPDATE asset_qty = asset_qty + quantity;
    END IF;

    IF trade_type = 'SELL' THEN
    -- again we use coalesce here to ensure if there is no quantity we don't
    -- throw an unwanted error when we grab the current quantity of the asset
    -- in the fund
        SELECT COALESCE(asset_qty, 0) INTO curr_fund_qty
        FROM composition AS c
        WHERE c.fund_id = fund_id AND c.asset_id = asset_id;

        -- if we are trying to sell more of the asset than we hold then throw an
        -- error
        IF quantity > curr_fund_qty THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Not enough assets to sell';
        END IF;
    END IF;

    -- update the trades table last so that if the error is thrown then we do
    -- not update it 
    INSERT INTO trades (trade_id, fund_id, asset_id, trade_type, quantity, 
                        purchase_price, exec_ts, clearinghouse_id)
    VALUES (trade_id, fund_id, asset_id, trade_type, quantity, purchase_price,
            exec_ts, clearinghouse_id);
END!

DELIMITER ;

-- create a trigger to update AUM whenever a new trade is added we keep this 
-- separate from the inserting above since we want this done independently
DELIMITER !
CREATE TRIGGER update_fund_aum
AFTER INSERT ON trades
FOR EACH ROW
BEGIN
    DECLARE new_aum DECIMAL(15,2);

     -- Call the function calculate_fund_aum to comptue the latest AUM for the fund affected by the trade
    SET new_aum = calculate_fund_aum(NEW.fund_id);

    -- Update the funds table with the new calcualted AUM
    UPDATE funds
    SET aum = new_aum
    WHERE fund_id = NEW.fund_id;
END!

DELIMITER ;

DELIMITER !
-- cancels a trade in case it should not have been made
CREATE PROCEDURE cancel_trade(
IN trade_id_param VARCHAR(20)
)
BEGIN
    DECLARE t_fund_id INT;
    DECLARE t_asset_id INT;
    DECLARE t_trade_type VARCHAR(15);
    DECLARE t_quantity DECIMAL(9,2);


    -- Retrieve trade details based on the provided trade_id
    SELECT fund_id, asset_id, trade_type, quantity
    INTO t_fund_id, t_asset_id, t_trade_type, t_quantity
    FROM trades
    WHERE trade_id = trade_id_param;

    -- If no trade is found, signal an error
    IF t_trade_type IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Trade not found';
    END IF;

    -- Reverse the trade effects on composition based on trade type
    IF t_trade_type = 'BUY' THEN
    -- For a BUY trade, subtract the quantity from the composition.
        UPDATE composition
        SET asset_qty = asset_qty - t_quantity
        WHERE fund_id = t_fund_id AND asset_id = t_asset_id;
    ELSEIF t_trade_type = 'SELL' THEN
    -- For a SELL trade, add the quantity back.
        UPDATE composition
        SET asset_qty = asset_qty + t_quantity
        WHERE fund_id = t_fund_id AND asset_id = t_asset_id;
    END IF;

    -- Delete the trade from the trades table
    DELETE FROM trades
    WHERE trade_id = trade_id_param;
END!

DELIMITER ;