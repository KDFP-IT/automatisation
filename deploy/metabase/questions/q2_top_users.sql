-- q2: top users by saved time for the period (ФИО из AD, fallback — логин).
SELECT COALESCE(NULLIF(user_name, ''), ad_login) AS user,
       ad_login,
       COUNT(*) AS events,
       COUNT(DISTINCT tool) AS tools_used,
       ROUND(SUM(saved_minutes) / 60.0, 2) AS saved_hours
FROM events
WHERE ts >= {{start}} AND ts < {{end}}
GROUP BY user, ad_login
ORDER BY saved_hours DESC
LIMIT 50;
