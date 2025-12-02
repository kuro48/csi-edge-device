# CSI Edge Device

Wi-Fi CSI（Channel State Information）を収集してAPIサーバー（v2）に送信するエッジデバイス用プログラムです。

## 主な機能

- **APIサーバーv2対応**: 最新のAPIエンドポイントとスキーマに対応
- **デバイス専用トークン認証**: セキュアな認証方式
- **自動デバイス登録**: セットアップスクリプトで簡単に登録
- **エラーハンドリング強化**: 安定した長時間運用
- **柔軟な設定**: 環境に応じた細かな調整が可能

## クイックスタート

### 1. セットアップ（初回のみ）

```bash
# セットアップスクリプトを実行
./setup.sh
```

対話形式で以下を入力します：
- サーバーURL（デフォルト: `http://api.csi.kur048.com`）
- 管理者ユーザー名（デフォルト: `admin`）
- 管理者パスワード
- デバイスID（デフォルト: `test_device_001`）

### 2. 動作テスト

```bash
# データアップロードテストを実行
./test_upload.sh
```

### 3. デバイス起動

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# メインプログラムを起動
python3 main.py --config config/device_config.json
```

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
| `device_token` | デバイス認証トークン | セットアップ時に自動設定 |
| `collection_interval` | データ収集間隔（秒） | 300 |
| `collection_duration` | 1回の収集時間（秒） | 60 |
| `channel_width` | Wi-Fiチャネル幅 | `80MHz` |
| `network_interface` | ネットワークインターフェース | `wlan0` |
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

デバイス専用トークン（Bearer認証）：
```
Authorization: Bearer device_<device_id>_<token_hash>
```

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

### 認証エラー

```bash
# デバイストークンの確認
cat config/device_config.json | grep device_token

# サーバー側でデバイス登録を確認
curl -H "Authorization: Bearer <admin_token>" \
     http://api.csi.kur048.com/api/v2/devices/
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
