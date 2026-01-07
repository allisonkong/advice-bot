SELECT
  YEAR(FROM_UNIXTIME(timestamp_micros / 1e6)) AS year,
  MONTH(FROM_UNIXTIME(timestamp_micros / 1e6)) AS month,
  prize,
  prize_name,
  COUNT(*) AS count,
  COUNT(*) * prize_value_m AS payout_m
FROM monthly_giveaway_rolls
  NATURAL JOIN prizes
WHERE prize != 0
GROUP BY year, month, prize
ORDER BY year, month, prize;


SELECT
  year, month, SUM(payout_m) AS total_payout_m
FROM (
  SELECT
    YEAR(FROM_UNIXTIME(timestamp_micros / 1e6)) AS year,
    MONTH(FROM_UNIXTIME(timestamp_micros / 1e6)) AS month,
    prize,
    prize_name,
    COUNT(*) AS count,
    COUNT(*) * prize_value_m AS payout_m
  FROM monthly_giveaway_rolls
    NATURAL JOIN prizes
  WHERE prize != 0
  GROUP BY year, month, prize
) AS monthly_payouts
GROUP BY year, month
ORDER BY year, month;
