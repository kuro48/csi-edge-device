#!/bin/bash

echo "=== CSI Edge Device Setup ==="

# 必要なディレクトリの作成
mkdir -p logs data

# Python依存関係のインストール
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# 設定ファイルの確認
if [ ! -f "config/device_config.json" ]; then
    echo "Please copy config/device_config.json.example to config/device_config.json and edit it"
    echo "cp config/device_config.json.example config/device_config.json"
    exit 1
fi

# tcpdumpの権限確認
echo "Checking tcpdump permissions..."
if ! sudo tcpdump --version > /dev/null 2>&1; then
    echo "Error: tcpdump not found or no sudo access"
    exit 1
fi

echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Edit config/device_config.json with your settings"
echo "2. Test with: python3 main.py --mode collect"
echo "3. Run in production: python3 main.py --mode schedule" 