from curl_cffi import requests
from datetime import datetime

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

def get_stock_summary(date, retries=3):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            print(f"Request attempt {attempt}/{retries}...")

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
                raise ValueError("Response JSON bukan object")

            if "data" not in data:
                raise ValueError("Response tidak memiliki field 'data'")

            return data

        except Exception as exc:
            last_error = exc
            print(f"Request gagal: {type(exc).__name__}: {exc}")

            if attempt < retries:
                print("Menunggu 3 detik sebelum retry...")
                import time
                time.sleep(3)

    raise RuntimeError(
        f"Gagal mengambil Stock Summary setelah {retries} percobaan"
    ) from last_error

def is_number(value):
    return isinstance(value, (int, float)) and value is not None


def main():
    date = "20260909"

    print("=" * 70)
    print("IDX DATA ENGINE - STOCK SUMMARY VALIDATION")
    print("=" * 70)

    print(f"\nTanggal           : {date}")
    print("Mengambil data...")

    data = get_stock_summary(date)

    rows = data.get("data", [])

    print(f"HTTP              : 200")
    print(f"recordsTotal      : {data.get('recordsTotal')}")
    print(f"Rows diterima     : {len(rows)}")

    # ------------------------------------------------------------
    # BASIC FIELD VALIDATION
    # ------------------------------------------------------------

    missing_code = []
    missing_date = []

    duplicate_codes = []

    codes = []

    for row in rows:
        code = row.get("StockCode")

        if not code:
            missing_code.append(row)

        else:
            codes.append(code)

        if not row.get("Date"):
            missing_date.append(code)

    seen = set()

    for code in codes:
        if code in seen:
            duplicate_codes.append(code)
        seen.add(code)

    # ------------------------------------------------------------
    # DATE VALIDATION
    # ------------------------------------------------------------

    wrong_dates = []

    for row in rows:
        value = row.get("Date")

        if not value:
            continue

        if not value.startswith(
            f"{date[:4]}-{date[4:6]}-{date[6:]}"
        ):
            wrong_dates.append(
                (row.get("StockCode"), value)
            )

    # ------------------------------------------------------------
    # OHLC VALIDATION
    # ------------------------------------------------------------

    invalid_ohlc = []

    for row in rows:
        code = row.get("StockCode")

        previous = row.get("Previous")
        open_price = row.get("OpenPrice")
        high = row.get("High")
        low = row.get("Low")
        close = row.get("Close")

        values = [
            previous,
            open_price,
            high,
            low,
            close,
        ]

        # Semua harus numerik
        if not all(is_number(x) for x in values):
            invalid_ohlc.append(
                (code, "non-numeric", values)
            )
            continue

        # Harga tidak boleh negatif
        if any(x < 0 for x in values):
            invalid_ohlc.append(
                (code, "negative-price", values)
            )
            continue

        # High harus >= Low
        if high < low:
            invalid_ohlc.append(
                (code, "High < Low", values)
            )
            continue

        # High harus >= Open
        if high < open_price:
            invalid_ohlc.append(
                (code, "High < Open", values)
            )
            continue

        # High harus >= Close
        if high < close:
            invalid_ohlc.append(
                (code, "High < Close", values)
            )
            continue

        # Low harus <= Open
        if low > open_price:
            invalid_ohlc.append(
                (code, "Low > Open", values)
            )
            continue

        # Low harus <= Close
        if low > close:
            invalid_ohlc.append(
                (code, "Low > Close", values)
            )

    # ------------------------------------------------------------
    # VOLUME / VALUE / FREQUENCY
    # ------------------------------------------------------------

    invalid_volume = []
    invalid_value = []
    invalid_frequency = []

    for row in rows:
        code = row.get("StockCode")

        volume = row.get("Volume")
        value = row.get("Value")
        frequency = row.get("Frequency")

        if not is_number(volume) or volume < 0:
            invalid_volume.append(
                (code, volume)
            )

        if not is_number(value) or value < 0:
            invalid_value.append(
                (code, value)
            )

        if not is_number(frequency) or frequency < 0:
            invalid_frequency.append(
                (code, frequency)
            )

    # ------------------------------------------------------------
    # FOREIGN FLOW
    # ------------------------------------------------------------

    invalid_foreign = []

    for row in rows:
        code = row.get("StockCode")

        foreign_buy = row.get("ForeignBuy")
        foreign_sell = row.get("ForeignSell")

        if (
            not is_number(foreign_buy)
            or not is_number(foreign_sell)
            or foreign_buy < 0
            or foreign_sell < 0
        ):
            invalid_foreign.append(
                (code, foreign_buy, foreign_sell)
            )

    # ------------------------------------------------------------
    # ZERO ACTIVITY
    # ------------------------------------------------------------

    zero_volume = []
    zero_frequency = []

    for row in rows:
        code = row.get("StockCode")

        if row.get("Volume") == 0:
            zero_volume.append(code)

        if row.get("Frequency") == 0:
            zero_frequency.append(code)

    # ------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION RESULT")
    print("=" * 70)

    print(f"\nMissing StockCode      : {len(missing_code)}")
    print(f"Missing Date           : {len(missing_date)}")
    print(f"Duplicate StockCode    : {len(duplicate_codes)}")
    print(f"Wrong Date             : {len(wrong_dates)}")

    print(f"\nInvalid OHLC           : {len(invalid_ohlc)}")
    print(f"Invalid Volume         : {len(invalid_volume)}")
    print(f"Invalid Value          : {len(invalid_value)}")
    print(f"Invalid Frequency      : {len(invalid_frequency)}")
    print(f"Invalid Foreign Flow   : {len(invalid_foreign)}")

    print(f"\nZero Volume             : {len(zero_volume)}")
    print(f"Zero Frequency         : {len(zero_frequency)}")

    # ------------------------------------------------------------
    # DETAILS
    # ------------------------------------------------------------

    if duplicate_codes:
        print("\nDuplicate codes:")
        for code in duplicate_codes[:20]:
            print(f"  - {code}")

    if wrong_dates:
        print("\nWrong dates:")
        for item in wrong_dates[:20]:
            print(f"  - {item}")

    if invalid_ohlc:
        print("\nInvalid OHLC:")
        for item in invalid_ohlc[:20]:
            print(f"  - {item}")

    if invalid_volume:
        print("\nInvalid Volume:")
        for item in invalid_volume[:20]:
            print(f"  - {item}")

    if invalid_value:
        print("\nInvalid Value:")
        for item in invalid_value[:20]:
            print(f"  - {item}")

    if invalid_frequency:
        print("\nInvalid Frequency:")
        for item in invalid_frequency[:20]:
            print(f"  - {item}")

    if invalid_foreign:
        print("\nInvalid Foreign Flow:")
        for item in invalid_foreign[:20]:
            print(f"  - {item}")

    # ------------------------------------------------------------
    # QUALITY SCORE
    # ------------------------------------------------------------

    checks = [
        len(missing_code) == 0,
        len(missing_date) == 0,
        len(duplicate_codes) == 0,
        len(wrong_dates) == 0,
        len(invalid_ohlc) == 0,
        len(invalid_volume) == 0,
        len(invalid_value) == 0,
        len(invalid_frequency) == 0,
        len(invalid_foreign) == 0,
    ]

    passed = sum(checks)
    total = len(checks)

    score = (passed / total) * 100

    print("\n" + "=" * 70)
    print("QUALITY")
    print("=" * 70)

    print(f"Checks Passed        : {passed}/{total}")
    print(f"QUALITY SCORE        : {score:.2f}%")

    if score == 100:
        print("STATUS               : VERIFIED")
    elif score >= 80:
        print("STATUS               : REVIEW")
    else:
        print("STATUS               : FAILED")

    print("=" * 70)


if __name__ == "__main__":
    main()