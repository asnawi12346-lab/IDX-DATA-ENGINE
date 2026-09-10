from curl_cffi import requests
import time


BASE = "https://www.idx.co.id"
URL = f"{BASE}/primary/TradingSummary/GetStockSummary"

HEADERS = {
    "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham/",
    "Origin": "https://www.idx.co.id",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
}


DATES = [
    "20260909",
    "20260908",
    "20260907",
    "20260904",
    "20260903",
]


def request_summary(date, retries=3):
    last_error = None

    for attempt in range(1, retries + 1):

        try:
            print(
                f"Request date={date}, "
                f"attempt={attempt}/{retries}"
            )

            response = requests.get(
                URL,
                params={
                    "date": date,
                    "start": 0,
                    "length": 9999,
                },
                impersonate="chrome",
                headers=HEADERS,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise ValueError(
                    "Response JSON bukan object"
                )

            if "data" not in data:
                raise ValueError(
                    "Response tidak memiliki field data"
                )

            if not isinstance(data["data"], list):
                raise ValueError(
                    "Field data bukan list"
                )

            return data

        except Exception as exc:

            last_error = exc

            print(
                f"Gagal: {type(exc).__name__}: {exc}"
            )

            if attempt < retries:

                wait = 3 * attempt

                print(
                    f"Retry dalam {wait} detik..."
                )

                time.sleep(wait)

    raise RuntimeError(
        f"Gagal setelah {retries} percobaan"
    ) from last_error


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def validate_date(date, rows, records_total):

    errors = []
    warnings = []

    # ==================================================
    # EXPECTED DATE
    # ==================================================

    # Request menggunakan format:
    # 20260909
    #
    # IDX mengembalikan:
    # 2026-09-09T00:00:00
    #
    # Jadi validator menormalisasi tanggal
    # request menjadi:
    # 2026-09-09

    expected_date = (
        f"{date[0:4]}-"
        f"{date[4:6]}-"
        f"{date[6:8]}"
    )

    # ==================================================
    # COMPLETENESS
    # ==================================================

    if records_total != len(rows):

        errors.append(
            f"recordsTotal={records_total}, "
            f"rows={len(rows)}"
        )

    # ==================================================
    # STOCK CODE
    # ==================================================

    missing_code = 0

    codes = []

    for row in rows:

        code = row.get("StockCode")

        if not code:

            missing_code += 1

        else:

            codes.append(code)

    duplicate_codes = (
        len(codes) - len(set(codes))
    )

    if missing_code > 0:

        errors.append(
            f"Missing StockCode={missing_code}"
        )

    if duplicate_codes > 0:

        errors.append(
            f"Duplicate StockCode={duplicate_codes}"
        )

    # ==================================================
    # DATE CONSISTENCY
    # ==================================================

    wrong_date = 0

    for row in rows:

        row_date = str(
            row.get("Date", "")
        )

        # IDX:
        # 2026-09-09T00:00:00
        #
        # Ambil 10 karakter pertama:
        # 2026-09-09

        actual_date = row_date[:10]

        if actual_date != expected_date:

            wrong_date += 1

    if wrong_date > 0:

        errors.append(
            f"Wrong Date={wrong_date}"
        )

    # ==================================================
    # MARKET STATUS
    # ==================================================

    active_volume = 0
    no_trade = 0
    active_open_zero = 0

    # ==================================================
    # NUMERIC VALIDATION COUNTERS
    # ==================================================

    invalid_ohlc = 0
    invalid_volume = 0
    invalid_value = 0
    invalid_frequency = 0
    invalid_foreign = 0

    # ==================================================
    # VALIDATE EACH ROW
    # ==================================================

    for row in rows:

        volume = row.get("Volume", 0)
        value = row.get("Value", 0)
        frequency = row.get("Frequency", 0)

        foreign_buy = row.get(
            "ForeignBuy",
            0
        )

        foreign_sell = row.get(
            "ForeignSell",
            0
        )

        # ------------------------------------------------
        # VOLUME
        # ------------------------------------------------

        if (
            not is_number(volume)
            or volume < 0
        ):

            invalid_volume += 1

        # ------------------------------------------------
        # VALUE
        # ------------------------------------------------

        if (
            not is_number(value)
            or value < 0
        ):

            invalid_value += 1

        # ------------------------------------------------
        # FREQUENCY
        # ------------------------------------------------

        if (
            not is_number(frequency)
            or frequency < 0
        ):

            invalid_frequency += 1

        # ------------------------------------------------
        # FOREIGN FLOW
        # ------------------------------------------------

        if (
            not is_number(foreign_buy)
            or foreign_buy < 0
            or not is_number(foreign_sell)
            or foreign_sell < 0
        ):

            invalid_foreign += 1

        # =================================================
        # ACTIVE / NO TRADE
        # =================================================

        if (
            is_number(volume)
            and volume > 0
        ):

            active_volume += 1

            previous = row.get(
                "Previous"
            )

            open_price = row.get(
                "OpenPrice"
            )

            high = row.get(
                "High"
            )

            low = row.get(
                "Low"
            )

            close = row.get(
                "Close"
            )

            # ------------------------------------------------
            # BASIC OHLC NUMERIC CHECK
            # ------------------------------------------------

            if (
                not is_number(previous)
                or previous < 0
                or not is_number(open_price)
                or open_price < 0
                or not is_number(high)
                or high < 0
                or not is_number(low)
                or low < 0
                or not is_number(close)
                or close < 0
            ):

                invalid_ohlc += 1

                continue

            # ------------------------------------------------
            # HIGH >= LOW
            # ------------------------------------------------

            if high < low:

                invalid_ohlc += 1

                continue

            # ------------------------------------------------
            # HIGH >= CLOSE
            # ------------------------------------------------

            if high < close:

                invalid_ohlc += 1

                continue

            # ------------------------------------------------
            # LOW <= CLOSE
            # ------------------------------------------------

            if low > close:

                invalid_ohlc += 1

                continue

            # ------------------------------------------------
            # OPEN VALIDATION
            #
            # OpenPrice = 0 is allowed by IDX data.
            # Therefore only validate relationship
            # when OpenPrice > 0.
            # ------------------------------------------------

            if open_price > 0:

                if high < open_price:

                    invalid_ohlc += 1

                    continue

                if low > open_price:

                    invalid_ohlc += 1

                    continue

            # ------------------------------------------------
            # ACTIVE OPEN ZERO
            # ------------------------------------------------

            if open_price == 0:

                active_open_zero += 1

        else:

            no_trade += 1

    # ==================================================
    # VALIDATION ERRORS
    # ==================================================

    if invalid_ohlc > 0:

        errors.append(
            f"Invalid Active OHLC={invalid_ohlc}"
        )

    if invalid_volume > 0:

        errors.append(
            f"Invalid Volume={invalid_volume}"
        )

    if invalid_value > 0:

        errors.append(
            f"Invalid Value={invalid_value}"
        )

    if invalid_frequency > 0:

        errors.append(
            f"Invalid Frequency={invalid_frequency}"
        )

    if invalid_foreign > 0:

        errors.append(
            f"Invalid Foreign Flow={invalid_foreign}"
        )

    # ==================================================
    # WARNINGS
    # ==================================================

    if no_trade > 0:

        warnings.append(
            f"{no_trade} NO_TRADE rows"
        )

    if active_open_zero > 0:

        warnings.append(
            f"{active_open_zero} active rows "
            f"with OpenPrice=0"
        )

    # ==================================================
    # STATUS
    # ==================================================

    if errors:

        status = "FAILED"

    elif warnings:

        status = "PASS_WITH_WARNING"

    else:

        status = "VERIFIED"

    return {
        "date": date,
        "records_total": records_total,
        "rows": len(rows),
        "active": active_volume,
        "no_trade": no_trade,
        "open_zero": active_open_zero,
        "missing_code": missing_code,
        "duplicate": duplicate_codes,
        "wrong_date": wrong_date,
        "invalid_ohlc": invalid_ohlc,
        "invalid_volume": invalid_volume,
        "invalid_value": invalid_value,
        "invalid_frequency": invalid_frequency,
        "invalid_foreign": invalid_foreign,
        "errors": errors,
        "warnings": warnings,
        "status": status,
        "codes": set(codes),
    }


def main():

    print("=" * 78)
    print(
        "IDX DATA ENGINE - "
        "MULTI DATE / FULL IDX TEST"
    )
    print("=" * 78)

    print("\nTanggal yang diuji:")

    for date in DATES:

        print(f"  - {date}")

    print("\nParameter:")

    print("  start    = 0")
    print("  length   = 9999")
    print("  universe = seluruh IDX")

    results = []

    # ==================================================
    # TEST EACH DATE
    # ==================================================

    for index, date in enumerate(DATES):

        if index > 0:

            time.sleep(3)

        print("\n" + "-" * 78)

        print(
            f"VALIDATING DATE : {date}"
        )

        print("-" * 78)

        try:

            data = request_summary(date)

            rows = data.get(
                "data",
                []
            )

            records_total = data.get(
                "recordsTotal"
            )

            result = validate_date(
                date=date,
                rows=rows,
                records_total=records_total,
            )

            results.append(result)

            # ----------------------------------------------
            # RESULT
            # ----------------------------------------------

            print(
                f"recordsTotal      : "
                f"{result['records_total']}"
            )

            print(
                f"Rows diterima     : "
                f"{result['rows']}"
            )

            print(
                f"Active            : "
                f"{result['active']}"
            )

            print(
                f"NO_TRADE          : "
                f"{result['no_trade']}"
            )

            print(
                f"Active Open=0     : "
                f"{result['open_zero']}"
            )

            print(
                f"Missing StockCode : "
                f"{result['missing_code']}"
            )

            print(
                f"Duplicate Code    : "
                f"{result['duplicate']}"
            )

            print(
                f"Wrong Date        : "
                f"{result['wrong_date']}"
            )

            print(
                f"Invalid OHLC      : "
                f"{result['invalid_ohlc']}"
            )

            print(
                f"Invalid Volume    : "
                f"{result['invalid_volume']}"
            )

            print(
                f"Invalid Value     : "
                f"{result['invalid_value']}"
            )

            print(
                f"Invalid Frequency : "
                f"{result['invalid_frequency']}"
            )

            print(
                f"Invalid Foreign   : "
                f"{result['invalid_foreign']}"
            )

            # ----------------------------------------------
            # WARNINGS
            # ----------------------------------------------

            if result["warnings"]:

                print("\nWarnings:")

                for warning in result["warnings"]:

                    print(
                        f"  - {warning}"
                    )

            # ----------------------------------------------
            # ERRORS
            # ----------------------------------------------

            if result["errors"]:

                print("\nErrors:")

                for error in result["errors"]:

                    print(
                        f"  - {error}"
                    )

            print(
                f"\nSTATUS            : "
                f"{result['status']}"
            )

        except Exception as exc:

            print(
                f"\nFATAL ERROR pada {date}: "
                f"{type(exc).__name__}: {exc}"
            )

            results.append(
                {
                    "date": date,
                    "records_total": 0,
                    "rows": 0,
                    "active": 0,
                    "no_trade": 0,
                    "open_zero": 0,
                    "missing_code": 0,
                    "duplicate": 0,
                    "wrong_date": 0,
                    "invalid_ohlc": 0,
                    "invalid_volume": 0,
                    "invalid_value": 0,
                    "invalid_frequency": 0,
                    "invalid_foreign": 0,
                    "errors": [str(exc)],
                    "warnings": [],
                    "status": "FAILED",
                    "codes": set(),
                }
            )

    # ==================================================
    # MULTI-DATE SUMMARY
    # ==================================================

    print("\n")

    print("=" * 78)
    print("MULTI-DATE SUMMARY")
    print("=" * 78)

    for result in results:

        print(
            f"{result['date']} | "
            f"rows={result['rows']:<4} | "
            f"active={result['active']:<4} | "
            f"no_trade={result['no_trade']:<4} | "
            f"status={result['status']}"
        )

    # ==================================================
    # SUCCESSFUL RESULTS
    # ==================================================

    successful = [
        result
        for result in results
        if result["status"] != "FAILED"
    ]

    # ==================================================
    # CHECK 1
    # COMPLETENESS
    # ==================================================

    completeness_pass = (
        len(successful) == len(results)
        and all(
            result["records_total"]
            == result["rows"]
            for result in successful
        )
    )

    # ==================================================
    # CHECK 2
    # DUPLICATES
    # ==================================================

    duplicate_pass = all(
        result["duplicate"] == 0
        for result in results
    )

    # ==================================================
    # CHECK 3
    # DATE CONSISTENCY
    # ==================================================

    date_pass = all(
        result["wrong_date"] == 0
        for result in results
    )

    # ==================================================
    # CHECK 4
    # VALIDATOR
    # ==================================================

    validation_pass = all(
        len(result["errors"]) == 0
        for result in results
    )

    # ==================================================
    # CHECK 5
    # UNIVERSE DIFFERENCE
    #
    # Universe tidak harus identik antar tanggal.
    # Kita hanya melaporkan perbedaan.
    # ==================================================

    universe_sets = [
        result["codes"]
        for result in successful
    ]

    universe_difference = False

    if universe_sets:

        base = universe_sets[0]

        for current in universe_sets[1:]:

            if current != base:

                universe_difference = True

                break

    # ==================================================
    # CROSS-DATE CHECKS
    # ==================================================

    print("\n--- CROSS-DATE CHECKS ---")

    print(
        f"Completeness semua tanggal : "
        f"{'PASS' if completeness_pass else 'FAIL'}"
    )

    print(
        f"Duplicate semua tanggal    : "
        f"{'PASS' if duplicate_pass else 'FAIL'}"
    )

    print(
        f"Date consistency            : "
        f"{'PASS' if date_pass else 'FAIL'}"
    )

    print(
        f"Validator V2                : "
        f"{'PASS' if validation_pass else 'FAIL'}"
    )

    if universe_difference:

        print(
            "Universe antar tanggal     : "
            "BERBEDA / REVIEW"
        )

        print(
            "Catatan: perbedaan universe "
            "tidak otomatis error."
        )

    else:

        print(
            "Universe antar tanggal     : "
            "IDENTIK"
        )

    # ==================================================
    # FINAL STATUS
    # ==================================================

    print("\n" + "=" * 78)

    if (
        completeness_pass
        and duplicate_pass
        and date_pass
        and validation_pass
    ):

        print("STATUS : VERIFIED")

        print("\nKESIMPULAN:")

        print(
            "Multi-date Stock Summary berhasil "
            "melewati validator V2."
        )

        print(
            "Seluruh tanggal yang diuji "
            "menghasilkan response lengkap."
        )

        print(
            "Universe IDX dapat diambil "
            "per tanggal menggunakan endpoint "
            "GetStockSummary."
        )

        print(
            "Tidak ditemukan error data "
            "pada validasi dasar."
        )

    else:

        print("STATUS : REVIEW")

        print("\nKESIMPULAN:")

        print(
            "Masih terdapat tanggal atau "
            "validasi yang perlu diperiksa."
        )

    print("=" * 78)


if __name__ == "__main__":
    main()