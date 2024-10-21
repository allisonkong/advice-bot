
CREATE TABLE discord_users (
  discord_user_id BIGINT NOT NULL,
  -- Globally unique username. This includes the discriminator if
  -- the user still has one.
  discord_username VARCHAR(255) NOT NULL,

  PRIMARY KEY (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE command_log (
  timestamp_micros BIGINT NOT NULL,
  discord_user_id BIGINT NOT NULL,
  command VARCHAR(255) NOT NULL,
  command_args VARCHAR(1000) NULL,
  command_outcome VARCHAR(1000) NULL,

  PRIMARY KEY (timestamp_micros),
  FOREIGN KEY (discord_user_id)
    REFERENCES discord_users (discord_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE monthly_lotto (
  discord_user_id BIGINT NOT NULL,
  last_attempt_micros BIGINT NOT NULL,

  PRIMARY KEY (discord_user_id),
  FOREIGN KEY (discord_user_id)
    REFERENCES discord_users (discord_user_id),
  FOREIGN KEY (last_attempt_micros)
    REFERENCES command_log (timestamp_micros)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
