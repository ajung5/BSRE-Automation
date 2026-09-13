# Security Policy

## Scope

Repository ini memproses data identitas dan menggunakan credential untuk mengakses API serta Google Spreadsheet. Perlakukan deployment produksi sebagai sistem yang menangani data sensitif.

## Jangan Commit Secret

Jangan pernah commit:

- `.env`;
- username/password API;
- token;
- Google Service Account JSON;
- private key;
- file export spreadsheet produksi;
- data NIK;
- log yang mengandung informasi sensitif.

Gunakan placeholder pada dokumentasi dan issue publik.

## Credential Management

Minimum recommendation:

- simpan secret di luar repository;
- batasi permission file `.env` dan credential;
- gunakan service account khusus;
- berikan akses hanya ke spreadsheet yang diperlukan;
- rotasi credential jika dicurigai terekspos;
- jangan menggunakan credential produksi pada test.

## Repository Public

Sebelum push:

```bash
git status
git diff --cached
```

Pastikan tidak ada secret atau data pribadi.

Jika secret pernah ter-commit, menghapus file pada commit terbaru **tidak cukup**. Secret harus segera dirotasi dan histori Git perlu ditangani sesuai prosedur organisasi.

## Windows Server / VPS

- gunakan account service dengan privilege minimum;
- batasi ACL directory project;
- lindungi `.env` dan credential JSON;
- batasi Remote Desktop;
- patch OS/Python secara berkala;
- review log dan scheduled task.

## Data Protection

NIK adalah data yang harus dilindungi. Hindari:

- mencetak NIK lengkap ke log tanpa kebutuhan;
- membagikan screenshot/log produksi ke issue publik;
- menyimpan backup tidak terenkripsi tanpa kontrol akses.

## Vulnerability Reporting

Jangan membuka public issue yang mengandung:

- credential;
- token;
- private endpoint;
- data NIK;
- informasi akses sistem produksi.

Laporkan isu keamanan secara privat kepada maintainer repository.
