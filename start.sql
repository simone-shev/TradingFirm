DROP DATABASE if exists final;
CREATE DATABASE final;
USE final;

source setup.sql;
source load-data.sql;
source setup-passwords.sql;
source setup-routines.sql;
source grant-permissions.sql;
source queries.sql;