-- q5: trench activity per week (run on the trench SQLite database).
-- Projects/schemes created, scheme saves (= versions), archive/trash ops
-- come from the audit events DB (q1), this covers the catalogue itself.
SELECT strftime('%Y-W%W', created_at) AS week,
       COUNT(*) AS projects_created
FROM projects
WHERE deleted_at IS NULL
GROUP BY week
ORDER BY week;

-- Schemes created per week:
-- SELECT strftime('%Y-W%W', created_at) AS week, COUNT(*) AS schemes_created
-- FROM schemes WHERE deleted_at IS NULL GROUP BY week ORDER BY week;

-- Scheme saves (versions) per week:
-- SELECT strftime('%Y-W%W', saved_at) AS week, COUNT(*) AS saves
-- FROM scheme_versions GROUP BY week ORDER BY week;
