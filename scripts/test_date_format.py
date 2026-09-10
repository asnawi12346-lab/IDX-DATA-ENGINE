from curl_cffi import requests


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


def main():
    date = "20260909"

    print("=" * 70)
    print("IDX DATA ENGINE - DATE FORMAT TEST")
    print("=" * 70)

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
    rows = data.get("data", [])

    print(f"\nRequest date : {date}")
    print(f"HTTP         : {response.status_code}")
    print(f"recordsTotal : {data.get('recordsTotal')}")
    print(f"Rows         : {len(rows)}")

    print("\n--- SAMPLE DATE VALUES ---")

    for index, row in enumerate(rows[:10], start=1):
        print(
            f"{index:02d}. "
            f"StockCode={row.get('StockCode')} | "
            f"Date={repr(row.get('Date'))} | "
            f"Type={type(row.get('Date')).__name__}"
        )

    print("\n--- FIRST ROW KEYS ---")

    if rows:
        print(list(rows[0].keys()))

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()