import requests, os


dwr_key = os.getenv('DAWARICH_API_KEY')
if not dwr_key:
    raise ValueError("Environment variable 'DAWARICH_URL' is not set.")

dwr_url = os.getenv('DAWARICH_URL')
if not dwr_url:
    raise ValueError("Environment variable 'DAWARICH_URL' is not set.")
API_ENDPOINT = dwr_url + "/api/v1/owntracks/points?api_key=" + dwr_key






def send_location(lat, lon, tst):
    
    # HTTPヘッダーを設定
    headers = {
    "Content-Type": "application/json"
    }

    # 送信するデータを設定
    data = {
    "_type": "location",
    "topic": "receipt-manager/nmt3325",
    "t": "u",
    "acc": "0",
    "alt": "0",
    "batt": "0",
    "bs": "true",
    "lat": lat,
    "lon": lon,
    "tst": tst, # ここにUNIX時間を入れる
    "vel": "0.0"
    }
    response = requests.post(API_ENDPOINT, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    return response

# テスト用
send_location(35.0, 139.767125, 1743005486) # 東京駅