
CREATE TABLE discord_users (
  discord_user_id BIGINT NOT NULL,
  discord_username VARCHAR(255) NOT NULL,

  PRIMARY KEY (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE command_log (
  message_id BIGINT NOT NULL,
  timestamp_micros BIGINT NOT NULL,
  discord_user_id BIGINT NOT NULL,
  command VARCHAR(255) NOT NULL,
  command_status INTEGER NOT NULL,

  PRIMARY KEY (message_id),
  FOREIGN KEY (discord_user_id)
    REFERENCES discord_users (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE monthly_giveaway_rolls (
  discord_user_id BIGINT NOT NULL,
  timestamp_micros BIGINT NOT NULL,
  -- Identifies the unique roll within a given participation.
  sequence_index INTEGER NOT NULL,
  -- See Prize enum.
  prize INTEGER NOT NULL,

  PRIMARY KEY (discord_user_id, timestamp_micros, sequence_index),
  FOREIGN KEY (discord_user_id)
    REFERENCES discord_users (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE prizes (
  prize INTEGER NOT NULL,
  prize_name VARCHAR(255) NOT NULL,
  prize_value_m INTEGER NOT NULL,
  PRIMARY KEY (prize)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO prizes
  (prize, prize_name, prize_value_m)
VALUES
  (0, 'NO_PRIZE', 0),
  (1, 'GOODYBAG', 5),
  (2, 'GP_2M', 2),
  (3, 'CUSTOM_RANK', 0),
  (4, 'CUSTOM_RANK_PLUSPLUS', 0),
  (5, 'GP_5M', 5),
  (6, 'GP_10M', 10);

CREATE OR REPLACE VIEW monthly_giveaway
AS
  SELECT
    discord_user_id,
    MAX(timestamp_micros) AS last_participation_micros
  FROM monthly_giveaway_rolls
  GROUP BY discord_user_id;
