#!/bin/bash

echo "CSI Edge Device セットアップを開始します..."

# 依存関係のインストール
echo "依存関係をインストールしています..."
pip3 install -r requirements.txt

# 設定ファイルの作成
echo "設定ファイルを作成しています..."
if [ ! -f "config/device_config.json" ]; then
    cp config/device_config.json.example config/device_config.json
    echo "設定ファイルを作成しました: config/device_config.json"
    echo "必要に応じて設定を編集してください。"
else
    echo "設定ファイルは既に存在します: config/device_config.json"
fi

# ディレクトリの作成
echo "必要なディレクトリを作成しています..."
mkdir -p data logs

# 権限の設定
echo "実行権限を設定しています..."
chmod +x main.py
chmod +x setup.sh
chmod +x deploy.sh

echo "セットアップが完了しました！"
echo ""
echo "次の手順:"
echo "1. config/device_config.json を編集して設定を確認"
echo "2. csi-analysis-server を起動: cd ../csi-analysis-server && docker-compose up --build"
echo "3. エッジデバイスを起動: python3 main.py --mode schedule" 