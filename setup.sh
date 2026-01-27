#!/bin/bash
# エッジデバイスセットアップスクリプト

set -e

echo "🚀 エッジデバイスのセットアップを開始します..."

# ディレクトリ確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Python仮想環境の確認
if [ ! -d "venv" ]; then
    echo "📦 Python仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate

# 依存関係のインストール
echo "📥 依存関係をインストール中..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# サーバーURLの入力
echo ""
read -p "サーバーURL [http://api.csi.kur048.com]: " server_url
server_url=${server_url:-http://api.csi.kur048.com}

# サーバーの稼働確認
echo "🔍 サーバーの稼働確認中..."
if ! curl -s "$server_url/api/v2/health" > /dev/null; then
    echo "❌ エラー: サーバーに接続できません: $server_url"
    exit 1
fi

echo "✅ サーバーは正常に稼働しています"

# デバイスIDの入力
echo ""
read -p "デバイスID [test_device_001]: " device_id
device_id=${device_id:-test_device_001}

# 設定ファイル生成
echo ""
echo "📝 設定ファイルを生成します..."
mkdir -p config
cat > config/device_config.json <<EOF
{
  "device_id": "${device_id}",
  "server_url": "${server_url}",
  "collection_interval": 300,
  "collection_duration": 60,
  "base_duration": 60,
  "channel_width": "80MHz",
  "network_interface": "wlan0",
  "csi_port": 5500,
  "upload_timeout": 60,
  "health_check_interval": 3600,
  "delete_after_upload": false
}
EOF

echo ""
echo "✅ セットアップが完了しました！"
echo ""
echo "次のコマンドでデバイスを起動できます:"
echo "  source venv/bin/activate"
echo "  python3 main.py"
