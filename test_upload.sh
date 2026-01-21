#!/bin/bash
# エッジデバイスのデータアップロードテストスクリプト

set -e

echo "🧪 エッジデバイスのデータアップロードテストを開始します..."

# ディレクトリ確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 設定ファイルの確認
CONFIG_FILE="config/device_config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ エラー: 設定ファイルが見つかりません: $CONFIG_FILE"
    echo "先に setup.sh を実行してデバイスを登録してください"
    exit 1
fi

echo "📄 使用する設定ファイル: $CONFIG_FILE"

# 設定ファイルから情報を取得
SERVER_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['server_url'])")
DEVICE_ID=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['device_id'])")

echo "🔗 サーバーURL: $SERVER_URL"
echo "🆔 デバイスID: $DEVICE_ID"

# サーバーのヘルスチェック
echo ""
echo "🔍 サーバーのヘルスチェック中..."
if ! curl -s "$SERVER_URL/api/v2/health" > /dev/null; then
    echo "❌ エラー: サーバーに接続できません"
    exit 1
fi

echo "✅ サーバーは正常に稼働しています"

# サンプルpcapファイルを作成
echo ""
echo "📦 テスト用ダミーデータを作成中..."
mkdir -p data
SAMPLE_FILE="data/test_$(date +%Y%m%d_%H%M%S).pcap"

# ダミーのpcapデータを作成（最小限のヘッダー）
printf '\xd4\xc3\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x01\x00\x00\x00' > "$SAMPLE_FILE"

echo "作成したテストファイル: $SAMPLE_FILE"

# データアップロード
echo ""
echo "📤 データアップロード中..."

RESPONSE=$(curl -s -X POST "$SERVER_URL/api/v2/csi-data/upload" \
    -F "file=@$SAMPLE_FILE" \
    -F "collection_start_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    -F "collection_duration=60" \
    -F "metadata={\"device_id\":\"$DEVICE_ID\"}")

echo ""
if echo "$RESPONSE" | grep -q '"id"'; then
    echo "✅ データアップロードが成功しました！"
    echo ""
    echo "レスポンス:"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo "❌ データアップロードに失敗しました"
    echo ""
    echo "エラーレスポンス:"
    echo "$RESPONSE"
    exit 1
fi

# テストファイルのクリーンアップ
echo ""
read -p "テストファイルを削除しますか？ [Y/n]: " cleanup
cleanup=${cleanup:-Y}

if [[ "$cleanup" =~ ^[Yy]$ ]]; then
    rm "$SAMPLE_FILE"
    echo "✅ テストファイルを削除しました"
fi
