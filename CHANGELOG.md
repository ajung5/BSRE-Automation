# Changelog

Format mengikuti prinsip Keep a Changelog.

## [Unreleased]

### Fixed — 2026-09-26

- Memperbaiki destructive date update: `NO_CERTIFICATE`, `NOT_FOUND`, `NO_DATA`, dan `NO_CERTIFICATE_DATE` tidak lagi mengosongkan Q/R yang sudah memiliki data.
- Memperluas normalisasi tanggal agar format tampilan Google Sheets yang ekuivalen tidak dianggap perubahan.
- Menambahkan dukungan `dd.mm.yyyy`, dua digit year, datetime, ISO datetime, nama bulan Indonesia/Inggris.
- Memperbaiki all-rows error handling agar exception menghasilkan exit code `1`.
- Menambahkan single-instance mutex pada `run_bsre.ps1` untuk mencegah concurrent execution.

### Changed — 2026-09-26

- Tanggal terbit memprioritaskan field aktual pada response sertifikat bila tersedia; fallback `expiry - 2 years` tetap dipertahankan untuk backward compatibility.
- Parser tanggal berakhir menerima beberapa candidate field tanpa mengubah behavior apabila API tetap memakai `berlaku_sampai`.
- Menambahkan statistik `Tanggal dipertahankan`.
- Menambahkan log `[DATE-DIFF]` dan `[DATE-PRESERVE]`.

### Tests — 2026-09-26

- Regression test untuk non-destructive date policy.
- Regression test equivalent date formats/idempotency.
- Regression test exact-cell update.
- Regression test actual issue-date field dan fallback legacy.
- Static regression guard terhadap mass formatting Q2:R.
- Static regression guard exit code all-rows.
- Static regression guard single-instance Task Scheduler wrapper.

### Documentation

- Menambahkan `docs/BUGFIX_DATE_IDEMPOTENCY.md`.
- Memperbarui README, logging, testing, troubleshooting, dan Task Scheduler guide.
