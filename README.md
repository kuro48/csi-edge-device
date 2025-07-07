# CSI Edge Device

エッジデバイス（Raspberry Pi）用のCSIデータ収集・送信システム

## 概要

このプロジェクトは、Raspberry Pi上でCSI（Channel State Information）データを収集し、csi-analysis-serverに送信するエッジデバイスシステムです。

## 機能

- **CSIデータ収集**: tcpdumpを使用したCSIデータの収集
- **自動送信**: 収集したデータをcsi-analysis-serverに自動送信
- **スケジュール実行**: 定期的なデータ収集・送信
- **ベースデータ収集**: 手動でのベースラインデータ収集

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 設定ファイルの作成

```bash
cp config/device_config.json.example config/device_config.json
```

設定ファイルを編集：

```json
{
  "device_id": "raspberry_pi_001",
  "server_url": "http://localhost:8000",
  "api_key": "test-key-123",
  "collection_interval": 300,
  "base_duration": 180,
  "channel_width": "80MHz",
  "location": "lab_room_1"
}
```

### 3. csi-analysis-serverとの連携

1. **csi-analysis-serverを起動**:
   ```bash
   cd ../csi-analysis-server
   docker-compose up --build
   ```

2. **エッジデバイスを起動**:
   ```bash
   python main.py --mode schedule
   ```

## 使用方法

### スケジュール実行（推奨）
```bash
python main.py --mode schedule
```

### 単発データ収集
```bash
python main.py --mode collect
```

### ベースデータ収集
```bash
python main.py --mode base
```

## 設定項目

- `device_id`: デバイスの一意識別子
- `server_url`: csi-analysis-serverのURL
- `api_key`: API認証キー（csi-analysis-serverと同じ値）
- `collection_interval`: データ収集間隔（秒）
- `base_duration`: ベースデータ収集時間（秒）
- `channel_width`: WiFiチャンネル幅
- `location`: 設置場所

## ログ

ログファイルは `logs/` ディレクトリに保存されます。

## トラブルシューティング

1. **tcpdump権限エラー**: `sudo` が必要
2. **ネットワーク接続エラー**: `server_url` を確認
3. **API認証エラー**: `api_key` を確認

## システム要件

- Python 3.7+
- tcpdump
- WiFiアダプター（CSI対応）
- ネットワーク接続

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

## 実行モード

| モード | 説明 | 使用場面 |
|--------|------|----------|
| `schedule` | 通常データを自動収集・送信 | 本番運用 |
| `collect` | 通常データを1回収集・送信 | テスト |
| `base` | ベースラインデータを手動収集・送信 | 環境変化時 |

## ライセンス

このプロジェクトは研究目的で開発されています。 