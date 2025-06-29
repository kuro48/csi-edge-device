# CSI Edge Device

Raspberry Pi用のCSI（Channel State Information）データ収集デバイスです。

## 概要

このデバイスは、Wi-Fi CSIデータを収集し、解析サーバーに送信する最小限の機能を提供します。

## 機能

- **CSIデータ収集**: tcpdumpを使用してCSIデータをPCAPファイルとして収集
- **データ送信**: 収集したPCAPファイルをHTTPで解析サーバーに送信
- **スケジュール実行**: 設定された間隔で自動的にデータ収集と送信を実行
- **ベースライン収集**: 定期的なベースラインデータの収集と送信

## セットアップ

### 必要条件

- Raspberry Pi 4（推奨）
- Python 3.7以上
- tcpdump
- nexmon（CSI取得用）

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 設定ファイルの編集
nano config/device_config.json
```

### 設定

`config/device_config.json`を編集して以下を設定：

```json
{
  "device": {
    "id": "raspberry_pi_001",
    "location": "room_101"
  },
  "csi_collection": {
    "interface": "wlan0",
    "window_size": 60,
    "channel_width": "80MHz"
  },
  "server": {
    "url": "http://192.168.1.100:8000",
    "api_key": "your_api_key"
  },
  "schedule": {
    "data_collection_interval": 300
  }
}
```

## 使用方法

### スケジュール実行（推奨）
```bash
python main.py --mode schedule
```

### 単発実行
```bash
# CSIデータ収集
python main.py --mode collect

# ベースライン収集
python main.py --mode baseline
```

## アーキテクチャ

```
CSI Edge Device
├── main.py                 # メインスクリプト
├── scripts/
│   ├── csi_collection/     # CSI収集モジュール
│   └── http_client/        # HTTP送信モジュール
├── config/                 # 設定ファイル
└── requirements.txt        # 依存関係
```

## データフロー

1. **CSI収集**: tcpdumpでCSIデータをPCAPファイルとして収集
2. **メタデータ作成**: デバイス情報とタイムスタンプを含むメタデータを作成
3. **HTTP送信**: PCAPファイルとメタデータを解析サーバーにPOST
4. **ログ記録**: 処理結果をログファイルに記録

## トラブルシューティング

### よくある問題

- **CSIデータが収集できない**: ネットワークインターフェースの確認
- **サーバーに送信できない**: ネットワーク接続とAPIキーの確認
- **tcpdumpエラー**: sudo権限の確認

### ログ確認

```bash
tail -f logs/edge_device_*.log
```

## ライセンス

このプロジェクトは研究目的で開発されています。 