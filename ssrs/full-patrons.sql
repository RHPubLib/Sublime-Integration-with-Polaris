-- full-patrons.sql
-- ============================================================
-- SSRS report query for the FULL / VERIFIED patron tier.
-- Powers the "Verified Patron" banner in Gmail.
--
-- RHPL example PatronCodes: 1, 3, 6, 8, 14, 24, 25, 26, 29
-- These map to: Resident Adult/Juvenile/Senior, Non-Resident,
-- MILibrary Card, OTBS, and similar full-privilege card types.
--
-- TO ADAPT FOR YOUR LIBRARY:
--   1. Run discover-patron-codes.sql to identify your code IDs.
--   2. Replace the IN (...) values with your full-privilege codes.
--   3. Replace '%@rhpl.org' with your staff email domain filter.
--
-- SSRS subscription settings:
--   Format:  CSV (comma delimited)
--   Deliver: Email to your sync mailbox
--   Subject: Sublime Full Patron Export   ← must match .env exactly
--   Schedule: Nightly, before the sync script fires
-- ============================================================

SELECT DISTINCT
    LOWER(LTRIM(RTRIM(PR.EmailAddress))) AS EmailAddress
FROM polaris.PatronRegistration AS PR WITH (NOLOCK)
JOIN polaris.Patrons AS P WITH (NOLOCK)
    ON P.PatronID = PR.PatronID
WHERE PR.EmailAddress IS NOT NULL
  AND PR.EmailAddress <> ''
  AND LOWER(RTRIM(LTRIM(PR.EmailAddress))) NOT LIKE '%@rhpl.org'  -- exclude staff; change to your domain
  AND P.PatronCodeID IN (1, 3, 6, 8, 14, 24, 25, 26, 29)         -- RHPL full-privilege codes; replace with yours
  AND P.RecordStatusID = 1
ORDER BY EmailAddress;
