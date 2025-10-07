# CSI Edge Device (APIサーバーv2対応版)

Wi-Fi CSI（Channel State Information）を収集してAPIサーバー（v2）に送信するエッジデバイス用プログラムです。

## 主な改良点

- **APIサーバーv2対応**: 最新のAPIエンドポイントとスキーマに対応
- **デバイス専用トークン認証**: `device_<device_id>_<token_hash>` 形式の認証
- **改良されたメタデータ形式**: JSON形式でのメタデータ送信
- **エラーハンドリング強化**: タイムアウト・接続エラーの適切な処理
- **設定の柔軟性**: より多くの設定項目をサポート
- **デバイス登録機能**: 新規デバイスの自動登録

## ファイル構成

```
csi-edge-device/
├── main_improved.py              # メインプログラム（v2対応版）
├── register_device.py            # デバイス登録スクリプト
├── config/
│   └── device_config_v2.json    # 設定ファイル（v2形式）
├── requirements_v2.txt          # 依存関係
└── README_v2.md                # このファイル
```

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements_v2.txt
```

### 2. デバイスの登録

新しいデバイスをAPIサーバーに登録します：

```bash
python3 register_device.py --device-id "raspberry_pi_002" --location "lab_room_2" --username admin
```

### 3. 設定ファイルの確認

生成された設定ファイル `config/device_config_v2.json` を確認・編集：

```json
{
  "device_id": "raspberry_pi_002",
  "server_url": "http://localhost:8000",
  "device_token": "device_raspberry_pi_002_abc123def456",
  "collection_interval": 300,
  "collection_duration": 60,
  "base_duration": 180,
  "channel_width": "80MHz",
  "location": "lab_room_2",
  "network_interface": "wlan0",
  "csi_port": 5500,
  "upload_timeout": 60,
  "health_check_interval": 3600,
  "delete_after_upload": false
}
```

## 使用方法

### 接続テスト

```bash
python3 main_improved.py --mode test
```

### 単発でCSIデータ収集・送信

```bash
# 通常のCSIデータ収集
python3 main_improved.py --mode collect

# ベースラインデータ収集
python3 main_improved.py --mode base
```

### スケジュール実行（常時稼働）

```bash
python3 main_improved.py --mode schedule
```

## 設定項目

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `device_id` | デバイス識別子 | 必須 |
| `server_url` | APIサーバーURL | `http://localhost:8000` |
| `device_token` | デバイス認証トークン | 必須 |
| `collection_interval` | 通常データ収集間隔（秒） | 300 |
| `collection_duration` | 1回の収集時間（秒） | 60 |
| `base_duration` | ベースライン収集時間（秒） | 180 |
| `channel_width` | チャネル幅 | `80MHz` |
| `location` | 設置場所 | `unknown` |
| `network_interface` | ネットワークインターフェース | `wlan0` |
| `csi_port` | CSI取得ポート | 5500 |
| `upload_timeout` | アップロードタイムアウト（秒） | 60 |
| `health_check_interval` | ヘルスチェック間隔（秒） | 3600 |
| `delete_after_upload` | 送信後ファイル削除フラグ | false |

## APIエンドポイント

### 使用するエンドポイント

- `POST /api/v2/csi-data/upload` - CSIデータアップロード
- `GET /health` - サーバーヘルスチェック
- `GET /api/v2/devices/{device_id}` - デバイス情報取得

### 認証

デバイス専用トークン（Bearer認証）：
```
Authorization: Bearer device_<device_id>_<token_hash>
```

## 送信データ形式

### フォームデータ

- `file`: PCAPファイル（バイナリ）
- `collection_start_time`: 収集開始時刻（ISO 8601形式）
- `collection_duration`: 収集時間（秒）
- `metadata`: メタデータ（JSON文字列）

### メタデータ例

```json
{
  "type": "csi_measurement",
  "timestamp": 1640995200,
  "collection_duration": 60,
  "channel_width": "80MHz",
  "location": "lab_room_1",
  "network_interface": "wlan0",
  "csi_port": 5500,
  "file_size": 1048576
}
```

## ログ

ログファイルは `logs/` ディレクトリに日時付きで保存されます：

- ファイル名: `edge_device_YYYYMMDD_HHMMSS.log`
- レベル: INFO以上
- 出力先: ファイル + コンソール

## systemd設定例

常時稼働させる場合のsystemdサービス設定：

```ini
[Unit]
Description=CSI Edge Device (v2)
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/csi-edge-device
ExecStart=/usr/bin/python3 main_improved.py --mode schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## トラブルシューティング

### よくある問題

1. **認証エラー**
   - デバイストークンが正しく設定されているか確認
   - デバイスがAPIサーバーに登録されているか確認

2. **ファイル送信エラー**
   - ネットワーク接続を確認
   - サーバーURLが正しいか確認
   - タイムアウト設定を調整

3. **CSIデータ収集エラー**
   - `sudo` 権限で実行されているか確認
   - ネットワークインターフェースが存在するか確認
   - tcpdumpがインストールされているか確認

### ログの確認

```bash
# 最新のログファイルを確認
ls -la logs/
tail -f logs/edge_device_YYYYMMDD_HHMMSS.log
```

### 接続テスト

```bash
# サーバー接続テスト
python3 main_improved.py --mode test

# 手動でAPIテスト
curl -H "Authorization: Bearer device_raspberry_pi_001_abc123" \
     http://localhost:8000/api/v2/devices/raspberry_pi_001
```

## 更新履歴

- **v2.0**: APIサーバーv2対応、デバイス専用トークン認証、エラーハンドリング強化
- **v1.0**: 初期バージョン