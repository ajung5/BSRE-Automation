# Repository Structure

Rekomendasi struktur final:

```text
BSRE-Automation/
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── INSTALLATION.md
│   ├── LOGGING.md
│   ├── TESTING.md
│   ├── TROUBLESHOOTING.md
│   ├── USAGE.md
│   └── WINDOWS_TASK_SCHEDULER.md
├── tests/
│   └── test_both_bsre_modes.py
├── .env.example
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── REPOSITORY_STRUCTURE.md
├── SECURITY.md
├── requirements.txt
├── cek_nik_bsre_spreadseheet_merge.py
├── cek_nik_bsre_spreadseheet_merge_all_rows.py
└── run_bsre.ps1
```

File source existing tetap berada di root agar path pada `run_bsre.ps1` dan penggunaan saat ini tidak perlu diubah.
