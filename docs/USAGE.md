# Usage

## Mode 1 — Filtered / Visible Rows

File:

```text
cek_nik_bsre_spreadseheet_merge.py
```

Mode ini hanya memproses row yang terlihat. Row yang disembunyikan oleh filter atau user tidak diproses.

Windows:

```powershell
python .\cek_nik_bsre_spreadseheet_merge.py
```

macOS/Linux:

```bash
python3 cek_nik_bsre_spreadseheet_merge.py
```

## Mode 2 — All Rows

File:

```text
cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Mode ini memproses seluruh row data tanpa dipengaruhi filter/hidden row.

Windows:

```powershell
python .\cek_nik_bsre_spreadseheet_merge_all_rows.py
```

macOS/Linux:

```bash
python3 cek_nik_bsre_spreadseheet_merge_all_rows.py
```

## Mapping Status

Mapping utama pada source saat ini:

| Status API | Status Pengguna | Status Sertifikat |
|---|---|---|
| `ISSUE` | Verified | Issued |
| `REVOKE` | Verified | Revoke |
| `RENEW` | Verified | Renew |
| `NO_CERTIFICATE` | Verified | New |
| `EXPIRED` | Verified | Expired |
| `NOT_REGISTERED` | Tidak diubah | Tidak diubah |

## Differential Update

Script membandingkan nilai API dengan nilai yang sudah ada di spreadsheet.

Contoh:

```text
O lama = Verified
P lama = Issued
Q lama = 12-Agu-2024
R lama = 12-Agu-2026

API:
O baru = Verified
P baru = Expired
Q baru = 2024-08-12
R baru = 2026-08-12
```

Hasil:

```text
O → tidak ditulis ulang
P → di-update
Q → tidak ditulis ulang
R → tidak ditulis ulang
```

Tanggal dinormalisasi sebelum dibandingkan agar perbedaan format tampilan tidak dianggap sebagai perubahan data.

## Exit Code

Untuk automation Windows, `run_bsre.ps1` meneruskan exit code proses Python. Gunakan nilai tersebut untuk mendeteksi keberhasilan atau kegagalan task.
