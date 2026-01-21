# CSI Edge Device

Wi-Fi CSI（Channel State Information）を収集してAPIサーバー（v2）に送信するエッジデバイス用プログラムです。

## 主な機能

- **APIサーバーv2対応**: 最新のAPIエンドポイントとスキーマに対応
- **シンプルな運用**: 認証不要のアップロードフロー
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
- **サーバーURL**: バックエンドAPIのURL（例: `http://localhost:8000`）
- **デバイスID**: 一意の識別子（例: `lab-device-001`）

セットアップスクリプトが自動で実行する内容：
1. Python仮想環境の作成
2. 依存パッケージのインストール
3. サーバー稼働確認
4. 設定ファイル生成（`config/device_config.json`）

### 2. 動作確認

#### 2-1. サーバー接続テスト

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 接続テスト実行
python3 test_upload.py --config config/device_config.json --file data/sample.pcap
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
python3 main.py
```

#### 3-2. スケジュール実行（常時稼働）

```bash
# スケジュールモードで起動
python3 main.py --mode schedule
```

このモードでは、設定ファイルの`collection_interval`（デフォルト: 300秒）ごとにCSIデータを自動収集・送信します。

## ファイル構成

```
csi-edge-device/
├── main.py                   # メインプログラム（通常CSI収集）
├── collect_base.py          # ベースCSI収集プログラム
├── setup.sh                  # セットアップスクリプト（推奨）
├── test_upload.sh           # テストスクリプト
├── test_upload.py           # テストスクリプト（PCAP指定）
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

### 実行

```bash
# 単発でCSIデータ収集・送信
python3 main.py --mode collect
```

**注**: ベースCSI収集は専用スクリプト `collect_base.py` を使用してください（下記参照）。

### デバイス情報の確認

```bash
# デバイス設定を確認
cat config/device_config.json
```

### ベースCSI（基準データ）の収集

**重要**: ベースCSIは、監視エリアに**人物がいない状態**で収集する必要があります。

#### ベースCSIとは？

ベースCSI（基準データ）は、Wi-Fi環境の基準状態を定義するデータです：

| 用途 | 説明 |
|------|------|
| **キャリブレーション** | Wi-Fi環境の基準状態を定義 |
| **ノイズフロア測定** | 人物がいない状態のCSIパターン |
| **比較基準** | 測定データとの相対値計算用 |
| **呼吸検出の基準化** | 人物有無の判定基準 |

#### ベースCSI収集手順

```bash
# 1. 監視エリアから人を退避させる
# 2. 環境を安定させる（物の移動や設定変更をしない）
# 3. ベースCSI収集スクリプトを実行

python3 collect_base.py
```

#### 実行内容

- **収集時間**: デフォルト180秒（3分間）
  - 設定ファイルの`base_duration`で変更可能
- **データタイプ**: `type: "base"` として自動的にサーバーに送信
- **ファイル名**: `data/base_csi_YYYYmmdd_HHMMSS.pcap`

#### 実行例

```bash
$ python3 collect_base.py

============================================================
🎯 BASE CSI COLLECTION AND UPLOAD
============================================================

📋 Instructions:
   1. Ensure NO PERSON is in the monitoring area
   2. Keep the environment stable during collection
   3. Do not move objects or change room configuration

⏱️  Waiting 5 seconds before starting...
   Press Ctrl+C to cancel if needed

============================================================
⚠️  IMPORTANT: Ensure NO PERSON is in the monitoring area
============================================================
Starting BASE CSI collection: 180s on wlan0:5500
Collection will take approximately 3.0 minutes
============================================================

Collection in progress...
(This process will run for the configured duration)

✅ Base CSI data collected successfully
   File: base_csi_20250112_143022.pcap
   Size: 3,145,728 bytes (3.00 MB)
   Duration: 180.2s

============================================================
Uploading BASE CSI to http://api.csi.kur048.com/api/v2/csi-data/upload-public...
============================================================

✅ Upload successful
   File: base_csi_20250112_143022.pcap
   Response ID: 12345
   Type: BASE CSI

============================================================
✅ BASE CSI COLLECTION AND UPLOAD COMPLETED
============================================================
```

#### 設定オプション

`config/device_config.json` で以下を設定できます：

```json
{
  "base_duration": 180,              // ベースCSI収集時間（秒）
  "delete_after_upload": false       // 送信後にローカルファイルを削除するか
}
```

#### 推奨実施タイミング

- システム初回セットアップ時
- 設置場所を変更した場合
- Wi-Fi環境に大きな変更があった場合（ルーター交換など）
- 定期的なキャリブレーション（月1回程度）

## API連携

### 使用するエンドポイント

- `POST /api/v2/csi-data/upload` - CSIデータアップロード
- `GET /api/v2/health` - サーバーヘルスチェック

### 認証方式

**認証不要**: デバイス認証は不要です。`metadata.device_id`で識別します。

### 送信データ形式

**フォームデータ:**
- `file`: PCAPファイル（バイナリ）
- `collection_start_time`: 収集開始時刻（ISO 8601）
- `collection_duration`: 収集時間（秒）

**メタデータ（JSON）:**
```json
{
  "type": "csi_measurement",
  "device_id": "edge-device-001",
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
# サーバー疎通確認
curl http://localhost:8000/api/v2/health
```

### 接続エラー

```bash
# サーバーのヘルスチェック
curl http://api.csi.kur048.com/api/v2/health

# ネットワーク接続確認
ping api.csi.kur048.com
```

### CSIデータ収集エラー

```bash
# sudo権限で実行されているか確認
sudo python3 main.py

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

## 依存関係

- Python 3.7以上
- requests
- tcpdump（CSIデータ収集用）

## ライセンス

MIT License

## 関連プロジェクト

- [CSI Web Platform](https://github.com/kuro48/csi-web-platform) - バックエンド・フロントエンド統合システム
