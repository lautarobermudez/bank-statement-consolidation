# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [0.1.0] - 2026-10-16
### Added
- Claude Code skill `consolidar-extractos`: turns a messy folder of bank statements into one clean Excel workbook per bank.
- Content-based readers for xls / xlsx / csv tables (header synonyms) and text PDFs (three specific layouts + a low-confidence generic one).
- Pipeline steps: inventory, read, unify, pdf, excel, verify. Every step writes auditable CSV files.
- Independent verification that re-opens the generated workbooks and recomputes row counts, totals and running balance.
- End-to-end test with fully synthetic statements covering the real-world problems the tool was built to solve.
- GitHub Actions CI running the test suite on Python 3.10 - 3.13.
