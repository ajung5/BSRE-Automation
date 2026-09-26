import gspread
import requests
import time
import os
import sys
import re

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from tqdm import tqdm
from google.oauth2.service_account import Credentials

# ============================================================
# KONFIGURASI
# ============================================================

load_dotenv()

BASE_URL = os.getenv("BSRE_BASE_URL")
USERNAME = os.getenv("BSRE_USERNAME")
PASSWORD = os.getenv("BSRE_PASSWORD")

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

STATUS_MAPPING = {
    "ISSUE": "Issued",
    "REVOKE": "Revoke",
    "RENEW": "Renew",
    "NO_CERTIFICATE": "New",
    "EXPIRED": "Expired",
}

REQUEST_DELAY = 0.1
HEARTBEAT_INTERVAL = 500

# Field alternatif hanya dibaca jika memang ada pada response API.
# Fallback perilaku lama tetap dipertahankan.
ISSUE_DATE_FIELDS = (
    "berlaku_mulai",
    "tanggal_terbit",
    "tanggal_mulai",
    "not_before",
    "valid_from",
)

EXPIRY_DATE_FIELDS = (
    "berlaku_sampai",
    "tanggal_berakhir",
    "not_after",
    "valid_to",
)

BULAN_MAPPING = {
    "jan": 1,
    "januari": 1,
    "january": 1,
    "feb": 2,
    "februari": 2,
    "february": 2,
    "mar": 3,
    "maret": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "mei": 5,
    "may": 5,
    "jun": 6,
    "juni": 6,
    "june": 6,
    "jul": 7,
    "juli": 7,
    "july": 7,
    "agu": 8,
    "agustus": 8,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "okt": 10,
    "oktober": 10,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "des": 12,
    "desember": 12,
    "dec": 12,
    "december": 12,
}


# ============================================================
# HELPER
# ============================================================


def ambil_nilai_cell(row, index):
    """Mengambil nilai cell secara aman. O=14, P=15, Q=16, R=17."""
    if len(row) > index:
        return str(row[index]).strip()
    return ""


def _format_tahun_2_digit(tahun):
    """Mengubah 2 digit year menjadi 4 digit mengikuti datetime %y."""
    if len(tahun) == 2:
        return datetime.strptime(tahun, "%y").strftime("%Y")
    return tahun


def normalisasi_tanggal(value):
    """
    Normalisasi tanggal ke YYYY-MM-DD untuk perbandingan idempotent.

    Format yang ditangani antara lain:
    - 2026-08-12
    - 12-08-2026 / 12/08/2026 / 12.08.2026
    - 12-08-26 / 12/08/26 / 12.08.26
    - 12-Agu-2026 / 12-Aug-2026 / 12 Agustus 2026
    - 2026-08-12 00:00:00 / ISO datetime

    Jika format tidak dikenali, nilai asli dikembalikan supaya perbedaan
    nyata tetap terdeteksi dan dapat dilihat pada diagnostic log.
    """
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    value = str(value).strip()
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value)

    # ISO datetime, termasuk bentuk dengan timezone/Z.
    if re.match(r"^\d{4}-\d{1,2}-\d{1,2}[T ]", value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%d.%m.%y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # dd-Bulan-yyyy / yyyy-Bulan-dd; separator -, /, ., atau spasi.
    match = re.match(
        r"^(\d{1,4})[-/. ]+([A-Za-z]+)[-/. ]+(\d{1,4})(?:[ T].*)?$",
        value,
        flags=re.IGNORECASE,
    )
    if match:
        p1, bulan_text, p3 = match.groups()
        bulan = BULAN_MAPPING.get(bulan_text.lower().rstrip("."))
        if bulan:
            try:
                if len(p1) == 4:
                    tahun = int(p1)
                    hari = int(p3)
                else:
                    hari = int(p1)
                    tahun = int(_format_tahun_2_digit(p3))

                parsed = datetime(tahun, bulan, hari)
                return parsed.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

    return value


def tanggal_iso_valid(value):
    """True bila value dapat dinormalisasi menjadi tanggal ISO valid."""
    normalized = normalisasi_tanggal(value)
    try:
        datetime.strptime(normalized, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def nilai_teks_berubah(nilai_lama, nilai_baru):
    lama = "" if nilai_lama is None else str(nilai_lama).strip()
    baru = "" if nilai_baru is None else str(nilai_baru).strip()
    return lama != baru


def nilai_tanggal_berubah(nilai_lama, nilai_baru):
    return normalisasi_tanggal(nilai_lama) != normalisasi_tanggal(nilai_baru)


def _ambil_field_tanggal(certificate, candidates):
    for field in candidates:
        raw = certificate.get(field)
        if raw not in (None, "") and tanggal_iso_valid(raw):
            return normalisasi_tanggal(raw), field
    return None, None


def ekstrak_tanggal_sertifikat(certificate):
    """
    Mengambil tanggal terbit/berakhir dari object sertifikat.

    Tanggal berakhir wajib valid agar sertifikat dapat dipakai.
    Tanggal terbit memakai field API jika tersedia; jika tidak tersedia,
    mempertahankan fallback legacy: tanggal berakhir - 2 tahun.
    """
    tanggal_berakhir, expiry_field = _ambil_field_tanggal(
        certificate,
        EXPIRY_DATE_FIELDS,
    )
    if not tanggal_berakhir:
        return None

    expired_dt = datetime.strptime(tanggal_berakhir, "%Y-%m-%d")

    tanggal_terbit, issue_field = _ambil_field_tanggal(
        certificate,
        ISSUE_DATE_FIELDS,
    )

    if tanggal_terbit:
        sumber_terbit = issue_field
    else:
        tanggal_terbit = (expired_dt - relativedelta(years=2)).strftime("%Y-%m-%d")
        sumber_terbit = "fallback_expiry_minus_2_years"

    return {
        "tanggal_expired_dt": expired_dt,
        "tanggal_terbit": tanggal_terbit,
        "tanggal_berakhir": tanggal_berakhir,
        "sumber_tanggal_terbit": sumber_terbit,
        "sumber_tanggal_berakhir": expiry_field,
        "data": certificate,
    }


def log_date_diff(cell, nilai_lama, nilai_baru, source=None):
    extra = f" | source={source}" if source else ""
    print(
        f"[DATE-DIFF] {cell} | "
        f"old_raw={nilai_lama!r} old_norm={normalisasi_tanggal(nilai_lama)!r} | "
        f"new_raw={nilai_baru!r} new_norm={normalisasi_tanggal(nilai_baru)!r}"
        f"{extra}"
    )


def log_date_preserve(nomor_baris, status_prof, tanggal_terbit_lama, tanggal_berakhir_lama):
    if tanggal_terbit_lama or tanggal_berakhir_lama:
        print(
            f"[DATE-PRESERVE] row={nomor_baris} status={status_prof} | "
            f"Q={tanggal_terbit_lama!r} R={tanggal_berakhir_lama!r}"
        )


# ============================================================
# KONEKSI GOOGLE
# ============================================================


def koneksi_google():
    if not GOOGLE_CREDENTIALS:
        raise ValueError("\nGOOGLE_CREDENTIALS belum diisi pada file .env.")

    if not os.path.exists(GOOGLE_CREDENTIALS):
        raise FileNotFoundError(
            f"\nFile credential Google tidak ditemukan: {GOOGLE_CREDENTIALS}\n"
            "Pastikan path GOOGLE_CREDENTIALS pada file .env sudah benar."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS,
        scopes=scopes,
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return client, spreadsheet, worksheet


# ============================================================
# API BSrE
# ============================================================


def cek_profile_sertifikat(nik):
    if not BASE_URL or not USERNAME or not PASSWORD:
        return None

    url = f"{BASE_URL}/api/user/profile/{nik}"

    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            success = data.get("success", False)

            if not success:
                return {
                    "status": "NO_DATA",
                    "tanggal_terbit": None,
                    "tanggal_berakhir": None,
                }

            profile_data = data.get("data", {}) or {}
            certificates = profile_data.get("sertifikat", []) or []

            if not certificates:
                return {
                    "status": "NO_CERTIFICATE",
                    "tanggal_terbit": None,
                    "tanggal_berakhir": None,
                }

            daftar_sertifikat_valid = []
            for certificate in certificates:
                if not isinstance(certificate, dict):
                    continue
                parsed = ekstrak_tanggal_sertifikat(certificate)
                if parsed:
                    daftar_sertifikat_valid.append(parsed)

            if not daftar_sertifikat_valid:
                return {
                    "status": "NO_CERTIFICATE_DATE",
                    "tanggal_terbit": None,
                    "tanggal_berakhir": None,
                }

            certificate_terbaru = max(
                daftar_sertifikat_valid,
                key=lambda item: item["tanggal_expired_dt"],
            )

            return {
                "status": "SUCCESS",
                "tanggal_terbit": certificate_terbaru["tanggal_terbit"],
                "tanggal_berakhir": certificate_terbaru["tanggal_berakhir"],
                "sumber_tanggal_terbit": certificate_terbaru["sumber_tanggal_terbit"],
                "sumber_tanggal_berakhir": certificate_terbaru["sumber_tanggal_berakhir"],
            }

        if response.status_code == 401:
            print(f"\nUNAUTHORIZED - NIK {nik} (Profile)")
            return None

        if response.status_code == 404:
            return {
                "status": "NOT_FOUND",
                "tanggal_terbit": None,
                "tanggal_berakhir": None,
            }

        print(f"\nHTTP ERROR {response.status_code} - NIK {nik} (Profile)")
        return None

    except Exception as e:
        print(f"\nERROR PROFILE - NIK {nik}: {e}")
        return None


def cek_status_sertifikat(nik):
    if not BASE_URL or not USERNAME or not PASSWORD:
        return None

    url = f"{BASE_URL}/api/user/status/{nik}"

    try:
        response = requests.get(
            url,
            auth=(USERNAME, PASSWORD),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            status_api = str(data.get("status", "")).strip().upper()

            if status_api == "NOT_REGISTERED":
                return {
                    "update": False,
                    "status_api": status_api,
                    "status_pengguna": None,
                    "status_sertifikat": None,
                }

            if status_api in STATUS_MAPPING:
                return {
                    "update": True,
                    "status_api": status_api,
                    "status_pengguna": "Verified",
                    "status_sertifikat": STATUS_MAPPING[status_api],
                }

            return {
                "update": False,
                "status_api": status_api,
                "status_pengguna": None,
                "status_sertifikat": None,
            }

        if response.status_code == 401:
            print(f"\nUNAUTHORIZED - NIK {nik} (Status)")
            return None

        print(f"\nHTTP ERROR {response.status_code} - NIK {nik} (Status)")
        return None

    except Exception as e:
        print(f"\nERROR STATUS - NIK {nik}: {e}")
        return None


# ============================================================
# PROSES GOOGLE SHEETS
# ============================================================


def proses_google_sheet():
    print("\n" + "=" * 70)
    print(" CEK STATUS DAN TANGGAL SERTIFIKAT ELEKTRONIK BSrE")
    print("=" * 70 + "\n")

    if not SPREADSHEET_ID or SPREADSHEET_ID == "ISI_ID_GOOGLE_SPREADSHEET":
        raise ValueError("\nSPREADSHEET_ID belum diisi.")
    if not WORKSHEET_NAME:
        raise ValueError("\nWORKSHEET_NAME belum diisi.")

    print("Menghubungkan ke Google Spreadsheet...")
    _, _, worksheet = koneksi_google()
    print("Berhasil terhubung.\n")

    print("Mengambil seluruh data spreadsheet...")
    data = worksheet.get_all_values()
    if not data:
        print("Spreadsheet kosong.")
        return

    header = data[0]
    try:
        kolom_nik_index = header.index("NIK") + 1
    except ValueError as exc:
        raise ValueError("\nKolom 'NIK' tidak ditemukan.") from exc

    if kolom_nik_index != 3:
        print(
            f"\nPERINGATAN: Kolom NIK ditemukan di posisi {kolom_nik_index}, "
            "bukan kolom C.\n"
        )

    header_updates = []
    if ambil_nilai_cell(header, 16) != "Tanggal terbit":
        header_updates.append({"range": "Q1", "values": [["Tanggal terbit"]]})
    if ambil_nilai_cell(header, 17) != "Tanggal berakhir":
        header_updates.append({"range": "R1", "values": [["Tanggal berakhir"]]})

    if header_updates:
        worksheet.batch_update(header_updates, value_input_option="USER_ENTERED")
        print("\nHeader yang diperbarui:")
        for item in header_updates:
            print(f"- {item['range']}")

    total_row = len(data) - 1
    semua_row_data = list(range(2, len(data) + 1))

    print(f"\nTotal row data       : {total_row}")
    print(f"Total row diproses   : {len(semua_row_data)}")
    print("Mode                 : SEMUA ROW")
    print("Update               : HANYA CELL O/P/Q/R YANG BERUBAH")
    print("Date policy          : PRESERVE existing Q/R jika profile tidak usable")
    print(f"Heartbeat            : SETIAP {HEARTBEAT_INTERVAL} ROW\n")

    update_cells = []
    row_yang_diubah = set()

    perubahan_o = perubahan_p = perubahan_q = perubahan_r = 0
    jumlah_row_tanpa_perubahan = 0
    jumlah_tanggal_dipertahankan = 0

    jumlah_sukses = 0
    jumlah_tidak_ada_sertifikat = 0
    jumlah_tidak_ditemukan = 0
    jumlah_tanggal_tidak_valid = 0
    jumlah_no_data = 0

    jumlah_issue = jumlah_revoke = jumlah_renew = 0
    jumlah_no_certificate = jumlah_expired = 0
    jumlah_not_registered = jumlah_tidak_diubah = 0
    jumlah_nik_kosong = jumlah_error = 0

    waktu_mulai_proses = time.monotonic()
    total_diproses = len(semua_row_data)

    def format_durasi(total_detik):
        total_detik = max(0, int(total_detik))
        jam, sisa = divmod(total_detik, 3600)
        menit, detik = divmod(sisa, 60)
        return f"{jam:02d}:{menit:02d}:{detik:02d}"

    def cetak_heartbeat(jumlah_selesai):
        if jumlah_selesai <= 0 or total_diproses <= 0:
            return
        elapsed = time.monotonic() - waktu_mulai_proses
        progress = (jumlah_selesai / total_diproses) * 100
        rata_rata_per_row = elapsed / jumlah_selesai
        estimasi_sisa = rata_rata_per_row * (total_diproses - jumlah_selesai)
        print(
            f"Progress : {jumlah_selesai} / {total_diproses} "
            f"({progress:.2f}%) | Elapsed: {format_durasi(elapsed)} | "
            f"ETA: {format_durasi(estimasi_sisa)}",
            flush=True,
        )

    for index_proses, nomor_baris in enumerate(
        tqdm(
            semua_row_data,
            total=len(semua_row_data),
            desc="Checking NIK",
            disable=not sys.stdout.isatty(),
        ),
        start=1,
    ):
        selesai_sebelumnya = index_proses - 1
        if selesai_sebelumnya > 0 and selesai_sebelumnya % HEARTBEAT_INTERVAL == 0:
            cetak_heartbeat(selesai_sebelumnya)

        row = data[nomor_baris - 1]
        nik = (
            str(row[kolom_nik_index - 1]).strip()
            if len(row) >= kolom_nik_index
            else ""
        )
        if not nik or nik.lower() in {"nan", "none"}:
            jumlah_nik_kosong += 1
            continue

        hasil_status = cek_status_sertifikat(nik)
        hasil_profile = cek_profile_sertifikat(nik)

        if hasil_status is None or hasil_profile is None:
            jumlah_error += 1
            time.sleep(REQUEST_DELAY)
            continue

        row_updated = False

        status_pengguna_lama = ambil_nilai_cell(row, 14)
        status_sertifikat_lama = ambil_nilai_cell(row, 15)
        tanggal_terbit_lama = ambil_nilai_cell(row, 16)
        tanggal_berakhir_lama = ambil_nilai_cell(row, 17)

        # ---------------- STATUS O/P ----------------
        if hasil_status["update"]:
            status_pengguna_baru = hasil_status["status_pengguna"]
            status_sertifikat_baru = hasil_status["status_sertifikat"]

            if nilai_teks_berubah(status_pengguna_lama, status_pengguna_baru):
                update_cells.append({
                    "range": f"O{nomor_baris}",
                    "values": [[status_pengguna_baru]],
                })
                perubahan_o += 1
                row_updated = True

            if nilai_teks_berubah(status_sertifikat_lama, status_sertifikat_baru):
                update_cells.append({
                    "range": f"P{nomor_baris}",
                    "values": [[status_sertifikat_baru]],
                })
                perubahan_p += 1
                row_updated = True

            status_api = hasil_status["status_api"]
            if status_api == "ISSUE":
                jumlah_issue += 1
            elif status_api == "REVOKE":
                jumlah_revoke += 1
            elif status_api == "RENEW":
                jumlah_renew += 1
            elif status_api == "NO_CERTIFICATE":
                jumlah_no_certificate += 1
            elif status_api == "EXPIRED":
                jumlah_expired += 1
        else:
            if hasil_status.get("status_api") == "NOT_REGISTERED":
                jumlah_not_registered += 1
            else:
                jumlah_tidak_diubah += 1

        # ---------------- TANGGAL Q/R ----------------
        status_prof = hasil_profile.get("status", "")
        tanggal_terbit_baru = None
        tanggal_berakhir_baru = None

        if status_prof == "SUCCESS":
            tanggal_terbit_baru = hasil_profile.get("tanggal_terbit")
            tanggal_berakhir_baru = hasil_profile.get("tanggal_berakhir")
            jumlah_sukses += 1
        elif status_prof == "NO_CERTIFICATE":
            jumlah_tidak_ada_sertifikat += 1
        elif status_prof == "NOT_FOUND":
            jumlah_tidak_ditemukan += 1
        elif status_prof == "NO_CERTIFICATE_DATE":
            jumlah_tanggal_tidak_valid += 1
        elif status_prof == "NO_DATA":
            jumlah_no_data += 1

        # Non-destructive policy: profile yang tidak usable tidak boleh
        # menghapus/mengubah Q/R yang sudah ada.
        if status_prof != "SUCCESS":
            if tanggal_terbit_lama or tanggal_berakhir_lama:
                jumlah_tanggal_dipertahankan += 1
            log_date_preserve(
                nomor_baris,
                status_prof,
                tanggal_terbit_lama,
                tanggal_berakhir_lama,
            )

        if tanggal_terbit_baru is not None and nilai_tanggal_berubah(
            tanggal_terbit_lama,
            tanggal_terbit_baru,
        ):
            log_date_diff(
                f"Q{nomor_baris}",
                tanggal_terbit_lama,
                tanggal_terbit_baru,
                hasil_profile.get("sumber_tanggal_terbit"),
            )
            update_cells.append({
                "range": f"Q{nomor_baris}",
                "values": [[tanggal_terbit_baru]],
            })
            perubahan_q += 1
            row_updated = True

        if tanggal_berakhir_baru is not None and nilai_tanggal_berubah(
            tanggal_berakhir_lama,
            tanggal_berakhir_baru,
        ):
            log_date_diff(
                f"R{nomor_baris}",
                tanggal_berakhir_lama,
                tanggal_berakhir_baru,
                hasil_profile.get("sumber_tanggal_berakhir"),
            )
            update_cells.append({
                "range": f"R{nomor_baris}",
                "values": [[tanggal_berakhir_baru]],
            })
            perubahan_r += 1
            row_updated = True

        if row_updated:
            row_yang_diubah.add(nomor_baris)
        else:
            jumlah_row_tanpa_perubahan += 1

        time.sleep(REQUEST_DELAY)

    if total_diproses > 0:
        cetak_heartbeat(total_diproses)

    print("\nMengupdate Google Spreadsheet...\n")
    if update_cells:
        worksheet.batch_update(update_cells, value_input_option="USER_ENTERED")
        print(f"Berhasil mengupdate {len(update_cells)} cell yang benar-benar berubah.")
        print("\nCell yang diperbarui:")
        for item in update_cells:
            print(f"- {item['range']}")
    else:
        print("Tidak ada perubahan data. Tidak ada cell O/P/Q/R yang diupdate.")

    total_cell_berubah = perubahan_o + perubahan_p + perubahan_q + perubahan_r
    if total_cell_berubah != len(update_cells):
        raise RuntimeError(
            "Inkonsistensi internal: total_cell_berubah "
            f"({total_cell_berubah}) != jumlah update_cells ({len(update_cells)})."
        )

    print("\n" + "=" * 70)
    print(" HASIL PENGECEKAN")
    print("=" * 70 + "\n")
    print(f"Total row data            : {total_row}")
    print(f"Total row diproses        : {len(semua_row_data)}")
    print(f"Total row berubah         : {len(row_yang_diubah)}")
    print(f"Total row tanpa perubahan : {jumlah_row_tanpa_perubahan}")
    print(f"Total cell berubah        : {total_cell_berubah}")
    print(f"Tanggal dipertahankan     : {jumlah_tanggal_dipertahankan}\n")

    print("--- PERUBAHAN CELL ---")
    print(f"Status Pengguna (O)       : {perubahan_o}")
    print(f"Status Sertifikat (P)     : {perubahan_p}")
    print(f"Tanggal terbit (Q)        : {perubahan_q}")
    print(f"Tanggal berakhir (R)      : {perubahan_r}\n")

    print("--- STATISTIK STATUS ---")
    print(f"ISSUE              : {jumlah_issue}")
    print(f"EXPIRED            : {jumlah_expired}")
    print(f"REVOKE             : {jumlah_revoke}")
    print(f"RENEW              : {jumlah_renew}")
    print(f"NO_CERTIFICATE     : {jumlah_no_certificate}")
    print(f"NOT_REGISTERED     : {jumlah_not_registered}")
    print(f"Tidak diubah       : {jumlah_tidak_diubah}\n")

    print("--- STATISTIK PROFILE ---")
    print(f"Tanggal ditemukan         : {jumlah_sukses}")
    print(f"Tidak ada sertifikat      : {jumlah_tidak_ada_sertifikat}")
    print(f"NIK tidak ditemukan       : {jumlah_tidak_ditemukan}")
    print(f"Tanggal tidak valid       : {jumlah_tanggal_tidak_valid}")
    print(f"Profile tanpa data        : {jumlah_no_data}\n")

    print(f"NIK kosong                : {jumlah_nik_kosong}")
    print(f"Error gabungan            : {jumlah_error}\n")
    print("Google Sheets hanya diupdate pada cell O/P/Q/R yang berubah.")
    print("Q/R dipertahankan ketika profile BSrE tidak menyediakan tanggal usable.")
    print("Tidak ada write/format massal ke range Q2:R.\n")


if __name__ == "__main__":
    try:
        proses_google_sheet()
    except KeyboardInterrupt:
        print("\nProses dihentikan oleh pengguna.")
        sys.exit(130)
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70 + "\n")
        print(str(e))
        print()
        sys.exit(1)
