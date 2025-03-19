-- This function generates a specified number of characters for using as a
-- salt in passwords.
DELIMITER !
CREATE FUNCTION make_salt(num_chars INT)
RETURNS VARCHAR(20) DETERMINISTIC
BEGIN
    DECLARE salt VARCHAR(20) DEFAULT '';

    -- Don't want to generate more than 20 characters of salt.
    SET num_chars = LEAST(20, num_chars);

    -- Generate the salt!  Characters used are ASCII code 32 (space)
    -- through 126 ('z').
    WHILE num_chars > 0 DO
        SET salt = CONCAT(salt, CHAR(32 + FLOOR(RAND() * 95)));
        SET num_chars = num_chars - 1;
    END WHILE;

    RETURN salt;
END !
DELIMITER ;


-- This table holds information for authenticating users based on
-- a password.  Passwords are not stored plaintext so that they
-- cannot be used by people that shouldn't have them.
-- You may extend that table to include an is_admin or role attribute if you
-- have admin or other roles for users in your application
-- (e.g. store managers, data managers, etc.)
CREATE TABLE user_info (
    -- Usernames are up to 20 characters.
    username VARCHAR(20) PRIMARY KEY,

    -- Salt will be 8 characters all the time, so we can make this 8.
    salt CHAR(8) NOT NULL,

    -- We use SHA-2 with 256-bit hashes.  MySQL returns the hash
    -- value as a hexadecimal string, which means that each byte is
    -- represented as 2 characters.  Thus, 256 / 8 * 2 = 64.
    -- We can use BINARY or CHAR here; BINARY simply has a different
    -- definition for comparison/sorting than CHAR.
    password_hash BINARY(64) NOT NULL
);


DELIMITER !
CREATE PROCEDURE sp_add_user(new_username VARCHAR(20), password VARCHAR(20))
BEGIN
    DECLARE salted_password VARCHAR(28); 
    DECLARE hashed_password BINARY(64);
    DECLARE salted VARCHAR(8);

    SET salted = make_salt(8);
    SET salted_password = CONCAT(salted, password);
    SET hashed_password = SHA2(salted_password, 256);

    INSERT INTO user_info (username, salt, password_hash)
    VALUES (new_username, salted, hashed_password);
END !
DELIMITER ;


DELIMITER !
CREATE FUNCTION authenticate(input_user VARCHAR(20), password VARCHAR(20))
RETURNS TINYINT DETERMINISTIC
BEGIN
    DECLARE user_exists INT; 
    DECLARE password_match INT;
    DECLARE hashed_password BINARY(64);
    DECLARE salted VARCHAR(8);

    -- check if the user exists first 
    SELECT EXISTS(SELECT 1 FROM user_info 
    WHERE username=input_user) 
    INTO user_exists;

    IF (user_exists = 1)
        THEN
        
        -- if they do exist check if the passwords match
        SELECT salt FROM user_info WHERE username=input_user INTO salted;
        SELECT SHA2(CONCAT(salted, password), 256) INTO hashed_password;
        
        SELECT EXISTS(SELECT 1 FROM user_info 
        WHERE username=input_user AND password_hash=hashed_password) 
        INTO password_match;
        
        -- if passwords match return 1 and if not then 0
        IF (password_match = 1) 
            THEN RETURN 1;
        ELSE RETURN 0;       
        END IF; 
    -- if the users don't even match return 0 
    ELSE RETURN 0;
    END IF;
END !
DELIMITER ;


DELIMITER !
CREATE PROCEDURE sp_change_password(input_user VARCHAR(20), password VARCHAR(20))
BEGIN
    DECLARE salted_password VARCHAR(28); 
    DECLARE hashed_password BINARY(64);
    DECLARE new_salt VARCHAR(8);

    SET new_salt = make_salt(8);
    SET salted_password = CONCAT(new_salt, password);
    SET hashed_password = SHA2(salted_password, 256);

    UPDATE user_info 
    SET salt = new_salt, password_hash = hashed_password
    WHERE username=input_user;
END !
DELIMITER ;
