# BSRE Automation

Automasi sinkronisasi **status pengguna dan sertifikat elektronik BSrE** dari API ke Google Spreadsheet berdasarkan NIK.

Project menyediakan dua mode:

- **Filtered / Visible Rows** — hanya row yang terlihat.
- **All Rows** — seluruh row, termasuk hidden/filter.

Keduanya menggunakan **strict differential write**: Google Sheets hanya menerima update untuk cell O/P/Q/R yang secara semantik benar-benar berubah.

## Perbaikan Date Idempotency

Versi patch 26 September 2026 memperketat perilaku Q/R:

- tanggal dibandingkan setelah normalisasi;
- format tampilan yang berbeda tetapi tanggalnya sama tidak dianggap perubahan;
- mendukung format numerik, dua-digit year, nama bulan Indonesia/Inggris, dan datetime;
- `NO_CERTIFICATE`, `NOT_FOUND`, `NO_DATA`, dan `NO_CERTIFICATE_DATE` **tidak menghapus tanggal lama**;
- update tanggal dicatat dengan `[DATE-DIFF]` berisi raw value dan normalized value;
- tanggal yang dipertahankan dicatat sebagai `[DATE-PRESERVE]`;
- tidak ada write atau format massal ke `Q2:R`;
- wrapper Windows memiliki single-instance mutex untuk mencegah concurrent sync;
- mode all-rows mengembalikan exit code non-zero jika terjadi exception.

Tujuan utamanya adalah **idempotency**: bila data API dan spreadsheet tidak berubah, run berikutnya harus menghasilkan **0 write**.

## Kolom Spreadsheet

| Kolom | Fungsi |
|---|---|
| C / NIK | sumber NIK |
| O | Status Pengguna |
| P | Status Sertifikat |
| Q | Tanggal terbit |
| R | Tanggal berakhir |

## Kebijakan tanggal

### Profile SUCCESS

Q/R dibandingkan dengan nilai lama setelah normalisasi. Hanya tanggal yang benar-benar berbeda yang ditulis.

### Profile tidak usable

Status berikut dianggap tidak cukup kuat untuk menghapus data historis:

```text
NO_CERTIFICATE
NOT_FOUND
NO_DATA
NO_CERTIFICATE_DATE
```

Q/R lama dipertahankan.

### Sumber tanggal terbit

Jika object sertifikat menyediakan field tanggal mulai/terbit yang dikenali, nilainya dipakai. Candidate field:

```text
berlaku_mulai
tanggal_terbit
tanggal_mulai
not_before
valid_from
```

Jika tidak ada field valid, compatibility fallback lama tetap dipakai:

```text
tanggal terbit = tanggal berakhir - 2 tahun
```

Tanggal berakhir dicari dari candidate field:

```text
berlaku_sampai
tanggal_berakhir
not_after
valid_to
```

## Menjalankan

All rows:

```bash
python cek_nik_bsre_spreadseheet_merge_all_rows.py
```

Filtered rows:

```bash
python cek_nik_bsre_spreadseheet_merge.py
```

Windows scheduled wrapper:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\BSRE-Automation\run_bsre.ps1"
```

## Regression test

```bash
python -m unittest tests.test_both_bsre_modes -v
```

Test mencakup:

- equivalent date formats;
- strict differential write;
- preservation Q/R pada profile tidak usable;
- pemilihan sertifikat dengan expiry terbaru;
- penggunaan actual issue-date field bila tersedia;
- fallback legacy expiry minus dua tahun;
- filtered-row behavior;
- guard terhadap mass formatting;
- guard exit code all-rows;
- guard single-instance wrapper.

## Log penting

Perubahan tanggal nyata:

```text
[DATE-DIFF] R128 | old_raw='12-Agu-2026' old_norm='2026-08-12' | new_raw='2027-08-12' new_norm='2027-08-12' | source=berlaku_sampai
```

Data lama dipertahankan karena profile tidak usable:

```text
[DATE-PRESERVE] row=128 status=NO_CERTIFICATE | Q='12-Agu-2024' R='12-Agu-2026'
```

## Dokumentasi

| Dokumen | Isi |
|---|---|
| `APPLY_PATCH.md` | langkah replace dan acceptance criteria |
| `docs/BUGFIX_DATE_IDEMPOTENCY.md` | root cause dan desain perbaikan |
| `docs/LOGGING.md` | diagnostic/audit log |
| `docs/TESTING.md` | regression test |
| `docs/TROUBLESHOOTING.md` | diagnosis bila Q/R masih berubah |
| `docs/WINDOWS_TASK_SCHEDULER.md` | scheduler dan concurrency guard |

## Security

Jangan commit `.env`, Google service-account JSON, username/password API, log produksi, atau export spreadsheet yang mengandung NIK.
