# Installation

## Requirements

- Python 3.10+
- Git
- akses ke API BSrE yang sah
- Google Service Account
- akses Editor ke Google Spreadsheet target
- PowerShell jika menggunakan automation Windows

## Clone Repository

```bash
git clone https://github.com/ajung5/BSRE-Automation.git
cd BSRE-Automation
```

## Windows

Buat virtual environment:

```powershell
python -m venv venv
```

Aktifkan:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependency:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Verifikasi

Windows:

```powershell
python --version
python -m pip list
```

macOS/Linux:

```bash
python3 --version
python3 -m pip list
```

Setelah dependency terpasang, lanjut ke [CONFIGURATION.md](CONFIGURATION.md).
