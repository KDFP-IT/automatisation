-- q1: actions and saved time by tool for the period.
-- Metabase variables: {{start}} / {{end}} (Field Filter or Date on events.ts).
SELECT tool,
       COUNT(*) AS events,
       COUNT(DISTINCT user_id) AS users,
       ROUND(SUM(saved_minutes) / 60.0, 2) AS saved_hours
FROM events
WHERE (details IS NULL OR details NOT LIKE '%mock%') AND ts >= {{start}} AND ts < {{end}}
GROUP BY tool
ORDER BY saved_hours DESC;
