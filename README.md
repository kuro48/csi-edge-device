# CSI Edge Device

Wi-Fi CSI（Channel State Information）を収集してAPIサーバー（v2）に送信するエッジデバイス用プログラムです。

## 主な機能

- **APIサーバーv2対応**: 最新のAPIエンドポイントとスキーマに対応
- **シンプルな認証**: 研究用に簡略化（デバイス認証不要）
- **自動デバイス登録**: セットアップスクリプトで簡単に登録
- **エラーハンドリング強化**: 安定した長時間運用
- **柔軟な設定**: 環境に応じた細かな調整が可能

## クイックスタート

### 前提条件

- **Raspberry Pi**（または互換デバイス）
- **Python 3.7以上**
- **tcpdump**（CSIデータ収集用）
- **Wi-Fiアダプター**（CSI取得対応のもの）

### 1. 初回セットアップ

#### 1-1. リポジトリのクローン

```bash
git clone https://github.com/kuro48/csi-edge-device.git
cd csi-edge-device
```

#### 1-2. セットアップスクリプト実行

```bash
# セットアップスクリプトを実行
chmod +x setup.sh
./setup.sh
```

対話形式で以下を入力します：
- **サーバーURL**: バックエンドAPIのURL（例: `http://localhost:8000` または `http://api.csi.kur048.com`）
- **管理者ユーザー名**: デフォルト `admin`
- **管理者パスワード**: デフォルト `admin123`（初回ログイン後に変更推奨）
- **デバイスID**: 一意の識別子（例: `lab-device-001`）

セットアップスクリプトが自動で実行する内容：
1. Python仮想環境の作成
2. 依存パッケージのインストール
3. サーバー稼働確認
4. デバイス登録
5. 設定ファイル生成（`config/device_config.json`）

### 2. 動作確認

#### 2-1. サーバー接続テスト

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 接続テスト実行
python3 main.py --config config/device_config.json --mode test
```

#### 2-2. データアップロードテスト

```bash
# テストスクリプトを実行
chmod +x test_upload.sh
./test_upload.sh
```

成功すると以下のような出力が表示されます：
```
✅ データアップロードが成功しました！
```

### 3. デバイス起動

#### 3-1. 単発実行（テスト用）

```bash
# CSIデータを1回収集して送信
python3 main.py --config config/device_config.json --mode collect
```

#### 3-2. スケジュール実行（常時稼働）

```bash
# スケジュールモードで起動
python3 main.py --config config/device_config.json --mode schedule
```

このモードでは、設定ファイルの`collection_interval`（デフォルト: 300秒）ごとにCSIデータを自動収集・送信します。

## ファイル構成

```
csi-edge-device/
├── main.py                   # メインプログラム
├── register_device.py        # デバイス登録スクリプト
├── setup.sh                  # セットアップスクリプト（推奨）
├── test_upload.sh           # テストスクリプト
├── config/
│   ├── device_config.json          # 設定ファイル
│   └── device_config.json.example  # 設定例
├── requirements.txt         # Python依存関係
├── data/                    # CSIデータ保存ディレクトリ
└── logs/                    # ログファイル保存ディレクトリ
```

## 設定ファイル

`config/device_config.json` の主要設定項目：

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `device_id` | デバイス識別子 | `test_device_001` |
| `server_url` | APIサーバーURL | `http://api.csi.kur048.com` |
| `collection_interval` | データ収集間隔（秒） | 300 |
| `collection_duration` | 1回の収集時間（秒） | 60 |
| `base_duration` | ベースライン収集時間（秒） | 180 |
| `channel_width` | Wi-Fiチャネル幅 | `80MHz` |
| `network_interface` | ネットワークインターフェース | `wlan0` |
| `csi_port` | CSIデータ受信ポート | 5500 |
| `location` | 設置場所 | `lab` |
| `delete_after_upload` | 送信後ファイル削除 | false |

## 使用方法

### モード別実行

```bash
# 接続テスト
python3 main.py --mode test

# 単発でCSIデータ収集・送信
python3 main.py --mode collect

# ベースラインデータ収集
python3 main.py --mode base

# スケジュール実行（常時稼働）
python3 main.py --mode schedule
```

### デバイス情報の確認

```bash
# デバイスステータスを確認
python3 main.py --mode status
```

## API連携

### 使用するエンドポイント

- `POST /api/v2/csi-data/upload` - CSIデータアップロード
- `GET /health` - サーバーヘルスチェック
- `GET /api/v2/devices/{device_id}` - デバイス情報取得

### 認証方式

**研究用に簡略化**: デバイス認証は不要です。`device_id`でデバイスを識別します。

### 送信データ形式

**フォームデータ:**
- `file`: PCAPファイル（バイナリ）
- `device_id`: デバイスID
- `collection_start_time`: 収集開始時刻（ISO 8601）
- `collection_duration`: 収集時間（秒）

**メタデータ（JSON）:**
```json
{
  "type": "csi_measurement",
  "timestamp": 1640995200,
  "collection_duration": 60,
  "channel_width": "80MHz",
  "location": "lab",
  "network_interface": "wlan0",
  "file_size": 1048576
}
```

## systemd設定（常時稼働）

Raspberry Piなどで常時稼働させる場合：

```bash
# systemdサービスファイルを作成
sudo cp systemd/csi-edge-device.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable csi-edge-device
sudo systemctl start csi-edge-device

# ステータス確認
sudo systemctl status csi-edge-device

# ログ確認
sudo journalctl -u csi-edge-device -f
```

## トラブルシューティング

### デバイス登録エラー

```bash
# サーバー側でデバイス登録を確認
# まずユーザーログイン
curl -X POST http://localhost:8000/api/v2/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'

# デバイス一覧取得
curl -X GET http://localhost:8000/api/v2/devices/ \
     -H "Authorization: Bearer <取得したトークン>"
```

### 接続エラー

```bash
# サーバーのヘルスチェック
curl http://api.csi.kur048.com/health

# ネットワーク接続確認
ping api.csi.kur048.com
```

### CSIデータ収集エラー

```bash
# sudo権限で実行されているか確認
sudo python3 main.py --mode collect

# ネットワークインターフェースの確認
ip link show

# tcpdumpのインストール確認
which tcpdump
```

### ログの確認

```bash
# 最新のログファイル
ls -lt logs/ | head -n 5

# ログをリアルタイム表示
tail -f logs/edge_device_*.log
```

## 開発・デバッグ

### 仮想環境の作成

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 設定ファイルのテスト

```bash
# 設定ファイルの構文チェック
python3 -c "import json; json.load(open('config/device_config.json'))"
```

### 手動でデバイス登録

```bash
python3 register_device.py \
    --server http://api.csi.kur048.com \
    --username admin \
    --password <password> \
    --device-id my_device \
    --name "マイデバイス" \
    --location "研究室"
```

## 依存関係

- Python 3.7以上
- requests
- schedule
- tcpdump（CSIデータ収集用）

## ライセンス

MIT License

## 関連プロジェクト

- [CSI Web Platform](https://github.com/kuro48/csi-web-platform) - バックエンド・フロントエンド統合システム
