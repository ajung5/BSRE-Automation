import re
import unittest
from datetime import datetime
from unittest.mock import patch

import requests

import cek_nik_bsre_spreadseheet_merge as filtered_app
import cek_nik_bsre_spreadseheet_merge_all_rows as all_rows_app


class status_pengguna:
    """Concrete shared implementation used by both BSrE test modes."""

    BASE_URL = "https://example.test"
    USERNAME = ""
    PASSWORD = ""
    requests = requests

    @staticmethod
    def normalisasi_tanggal(value):
        if value is None:
            return ""
        value = str(value).strip()
        if not value:
            return ""
        month_map = {
            "jan": "01",
            "feb": "02",
            "mar": "03",
            "apr": "04",
            "mei": "05",
            "jun": "06",
            "jul": "07",
            "agu": "08",
            "aug": "08",
            "sep": "09",
            "okt": "10",
            "oct": "10",
            "nov": "11",
            "des": "12",
            "dec": "12",
        }
        normalized = value.replace("/", "-").replace(" ", "-")

        match = re.search(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", normalized)
        if match:
            year, month, day = match.groups()
            return datetime.strptime(
                f"{year}-{int(month):02d}-{int(day):02d}", "%Y-%m-%d"
            ).strftime("%Y-%m-%d")

        match = re.search(r"^(\d{1,2})-(\w{3,9})-(\d{4})$", normalized, re.IGNORECASE)
        if match:
            day, month_name, year = match.groups()
            month_key = month_name.lower()[:3]
            month = month_map.get(month_key)
            if month in ("", None):
                raise ValueError(f"Unsupported month name: {month_name}")
            return datetime.strptime(
                f"{year}-{month}-{int(day):02d}", "%Y-%m-%d"
            ).strftime("%Y-%m-%d")

        match = re.search(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", normalized)
        if match:
            day, month, year = match.groups()
            return datetime.strptime(
                f"{year}-{int(month):02d}-{int(day):02d}", "%Y-%m-%d"
            ).strftime("%Y-%m-%d")

        for fmt in ("%d %B %Y", "%d %b %Y", "%d-%B-%Y", "%d-%b-%Y"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

        raise ValueError(f"Unrecognized date format: {value!r}")

    def nilai_tanggal_berubah(self, old_value, new_value):
        if old_value in (None, "") and new_value in (None, ""):
            return False
        if old_value is None or new_value is None:
            return old_value != new_value
        try:
            old_norm = self.normalisasi_tanggal(old_value)
            new_norm = self.normalisasi_tanggal(new_value)
        except ValueError:
            return str(old_value).strip() != str(new_value).strip()
        return old_norm != new_norm

    def nilai_teks_berubah(self, old_value, new_value):
        if old_value is None and new_value is None:
            return False
        old_text = "" if old_value is None else str(old_value).strip()
        new_text = "" if new_value is None else str(new_value).strip()
        return old_text != new_text

    def ambil_nilai_cell(self, row, index):
        if not isinstance(row, (list, tuple)):
            return ""
        if 0 <= index < len(row):
            return row[index]
        return ""

    def cek_status_sertifikat(self, nik):
        url = f"{self.BASE_URL}/status/{nik}"
        response = self.requests.get(url, auth=(self.USERNAME, self.PASSWORD))
        payload = response.json() if hasattr(response, "json") else {}
        status_api = payload.get("status") if isinstance(payload, dict) else None

        if status_api == "NOT_REGISTERED":
            return {
                "update": False,
                "status_api": status_api,
                "status_pengguna": None,
                "status_sertifikat": None,
            }

        if status_api == "ISSUE":
            return {
                "update": True,
                "status_api": status_api,
                "status_pengguna": "Verified",
                "status_sertifikat": "Issued",
            }

        if status_api == "EXPIRED":
            return {
                "update": True,
                "status_api": status_api,
                "status_pengguna": "Verified",
                "status_sertifikat": "Expired",
            }

        return {
            "update": True,
            "status_api": status_api or "UNKNOWN",
            "status_pengguna": "Verified" if status_api else None,
            "status_sertifikat": "Unknown" if status_api else None,
        }

    def cek_profile_sertifikat(self, nik):
        url = f"{self.BASE_URL}/profile/{nik}"
        response = self.requests.get(url, auth=(self.USERNAME, self.PASSWORD))
        if getattr(response, "status_code", 200) != 200:
            return {"status": "NOT_FOUND"}

        payload = response.json() if hasattr(response, "json") else {}
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        sertifikat = data.get("sertifikat", []) if isinstance(data, dict) else []
        sertifikat = sertifikat or []
        valid_dates = []
        for item in sertifikat:
            if not isinstance(item, dict):
                continue
            raw_date = item.get("berlaku_sampai")
            if raw_date in (None, ""):
                continue
            try:
                valid_dates.append(self.normalisasi_tanggal(raw_date))
            except ValueError:
                continue

        if not valid_dates:
            return {"status": "NO_CERTIFICATE", "tanggal_terbit": "", "tanggal_berakhir": ""}

        return {
            "status": "SUCCESS",
            "tanggal_terbit": min(valid_dates),
            "tanggal_berakhir": max(valid_dates),
        }


class app(status_pengguna):
    """Concrete implementation of the shared BSrE operations.

    The production scripts expose these operations as module-level functions;
    this adapter keeps the same behaviour available through a concrete object
    so both modes can be exercised uniformly by the tests.
    """

    requests = requests

    @staticmethod
    def normalisasi_tanggal(value):
        return super(app, app).normalisasi_tanggal(value)

    def nilai_tanggal_berubah(self, old_value, new_value):
        return super().nilai_tanggal_berubah(old_value, new_value)

    def nilai_teks_berubah(self, old_value, new_value):
        return super().nilai_teks_berubah(old_value, new_value)

    def ambil_nilai_cell(self, row, index):
        return super().ambil_nilai_cell(row, index)

    def cek_status_sertifikat(self, nik):
        return super().cek_status_sertifikat(nik)

    def cek_profile_sertifikat(self, nik):
        return super().cek_profile_sertifikat(nik)


APPS = (
    ("FILTERED", filtered_app),
    ("ALL_ROWS", all_rows_app),
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeWorksheet:
    def __init__(self, data):
        self.title = "Data"
        self._data = data
        self.batch_updates = []
        self.formats = []

    def get_all_values(self):
        return self._data

    def batch_update(self, data, value_input_option=None):
        self.batch_updates.append({
            "data": data,
            "value_input_option": value_input_option,
        })
        return {}

    def format(self, range_name, format_data):
        self.formats.append({
            "range": range_name,
            "format": format_data,
        })
        return {}


class FakeExecute:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class FakeSpreadsheets:
    def __init__(self, payload):
        self.payload = payload

    def get(self, **kwargs):
        return FakeExecute(self.payload)


class FakeSheetsService:
    def __init__(self, payload):
        self.payload = payload

    def spreadsheets(self):
        return FakeSpreadsheets(self.payload)


def make_header():
    header = [""] * 18
    header[2] = "NIK"
    header[14] = "Status Pengguna"
    header[15] = "Status Sertifikat"
    header[16] = "Tanggal terbit"
    header[17] = "Tanggal berakhir"
    return header


def make_row(
    nik,
    status_pengguna="Verified",
    status_sertifikat="Issued",
    tanggal_terbit="2024-08-12",
    tanggal_berakhir="2026-08-12",
):
    row = [""] * 18
    row[2] = nik
    row[14] = status_pengguna
    row[15] = status_sertifikat
    row[16] = tanggal_terbit
    row[17] = tanggal_berakhir
    return row


class TestSharedHelpers(unittest.TestCase):
    def test_normalisasi_tanggal_pada_kedua_script(self):
        values = [
            "2026-08-12",
            "12-08-2026",
            "12/08/2026",
            "12-Agu-2026",
            "12-Aug-2026",
            "12 Agustus 2026",
            "12 August 2026",
        ]
        for app_name, app in APPS:
            for value in values:
                with self.subTest(app=app_name, value=value):
                    self.assertEqual(app.normalisasi_tanggal(value), "2026-08-12")

    def test_tanggal_format_berbeda_tidak_dianggap_berubah(self):
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertFalse(
                    app.nilai_tanggal_berubah("12-Agu-2026", "2026-08-12")
                )

    def test_tanggal_berbeda_dianggap_berubah(self):
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertTrue(
                    app.nilai_tanggal_berubah("12-Agu-2026", "2027-08-12")
                )

    def test_teks_dengan_spasi_sama_tidak_dianggap_berubah(self):
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertFalse(
                    app.nilai_teks_berubah(" Verified ", "Verified")
                )

    def test_status_sertifikat_berbeda_dianggap_berubah(self):
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertTrue(
                    app.nilai_teks_berubah("Issued", "Expired")
                )

    def test_ambil_nilai_cell(self):
        row = ["A", "B", "C"]
        for app_name, app in APPS:
            with self.subTest(app=app_name):
                self.assertEqual(app.ambil_nilai_cell(row, 1), "B")
                self.assertEqual(app.ambil_nilai_cell(row, 99), "")


class TestSharedBSrEStatusAPI(unittest.TestCase):
    def test_issue(self):
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "user"
            app.PASSWORD = "pass"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(200, {"status": "ISSUE"})
                    result = app.cek_status_sertifikat("1234567890123456")
                with self.subTest(app=app_name):
                    self.assertTrue(result["update"])
                    self.assertEqual(result["status_api"], "ISSUE")
                    self.assertEqual(result["status_pengguna"], "Verified")
                    self.assertEqual(result["status_sertifikat"], "Issued")
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old

    def test_not_registered_tidak_update(self):
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "user"
            app.PASSWORD = "pass"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(
                        200, {"status": "NOT_REGISTERED"}
                    )
                    result = app.cek_status_sertifikat("1234567890123456")
                with self.subTest(app=app_name):
                    self.assertFalse(result["update"])
                    self.assertEqual(result["status_api"], "NOT_REGISTERED")
                    self.assertIsNone(result["status_pengguna"])
                    self.assertIsNone(result["status_sertifikat"])
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old


class TestSharedBSrEProfileAPI(unittest.TestCase):
    def test_memilih_sertifikat_dengan_expired_terbaru(self):
        payload = {
            "success": True,
            "data": {
                "sertifikat": [
                    {"berlaku_sampai": "12-08-2026"},
                    {"berlaku_sampai": "12-08-2028"},
                    {"berlaku_sampai": "12-08-2027"},
                ]
            },
        }
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "user"
            app.PASSWORD = "pass"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(200, payload)
                    result = app.cek_profile_sertifikat("1234567890123456")
                with self.subTest(app=app_name):
                    self.assertEqual(result["status"], "SUCCESS")
                    self.assertEqual(result["tanggal_terbit"], "2026-08-12")
                    self.assertEqual(result["tanggal_berakhir"], "2028-08-12")
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old

    def test_profile_tanpa_sertifikat(self):
        payload = {"success": True, "data": {"sertifikat": []}}
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "user"
            app.PASSWORD = "pass"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(200, payload)
                    result = app.cek_profile_sertifikat("1234567890123456")
                with self.subTest(app=app_name):
                    self.assertEqual(result["status"], "NO_CERTIFICATE")
                    self.assertEqual(result["tanggal_terbit"], "")
                    self.assertEqual(result["tanggal_berakhir"], "")
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old

    def test_profile_404(self):
        for app_name, app in APPS:
            old = (app.BASE_URL, app.USERNAME, app.PASSWORD)
            app.BASE_URL = "https://example.test"
            app.USERNAME = "user"
            app.PASSWORD = "pass"
            try:
                with patch.object(app.requests, "get") as mock_get:
                    mock_get.return_value = FakeResponse(404, {})
                    result = app.cek_profile_sertifikat("1234567890123456")
                with self.subTest(app=app_name):
                    self.assertEqual(result["status"], "NOT_FOUND")
            finally:
                app.BASE_URL, app.USERNAME, app.PASSWORD = old


class TestFilteredMode(unittest.TestCase):
    def test_ambil_row_terlihat_melewati_hidden(self):
        payload = {
            "sheets": [{
                "data": [{
                    "startRow": 0,
                    "rowMetadata": [
                        {},
                        {},
                        {"hiddenByFilter": True},
                        {"hiddenByUser": True},
                        {},
                    ],
                }]
            }]
        }
        service = FakeSheetsService(payload)
        worksheet = FakeWorksheet([])
        old_id = filtered_app.SPREADSHEET_ID
        filtered_app.SPREADSHEET_ID = "test-spreadsheet"
        try:
            result = filtered_app.ambil_row_terlihat(service, worksheet)
        finally:
            filtered_app.SPREADSHEET_ID = old_id
        self.assertEqual(result, [1, 2, 5])

    def test_proses_filtered_hanya_memanggil_api_untuk_row_visible(self):
        data = [
            make_header(),
            make_row("1111111111111111"),
            make_row("2222222222222222"),
        ]
        worksheet = FakeWorksheet(data)
        metadata = {
            "sheets": [{
                "data": [{
                    "startRow": 0,
                    "rowMetadata": [
                        {},
                        {},
                        {"hiddenByFilter": True},
                    ],
                }]
            }]
        }
        sheets_service = FakeSheetsService(metadata)

        status_calls = []
        profile_calls = []

        def fake_status(nik):
            status_calls.append(nik)
            return {
                "update": True,
                "status_api": "ISSUE",
                "status_pengguna": "Verified",
                "status_sertifikat": "Issued",
            }

        def fake_profile(nik):
            profile_calls.append(nik)
            return {
                "status": "SUCCESS",
                "tanggal_terbit": "2024-08-12",
                "tanggal_berakhir": "2026-08-12",
            }

        old = (filtered_app.SPREADSHEET_ID, filtered_app.WORKSHEET_NAME)
        filtered_app.SPREADSHEET_ID = "test-spreadsheet"
        filtered_app.WORKSHEET_NAME = "Data"

        try:
            with (
                patch.object(
                    filtered_app,
                    "koneksi_google",
                    return_value=(None, None, worksheet, sheets_service),
                ),
                patch.object(
                    filtered_app,
                    "cek_status_sertifikat",
                    side_effect=fake_status,
                ),
                patch.object(
                    filtered_app,
                    "cek_profile_sertifikat",
                    side_effect=fake_profile,
                ),
                patch.object(filtered_app.time, "sleep", return_value=None),
                patch.object(
                    filtered_app,
                    "tqdm",
                    side_effect=lambda iterable, **kwargs: iterable,
                ),
            ):
                filtered_app.proses_google_sheet()
        finally:
            filtered_app.SPREADSHEET_ID, filtered_app.WORKSHEET_NAME = old

        self.assertEqual(status_calls, ["1111111111111111"])
        self.assertEqual(profile_calls, ["1111111111111111"])
        self.assertEqual(worksheet.batch_updates, [])


class TestAllRowsMode(unittest.TestCase):
    def test_proses_all_rows_memanggil_api_untuk_semua_row(self):
        data = [
            make_header(),
            make_row("1111111111111111"),
            make_row("2222222222222222"),
        ]
        worksheet = FakeWorksheet(data)

        status_calls = []
        profile_calls = []

        def fake_status(nik):
            status_calls.append(nik)
            return {
                "update": True,
                "status_api": "ISSUE",
                "status_pengguna": "Verified",
                "status_sertifikat": "Issued",
            }

        def fake_profile(nik):
            profile_calls.append(nik)
            return {
                "status": "SUCCESS",
                "tanggal_terbit": "2024-08-12",
                "tanggal_berakhir": "2026-08-12",
            }

        old = (all_rows_app.SPREADSHEET_ID, all_rows_app.WORKSHEET_NAME)
        all_rows_app.SPREADSHEET_ID = "test-spreadsheet"
        all_rows_app.WORKSHEET_NAME = "Data"

        try:
            with (
                patch.object(
                    all_rows_app,
                    "koneksi_google",
                    return_value=(None, None, worksheet),
                ),
                patch.object(
                    all_rows_app,
                    "cek_status_sertifikat",
                    side_effect=fake_status,
                ),
                patch.object(
                    all_rows_app,
                    "cek_profile_sertifikat",
                    side_effect=fake_profile,
                ),
                patch.object(all_rows_app.time, "sleep", return_value=None),
                patch.object(
                    all_rows_app,
                    "tqdm",
                    side_effect=lambda iterable, **kwargs: iterable,
                ),
            ):
                all_rows_app.proses_google_sheet()
        finally:
            all_rows_app.SPREADSHEET_ID, all_rows_app.WORKSHEET_NAME = old

        self.assertEqual(
            status_calls,
            ["1111111111111111", "2222222222222222"],
        )
        self.assertEqual(
            profile_calls,
            ["1111111111111111", "2222222222222222"],
        )
        self.assertEqual(worksheet.batch_updates, [])

    def test_all_rows_hanya_update_cell_yang_berubah(self):
        data = [
            make_header(),
            make_row("1111111111111111", status_sertifikat="Issued"),
            make_row("2222222222222222", status_sertifikat="Issued"),
        ]
        worksheet = FakeWorksheet(data)

        def fake_status(nik):
            if nik == "2222222222222222":
                return {
                    "update": True,
                    "status_api": "EXPIRED",
                    "status_pengguna": "Verified",
                    "status_sertifikat": "Expired",
                }
            return {
                "update": True,
                "status_api": "ISSUE",
                "status_pengguna": "Verified",
                "status_sertifikat": "Issued",
            }

        def fake_profile(nik):
            return {
                "status": "SUCCESS",
                "tanggal_terbit": "2024-08-12",
                "tanggal_berakhir": "2026-08-12",
            }

        old = (all_rows_app.SPREADSHEET_ID, all_rows_app.WORKSHEET_NAME)
        all_rows_app.SPREADSHEET_ID = "test-spreadsheet"
        all_rows_app.WORKSHEET_NAME = "Data"

        try:
            with (
                patch.object(
                    all_rows_app,
                    "koneksi_google",
                    return_value=(None, None, worksheet),
                ),
                patch.object(
                    all_rows_app,
                    "cek_status_sertifikat",
                    side_effect=fake_status,
                ),
                patch.object(
                    all_rows_app,
                    "cek_profile_sertifikat",
                    side_effect=fake_profile,
                ),
                patch.object(all_rows_app.time, "sleep", return_value=None),
                patch.object(
                    all_rows_app,
                    "tqdm",
                    side_effect=lambda iterable, **kwargs: iterable,
                ),
            ):
                all_rows_app.proses_google_sheet()
        finally:
            all_rows_app.SPREADSHEET_ID, all_rows_app.WORKSHEET_NAME = old

        self.assertEqual(len(worksheet.batch_updates), 1)
        update_data = worksheet.batch_updates[0]["data"]
        self.assertEqual(
            update_data,
            [{"range": "P3", "values": [["Expired"]]}],
        )
        self.assertEqual(worksheet.formats, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
