-- q6: office-chat activity (run on the chat SQLite file).
-- The chat server runs outside the portal compose; copy its sqlite file to
-- the VPS analyst host or mount it into Metabase the same way as audit.
SELECT date(sent_at) AS day,
       COUNT(*) AS messages,
       COUNT(DISTINCT sender) AS active_users
FROM messages
WHERE sent_at >= {{start}} AND sent_at < {{end}}
GROUP BY day
ORDER BY day;

-- Archive-status split (pending = waiting for Bitrix, review = manual check):
-- SELECT archive, COUNT(*) AS messages FROM messages GROUP BY archive;
