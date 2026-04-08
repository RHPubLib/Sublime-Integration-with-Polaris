-- digital-patrons.sql
-- ============================================================
-- SSRS report query for the DIGITAL / E-CARD patron tier.
-- Powers the "E-Card / Digital Card" banner in Gmail.
--
-- RHPL example PatronCodes: 15, 20, 27
-- These map to eCard, Digital Access Card, and similar
-- card types that provide eContent access only (no physical
-- item checkout, no room booking, no event registration).
--
-- TO ADAPT FOR YOUR LIBRARY:
--   1. Run discover-patron-codes.sql to identify your code IDs.
--   2. Replace the IN (...) values with your digital-only codes.
--   3. Replace '%@rhpl.org' with your staff email domain filter.
--
-- SSRS subscription settings:
--   Format:  CSV (comma delimited)
--   Deliver: Email to your sync mailbox
--   Subject: Sublime Digital Patron Export   ← must match .env exactly
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
  AND P.PatronCodeID IN (15, 20, 27)                               -- RHPL digital card codes; replace with yours
  AND P.RecordStatusID = 1
ORDER BY EmailAddress;
