-- q4: errors by tool and action (reliability).
SELECT tool,
       action,
       status,
       COUNT(*) AS events,
       error
FROM events
WHERE ts >= {{start}} AND ts < {{end}}
  AND (status != 'ok' OR error IS NOT NULL)
GROUP BY tool, action, status, error
ORDER BY events DESC
LIMIT 100;
