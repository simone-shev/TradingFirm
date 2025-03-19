DROP USER IF EXISTS 'compliance123'@'localhost';
DROP USER IF EXISTS 'trader456'@'localhost';
DROP USER IF EXISTS 'data789'@'localhost';

CREATE USER 'compliance123'@'localhost' IDENTIFIED BY 'password';
CREATE USER 'trader456'@'localhost' IDENTIFIED BY 'password';
CREATE USER 'data789'@'localhost' IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES ON final.* TO 'trader456'@'localhost';
GRANT ALL PRIVILEGES ON final.* TO 'data789'@'localhost';
GRANT EXECUTE ON PROCEDURE final.sp_add_user TO 'compliance123'@'localhost';
GRANT EXECUTE ON FUNCTION final.authenticate TO 'compliance123'@'localhost';
GRANT EXECUTE ON FUNCTION final.calculate_fund_aum TO 'compliance123'@'localhost';
GRANT SELECT ON final.* TO 'compliance123'@'localhost';
FLUSH PRIVILEGES;