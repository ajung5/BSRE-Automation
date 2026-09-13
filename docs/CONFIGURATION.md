# Configuration

Project membaca konfigurasi dari file `.env`.

Salin template:

```text
.env.example
```

menjadi:

```text
.env
```

## Environment Variables

```env
BSRE_BASE_URL=https://example-bsre-api
BSRE_USERNAME=your_username
BSRE_PASSWORD=your_password

GOOGLE_CREDENTIALS=google_credentials.json
SPREADSHEET_ID=your_google_spreadsheet_id
WORKSHEET_NAME=Nama Worksheet
```

## Google Service Account

Simpan credential Google Service Account pada path yang ditentukan oleh:

```env
GOOGLE_CREDENTIALS=google_credentials.json
```

Temukan `client_email` pada credential:

```json
{
  "client_email": "service-account-name@project-id.iam.gserviceaccount.com"
}
```

Share Google Spreadsheet ke email service account tersebut dengan akses:

```text
Editor
```

## Spreadsheet

Pastikan:

- `SPREADSHEET_ID` sesuai spreadsheet target;
- `WORKSHEET_NAME` sama persis dengan nama worksheet;
- data memiliki kolom NIK;
- kolom O/P/Q/R tersedia untuk hasil sinkronisasi.

## Kolom Output

| Kolom | Data |
|---|---|
| O | Status Pengguna |
| P | Status Sertifikat |
| Q | Tanggal terbit |
| R | Tanggal berakhir |

## Security

`.env` dan file credential tidak boleh di-commit.

Repository sudah seharusnya mengabaikan:

```text
.env
*.env
google_credentials.json
*credentials*.json
```

Lihat juga [../SECURITY.md](../SECURITY.md).
