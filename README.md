# CSI Edge Device

Raspberry Pi用のCSI（Channel State Information）データ収集デバイスです。

## 概要

このデバイスは、Wi-Fi CSIデータを収集し、解析サーバーに送信する最小限の機能を提供します。

## 機能

- **CSIデータ収集**: tcpdumpを使用してCSIデータをPCAPファイルとして収集
- **データ送信**: 収集したPCAPファイルをHTTPで解析サーバーに送信
- **自動実行**: 設定された間隔で自動的にCSIデータ収集と送信を実行
- **手動ベース**: 必要に応じてベースデータを手動収集

## セットアップ

### 必要条件

- Raspberry Pi 4（推奨）
- Python 3.7以上
- tcpdump

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 設定ファイルの編集
cp config/device_config.json.example config/device_config.json
nano config/device_config.json
```

### 設定

`config/device_config.json`を編集して以下を設定：

```json
{
  "device_id": "raspberry_pi_001",
  "server_url": "http://192.168.1.100:8000",
  "api_key": "your_api_key",
  "collection_interval": 300,
  "base_duration": 180
}
```

## 使用方法

### 自動実行（推奨）
```bash
# 通常のCSIデータを自動収集・送信
python main.py --mode schedule
```

### 手動実行
```bash
# 通常のCSIデータを1回収集・送信
python main.py --mode collect

# ベースラインデータを手動収集・送信
python main.py --mode base
```

## アーキテクチャ

```
CSI Edge Device
├── main.py                 # メインスクリプト
├── config/                 # 設定ファイル
├── requirements.txt        # 依存関係
└── README.md              # ドキュメント
```

## データフロー

### 通常データ（自動）
1. **CSI収集**: tcpdumpでCSIデータをPCAPファイルとして収集（60秒間）
2. **メタデータ作成**: デバイス情報とタイムスタンプを含むメタデータを作成
3. **HTTP送信**: PCAPファイルとメタデータを解析サーバーにPOST
4. **ログ記録**: 処理結果をログファイルに記録

### ベースラインデータ（手動）
1. **ベースライン収集**: 設定された時間（デフォルト180秒）でベースラインCSIデータを収集
2. **メタデータ作成**: ベースライン用のメタデータを作成
3. **HTTP送信**: ベースラインデータを解析サーバーにPOST

## 設定項目

| 項目 | 説明 | 例 |
|------|------|-----|
| `device_id` | デバイスの一意識別子 | `"raspberry_pi_001"` |
| `server_url` | 解析サーバーのURL | `"http://192.168.1.100:8000"` |
| `api_key` | API認証キー | `"your_api_key"` |
| `collection_interval` | 通常データ収集間隔（秒） | `300` |
| `base_duration` | ベースライン収集時間（秒） | `180` |

## 実行モード

| モード | 説明 | 使用場面 |
|--------|------|----------|
| `schedule` | 通常データを自動収集・送信 | 本番運用 |
| `collect` | 通常データを1回収集・送信 | テスト |
| `base` | ベースラインデータを手動収集・送信 | 環境変化時 |

## トラブルシューティング

### よくある問題

- **CSIデータが収集できない**: tcpdumpの権限確認
- **サーバーに送信できない**: ネットワーク接続とAPIキーの確認
- **tcpdumpエラー**: sudo権限の確認

### ログ確認

```bash
tail -f logs/edge_device_*.log
```

## ライセンス

このプロジェクトは研究目的で開発されています。 