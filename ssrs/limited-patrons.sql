-- limited-patrons.sql
-- ============================================================
-- SSRS report query for the LIMITED / RESTRICTED patron tier.
-- Powers the "Restricted Card" banner in Gmail.
--
-- RHPL example PatronCodes: 2, 4, 9, 17
-- These map to card types that restrict patrons from placing
-- holds, booking meeting rooms, or registering for events
-- (e.g., Non-Resident Limited, Reciprocal Borrower, Homebound,
-- Temporary card types).
--
-- TO ADAPT FOR YOUR LIBRARY:
--   1. Run discover-patron-codes.sql to identify your code IDs.
--   2. Replace the IN (...) values with your restricted/limited codes.
--   3. Replace '%@rhpl.org' with your staff email domain filter.
--
-- SSRS subscription settings:
--   Format:  CSV (comma delimited)
--   Deliver: Email to your sync mailbox
--   Subject: Sublime Limited Patron Export   ← must match .env exactly
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
  AND P.PatronCodeID IN (2, 4, 9, 17)                             -- RHPL limited card codes; replace with yours
  AND P.RecordStatusID = 1
ORDER BY EmailAddress;
