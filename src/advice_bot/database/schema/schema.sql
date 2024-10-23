
CREATE TABLE discord_users (
  discord_user_id BIGINT NOT NULL,
  discord_username VARCHAR(255) NOT NULL,

  PRIMARY KEY (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE command_log (
  message_id BIGINT NOT NULL,
  timestamp_micros BIGINT NOT NULL,
  discord_user_id BIGINT NOT NULL,
  command VARCHAR(255) NOT NULL,
  command_status INTEGER NOT NULL,

  PRIMARY KEY (message_id),
  FOREIGN KEY (discord_user_id)
    REFERENCES discord_users (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE monthly_lottery (
  discord_user_id BIGINT NOT NULL,
  last_participation_micros BIGINT NOT NULL,

  PRIMARY KEY (discord_user_id),
  FOREIGN KEY (discord_user_id)
    REFERENCES discord_users (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
