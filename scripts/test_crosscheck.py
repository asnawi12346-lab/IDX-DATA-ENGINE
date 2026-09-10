from curl_cffi import requests
import time

BASE = "https://www.idx.co.id"

HEADERS_COMPANY = {
    "Referer": "https://www.idx.co.id/",
    "Accept": "application/json, text/plain, */*",
}

HEADERS_STOCK = {
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


def get_company_profiles():
    url = f"{BASE}/primary/ListedCompany/GetCompanyProfiles"

    response = requests.get(
        url,
        params={"start": 0, "length": 9999},
        impersonate="chrome",
        headers=HEADERS_COMPANY,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_stock_summary(date):
    url = f"{BASE}/primary/TradingSummary/GetStockSummary"

    response = requests.get(
        url,
        params={
            "date": date,
            "start": 0,
            "length": 9999,
        },
        impersonate="chrome",
        headers=HEADERS_STOCK,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def main():
    date = "20260909"

    print("=" * 60)
    print("IDX DATA ENGINE - COMPANY / STOCK CROSS CHECK")
    print("=" * 60)

    print("\n[1/2] Mengambil Company Profiles...")

    company_json = get_company_profiles()

    companies = {
        row.get("KodeEmiten")
        for row in company_json.get("data", [])
        if row.get("KodeEmiten")
    }

    print(f"HTTP             : 200")
    print(f"recordsTotal     : {company_json.get('recordsTotal')}")
    print(f"Company rows     : {len(companies)}")

    print("\nMenunggu 2 detik...")
    time.sleep(2)

    print("\n[2/2] Mengambil Stock Summary...")
    
    stock_json = get_stock_summary(date)

    stock_rows = stock_json.get("data", [])

    stocks = {
        row.get("StockCode")
        for row in stock_rows
        if row.get("StockCode")
    }

    print(f"HTTP             : 200")
    print(f"recordsTotal     : {stock_json.get('recordsTotal')}")
    print(f"Stock rows       : {len(stock_rows)}")
    print(f"Unique StockCode : {len(stocks)}")

    duplicates = len(stock_rows) - len(stocks)

    stock_not_master = sorted(stocks - companies)
    master_not_stock = sorted(companies - stocks)

    print("\n" + "=" * 60)
    print("CROSS CHECK RESULT")
    print("=" * 60)

    print(f"Company Profiles : {len(companies)}")
    print(f"Stock Summary    : {len(stocks)}")
    print(f"Duplicate Stock  : {duplicates}")

    print("\nStock Summary tetapi TIDAK ada di Company Profiles:")
    if stock_not_master:
        for code in stock_not_master:
            print(f"  - {code}")
    else:
        print("  NONE")

    print("\nCompany Profiles tetapi TIDAK ada di Stock Summary:")
    if master_not_stock:
        for code in master_not_stock:
            print(f"  - {code}")
    else:
        print("  NONE")

    print("\n" + "=" * 60)
    print("STATUS")
    print("=" * 60)

    if duplicates == 0:
        print("Duplicate         : PASS")
    else:
        print("Duplicate         : CHECK")

    if len(stock_not_master) <= 5:
        print("Universe mismatch : PASS / REVIEW")
    else:
        print("Universe mismatch : CHECK")

    print("=" * 60)


if __name__ == "__main__":
    main()