from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
import os, base64, sqlite3, json, requests

# geminiのクライアントをインポート
from google import genai
from google.genai import types

# ファイル名の安全性を確保するための関数
from werkzeug.utils import secure_filename

#unix時間を取得するためのモジュール
from datetime import datetime

import dawarich


#google api keyの設定
GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

print(GEMINI_API_KEY)

app = Flask(__name__)

app.secret_key = '6461fcb1c4b14a9880096b4abd26a77c34bb0a849071dad6'  # フラッシュメッセージには必須

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'heic'}

def allowed_file(filename):
    # ファイル名に拡張子が含まれているか確認し、許可された拡張子かチェック
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# アップロードフォルダを設定
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # フォルダが存在しない場合は作成
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MBの制限

# データベース初期化
def init_db():
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()

    # テーブル作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT NOT NULL,
        phone_number TEXT,
        address TEXT,
        date TEXT NOT NULL,
        time TEXT,
        total_amount REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_db()

# 手動でレシートを追加するエンドポイント
@app.route("/add", methods=["POST"])
def add_receipt():
    store_name = request.form["store_name"]
    date = request.form["date"]
    total_amount = request.form["total_amount"]

    # データベースにデータを保存
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO receipts (store_name, phone_number, address, date, total_amount)
    VALUES (?, ?, ?, ?, ?)
    """, (store_name, date, total_amount))
    conn.commit()
    conn.close()

    return "Receipt added successfully!"


@app.route('/')
def home():
    # アップロードされた画像一覧を取得
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    # ファイルが送信されているかチェック
    if 'file' not in request.files:
        flash("No file part")
        return "No file part"
    file = request.files['file']
    file_size = file.stream.tell()
    # ファイルサイズのチェック
    if file_size > 10 * 1024 * 1024:
        flash("File size exceeds the limit: 10MB")
        return "File size exceeds the limit"
    # ファイル名のチェック
    if file.filename == '':
        flash("No selected file")
        return "No selected file"

    # ファイル形式のバリデーション
    if not allowed_file(file.filename):
        flash("File type not allowed. Please upload JPG, PNG, or GIF.")
        return "File type not allowed"

    # ファイルを保存    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    flash(f"File uploaded successfully: {file.filename}")

    #画像をバイナリとして読む
    with open(file_path, "rb") as f:
        image_bytes = f.read()



    #geminiにデータを送信
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=["""レシートに書いてあることを以下のjsonフォーマットで教えてください。
                  以下がjsonのフォーマットの例です。指定された要素以外は含めないでください。
                  必ず以下のフォーマットに従い、"{"で始めて、"}"で閉じてください。
                  また、店名は省略せず全て含め、チェーン店などで店名に地名が含まれている場合は、地名も店名に含めてください。
                  電話番号が二つある場合は店舗用の番号を採用して一つだけ返答してください。電話番号にはハイフンを含めないでください。
                    {
                        "store_name": "スーパーA 新宿店",
                        "phone_number": "0123456789",
                        "address": "東京都新宿区西新宿1-1-1",
                        "date": "2022-01-01",
                        "time": "19:34:00",
                        "total_amount": 1000
                        
                    }
                  
                  """,
                  types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        ],
        config={'response_mime_type': 'application/json'}
    )

    # レスポンスをテキストファイルに保存
    with open("/logs/response.txt", mode='a', encoding="utf-8") as file:
        file.write(response.text)


    data_dict = json.loads(response.text)
    print(data_dict)
    
    # データベースにデータを保存
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO receipts (store_name, phone_number, address, date, time, total_amount)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data_dict.get("store_name", None),
        data_dict.get("phone_number", None),
        data_dict.get("address", None),
        data_dict.get("date", None), 
        data_dict.get("time", "00:00:00") or "00:00:00", # 時刻がない場合は 00:00:00 とする
        data_dict.get("total_amount", None)
    ))
    conn.commit()
    conn.close()

    # google map apiにアクセス
    if not MAPS_API_KEY:
        raise ValueError("Google Maps API key is not set. Please check your environment variables.")
    
    API_ENDPOINT = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={data_dict.get('phone_number', '')}+{data_dict.get('store_name', '')}&key={MAPS_API_KEY}"
    result = requests.get(API_ENDPOINT)

    point_dict = json.loads(result.text)


    
    # レスポンスをデバッグ用に表示
    print("Google Maps API Response:", result.text)


    
    # Google Maps APIのレスポンスをパース
    point_dict = json.loads(result.text)

    # 経度と緯度を取得
    if point_dict.get("status") == "OK" and point_dict.get("results"):
        location = point_dict["results"][0]["geometry"]["location"]
        lon = location["lng"]  # 経度
        lat = location["lat"]  # 緯度
        print(f"Longitude: {lon}, Latitude: {lat}")
    else:
        lon = None
        lat = None
        print("Failed to retrieve location data from Google Maps API.")

    # UNIX時間に整形
    date_str= data_dict.get("date", None) + " " + data_dict.get("time", "00:00:00")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    unix_time = int(date_obj.timestamp())


    # 位置情報送信を行うかどうかのフラグ
    data_send = False


    if lon is not None and lat is not None and data_send == True:
        # 位置情報をdawarichに送信
        dawarich.send_location(lat, lon, unix_time)
        print(f"Sending location to Dawarich: Longitude={lon}, Latitude={lat}")
        

    # フラッシュメッセージを表示
    debugging_message = f"Dawarich location send\n Longitude: {lon}, Latitude: {lat}\n date_time: {date_str}\n unix_time: {unix_time}"
    flash(debugging_message)
    flash(response.text)
    flash(result.text)
    


    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # 保存した画像をブラウザで表示
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/delete/<filename>')
def delete_file(filename):
    #画像削除
    safe_filename = secure_filename(filename) #相対パスによる悪意のあるファイル削除から保護
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        return f"File not found: {safe_filename}", 404
    return redirect(url_for('home'))


# データベースからデータを取得する関数
def get_receipts():
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM receipts")
    receipts = cursor.fetchall()
    conn.close()
    return receipts

# レシート一覧を表示するエンドポイント
@app.route('/receipts')
def show_receipts():
    receipts = get_receipts()
    # データを HTML テンプレートに渡す
    return render_template('receipts.html', receipts=receipts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)