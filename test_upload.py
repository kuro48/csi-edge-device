#!/usr/bin/env python3
"""
既存のpcapファイルをアップロードするテストスクリプト
"""
import sys
import argparse
from main import EdgeDeviceManager


def main():
    parser = argparse.ArgumentParser(description="CSIデータアップロードテスト")
    parser.add_argument("--config", type=str, default="config/production_config.json", help="設定ファイルのパス")
    parser.add_argument("--file", type=str, required=True, help="アップロードするpcapファイルのパス")
    parser.add_argument("--type", type=str, default="csi_measurement", choices=["csi_measurement", "base"], help="データタイプ")

    args = parser.parse_args()

    # エッジデバイスマネージャーの初期化
    try:
        manager = EdgeDeviceManager(args.config)
        print(f"✅ エッジデバイスマネージャーを初期化しました")
        print(f"   デバイスID: {manager.config['device_id']}")
        print(f"   サーバーURL: {manager.config['server_url']}")
    except Exception as e:
        print(f"❌ 初期化に失敗しました: {e}")
        sys.exit(1)

    # 接続テスト
    print("\n🔌 サーバー接続テスト中...")
    if not manager.test_connection():
        print("❌ サーバーへの接続に失敗しました")
        sys.exit(1)
    print("✅ サーバーへの接続に成功しました")

    # ファイルアップロード
    print(f"\n📤 ファイルアップロード中: {args.file}")
    success = manager._send_csi_data(args.file, args.type)

    if success:
        print(f"✅ ファイルのアップロードに成功しました")
        sys.exit(0)
    else:
        print(f"❌ ファイルのアップロードに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
