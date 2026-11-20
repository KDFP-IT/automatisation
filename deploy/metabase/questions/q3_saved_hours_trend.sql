-- q3: saved-hours trend per week and tool.
SELECT strftime('%Y-W%W', ts) AS week,
       tool,
       COUNT(*) AS events,
       ROUND(SUM(saved_minutes) / 60.0, 2) AS saved_hours
FROM events
WHERE (details IS NULL OR details NOT LIKE '%mock%') AND ts >= {{start}} AND ts < {{end}}
GROUP BY week, tool
ORDER BY week, tool;
