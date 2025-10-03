CREATE VIEW IF NOT EXISTS daily_breathing AS
SELECT
    DATE(timestamp) AS date,
    SUM(CASE WHEN response=1 THEN 5.3333 ELSE 0 END) AS total_minutes,
    COUNT(CASE WHEN response=1 THEN 1 END) AS sessions,
    CASE strftime('%w', timestamp)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END AS weekday,
    SUM(SUM(CASE WHEN response=1 THEN 5.3333 ELSE 0 END)) 
        OVER (ORDER BY DATE(timestamp)) AS cumulative_minutes
FROM breathing_log
GROUP BY DATE(timestamp)
ORDER BY DATE(timestamp);
