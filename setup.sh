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
pip install -q requests schedule

# サーバーURLの入力
echo ""
read -p "サーバーURL [http://api.csi.kur048.com]: " server_url
server_url=${server_url:-http://api.csi.kur048.com}

# サーバーの稼働確認
echo "🔍 サーバーの稼働確認中..."
if ! curl -s "$server_url/health" > /dev/null; then
    echo "❌ エラー: サーバーに接続できません: $server_url"
    exit 1
fi

echo "✅ サーバーは正常に稼働しています"

# 管理者認証情報の入力
echo ""
echo "📝 管理者アカウントでログインしてデバイスを登録します"
read -p "ユーザー名 [admin]: " username
username=${username:-admin}

read -sp "パスワード: " password
echo ""

if [ -z "$password" ]; then
    password="admin123"
fi

# デバイスIDの入力
echo ""
read -p "デバイスID [test_device_001]: " device_id
device_id=${device_id:-test_device_001}

# デバイス登録
echo ""
echo "🔐 デバイス登録を実行中..."
python3 register_device.py \
    --server "$server_url" \
    --username "$username" \
    --device-id "$device_id" \
    --location "lab"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ セットアップが完了しました！"
    echo ""
    echo "次のコマンドでデバイスを起動できます:"
    echo "  source venv/bin/activate"
    echo "  python3 main.py --config config/device_config.json"
else
    echo ""
    echo "❌ デバイス登録に失敗しました"
    exit 1
fi
