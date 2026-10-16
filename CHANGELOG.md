# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [0.2.0] - 2026-10-16
### Added
- Optional `mayor` step: when a bank statement is lost, supplement it with the accounting-ledger export of that bank account. Rows go to separate, labelled sheets (never merged with bank data); out-of-period rows are excluded and reported; HTML entities that split CSV rows are decoded first.
- Verification now also checks the ledger sheets (row count and totals) and keeps them out of the bank running-balance check.
- Tests for the ledger source (debit/credit crossing, entity decoding, out-of-period row, separate sheet and label).
### Documentation
- Lesson: a file that arrives again can be identical to one already loaded (compare `md5` first).

## [0.1.0] - 2026-10-16
### Added
- Claude Code skill `consolidar-extractos`: turns a messy folder of bank statements into one clean Excel workbook per bank.
- Content-based readers for xls / xlsx / csv tables (header synonyms) and text PDFs (three specific layouts + a low-confidence generic one).
- Pipeline steps: inventory, read, unify, pdf, excel, verify. Every step writes auditable CSV files.
- Independent verification that re-opens the generated workbooks and recomputes row counts, totals and running balance.
- End-to-end test with fully synthetic statements covering the real-world problems the tool was built to solve.
- GitHub Actions CI running the test suite on Python 3.10 - 3.13.
