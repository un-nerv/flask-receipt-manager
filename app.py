from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
import os
from google import genai
from google.genai import types
from werkzeug.utils import secure_filename
import base64
import sqlite3
import json


#google api keyの設定
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GOOGLE_API_KEY)

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
        date TEXT NOT NULL,
        total_amount REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/add", methods=["POST"])
def add_receipt():
    store_name = request.form["store_name"]
    date = request.form["date"]
    total_amount = request.form["total_amount"]

    # データベースにデータを保存
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO receipts (store_name, date, total_amount)
    VALUES (?, ?, ?)
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
                  いかがjsonのフォーマットの例です。いかに指定された要素以外は含めないでください。また、店名は省略せず全て含めてください。
                    {
                        "store_name": "スーパーA",
                        "date": "2022-01-01",
                        "total_amount": 1000
                    }
                  
                  """,
                  types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        ],
        config={'response_mime_type': 'application/json'}
    )

    data_dict = json.loads(response.text)
    print(data_dict)
    # データベースにデータを保存
    conn = sqlite3.connect("receipts.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO receipts (store_name, date, total_amount)
    VALUES (?, ?, ?)
    """, (data_dict["store_name"], data_dict["date"], data_dict["total_amount"]))
    conn.commit()
    conn.close

    flash(response.text)
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # 保存した画像をブラウザで表示
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
@app.route('/delete/<filename>')
def delete_file(filename):
    #画像削除
    safe_filename = secure_filename(filename)#相対パスによる悪意のあるファイル削除から保護
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

@app.route('/receipts')
def show_receipts():
    receipts = get_receipts()
    # データを HTML テンプレートに渡す
    return render_template('receipts.html', receipts=receipts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)