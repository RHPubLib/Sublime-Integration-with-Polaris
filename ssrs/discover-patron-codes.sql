-- discover-patron-codes.sql
-- ============================================================
-- Run this query against your Polaris database FIRST.
-- It shows every patron code at your library, how many
-- patrons with an email address use each code, and the
-- code's description.
--
-- Use the results to decide which PatronCodeIDs belong in
-- each of your three banner tiers, then update the three
-- report queries (full-patrons.sql, digital-patrons.sql,
-- limited-patrons.sql) accordingly.
--
-- Also note which codes represent staff-only cards --
-- those should be excluded from all three reports.
--
-- Polaris data source: PolarisNorthStar (or your local name)
-- ============================================================

SELECT
    P.PatronCodeID,
    PC.Description,
    COUNT(*)            AS TotalPatrons,
    SUM(CASE WHEN PR.EmailAddress IS NOT NULL
                  AND PR.EmailAddress <> '' THEN 1 ELSE 0 END) AS PatronsWithEmail
FROM polaris.Patrons AS P WITH (NOLOCK)
JOIN polaris.PatronCodes AS PC WITH (NOLOCK)
    ON PC.PatronCodeID = P.PatronCodeID
LEFT JOIN polaris.PatronRegistration AS PR WITH (NOLOCK)
    ON PR.PatronID = P.PatronID
WHERE P.RecordStatusID = 1   -- active records only
GROUP BY P.PatronCodeID, PC.Description
ORDER BY TotalPatrons DESC;
