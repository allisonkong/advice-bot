DROP DATABASE IF EXISTS advice_bot_dev;
CREATE DATABASE advice_bot_dev;
USE advice_bot_dev;

GRANT SELECT, INSERT, UPDATE, DELETE ON *.* TO 'advice_bot'@'%';

SOURCE advice_bot/database/schema/schema.sql;
