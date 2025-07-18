import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient

# Koneksi ke MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["palugada"]
collection = db["bbm"]

# Fungsi untuk mendapatkan harga dari halaman web
def get_price(url, target_data_test):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    price_tag = soup.find('div', {'data-test': target_data_test}) or soup.find('p', {'data-test-id': target_data_test})

    if price_tag:
        price_text = price_tag.text
        price = ''.join(c for c in price_text if c.isdigit() or c == '.' or c == ',')
        price = price.replace(",", "")
        return float(price)
    else:
        return None

# Fungsi untuk mengambil data harga saham BP
def get_bp_share_prices():
    url = "https://apps.bp.com/SharePriceFeed"
    headers = {
        "x-api-key": "8tmAkp0htLAW4cq1zSPk8YGgKpG4dU62gl80C6Cj"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return {
            "ldn_current_price": data.get('ldn-currentPrice'),
            "ldn_current_trend": data.get('ldn-currentTrend'),
            "bre_current_price": data.get('bre-currentPrice'),
            "bre_current_trend": data.get('bre-currentTrend'),
            "nyc_current_price": data.get('nyc-currentPrice'),
            "nyc_current_trend": data.get('nyc-currentTrend'),
            "fra_current_price": data.get('fra-currentPrice'),
            "fra_current_trend": data.get('fra-currentTrend'),
        }
    else:
        print(f"Gagal ambil data BP API: {response.status_code}")
        return None

# Fungsi menyimpan data ke MongoDB
def save_to_db(brent_price, usd_idr, harga_bbm_dasar, bp_data, kesimpulan):
    rectimestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rectimestamp_epoch = int(datetime.now().timestamp())

    document = {
        "brent_price": brent_price,
        "usd_idr": usd_idr,
        "harga_bbm_dasar": harga_bbm_dasar,
        "bp_ldn_price": bp_data['ldn_current_price'],
        "bp_ldn_trend": bp_data['ldn_current_trend'],
        "bp_bre_price": bp_data['bre_current_price'],
        "bp_bre_trend": bp_data['bre_current_trend'],
        "bp_nyc_price": bp_data['nyc_current_price'],
        "bp_nyc_trend": bp_data['nyc_current_trend'],
        "bp_fra_price": bp_data['fra_current_price'],
        "bp_fra_trend": bp_data['fra_current_trend'],
        "kesimpulan": kesimpulan,
        "rectimestamp": rectimestamp,
        "rectimestamp_epoch": rectimestamp_epoch
    }

    collection.insert_one(document)

# Fungsi untuk menganalisis kesimpulan
def analyze_trend(bp_data):
    up = 0
    down = 0
    stable = 0

    for market in ['ldn', 'bre', 'nyc', 'fra']:
        trend = bp_data.get(f"{market}_current_trend", "").upper()
        if trend == "UP":
            up += 1
        elif trend == "DOWN":
            down += 1
        else:
            stable += 1

    if up > down:
        return f"Harga BBM kemungkinan NAIK karena {up} pasar menunjukkan kenaikan harga."
    elif down > up:
        return f"Harga BBM kemungkinan TURUN karena {down} pasar menunjukkan penurunan harga."
    else:
        return "Harga BBM kemungkinan STABIL karena jumlah pasar yang naik dan turun seimbang."

# Main function
def main_bbm():
    brent_url = "https://www.investing.com/commodities/brent-oil"
    usd_idr_url = "https://www.investing.com/currencies/usd-idr"

    brent_price = get_price(brent_url, "instrument-price-last")
    usd_idr = get_price(usd_idr_url, "instrument-price-last")
    bp_data = get_bp_share_prices()

    print("=== DASHBOARD BBM & BP MONITORING ===")

    if brent_price is not None:
        print(f"Harga Brent Oil        : {brent_price} USD/barel")
    else:
        print("Gagal mengambil harga minyak Brent.")

    if usd_idr is not None:
        print(f"Kurs USD/IDR           : {usd_idr} Rupiah")
    else:
        print("Gagal mengambil kurs USD/IDR.")

    if brent_price is not None and usd_idr is not None:
        harga_bbm_dasar = brent_price * usd_idr / 159
        print(f"Estimasi Harga BBM Dasar: Rp{harga_bbm_dasar:,.2f} per liter (belum termasuk pajak dan margin)")
    else:
        harga_bbm_dasar = None

    print("\n--- Harga Saham BP ---")
    if bp_data:
        print(f"LDN Price : {bp_data['ldn_current_price']} ({bp_data['ldn_current_trend']})")
        print(f"BRE Price : {bp_data['bre_current_price']} ({bp_data['bre_current_trend']})")
        print(f"NYC Price : {bp_data['nyc_current_price']} ({bp_data['nyc_current_trend']})")
        print(f"FRA Price : {bp_data['fra_current_price']} ({bp_data['fra_current_trend']})")
    else:
        print("Gagal mengambil data saham BP.")

    if brent_price is not None and usd_idr is not None and bp_data:
        kesimpulan = analyze_trend(bp_data)
        print("\n=== Kesimpulan ===")
        print(kesimpulan)

        save_to_db(brent_price, usd_idr, harga_bbm_dasar, bp_data, kesimpulan)
        print("\nData telah disimpan ke database MongoDB `palugada.bbm`.")

if __name__ == "__main__":
    main_bbm()
