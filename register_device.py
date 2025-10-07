#!/usr/bin/env python3
"""
デバイス登録スクリプト
新しいエッジデバイスをAPIサーバーに登録し、デバイストークンを取得
"""

import json
import sys
import argparse
import requests
import getpass
from typing import Optional, Dict, Any


class DeviceRegistration:
    """デバイス登録クラス"""

    def __init__(self, server_url: str):
        """
        初期化

        Args:
            server_url: APIサーバーのURL
        """
        self.server_url = server_url.rstrip('/')

    def login(self, username: str, password: str) -> Optional[str]:
        """
        ユーザーログインしてJWTトークンを取得

        Args:
            username: ユーザー名
            password: パスワード

        Returns:
            JWTトークン
        """
        try:
            url = f"{self.server_url}/api/v2/auth/login"
            data = {
                "username": username,
                "password": password
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print("ログインに成功しました")
                return result.get('access_token')
            else:
                print(f"ログインに失敗しました (HTTP {response.status_code}): {response.text}")
                return None

        except Exception as e:
            print(f"ログイン中にエラーが発生しました: {e}")
            return None

    def register_device(self, access_token: str, device_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        デバイスを登録

        Args:
            access_token: JWTアクセストークン
            device_info: デバイス情報

        Returns:
            登録結果
        """
        try:
            url = f"{self.server_url}/api/v2/devices/"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json=device_info, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                print(f"デバイス登録に成功しました: {result.get('device_id')}")
                return result
            else:
                print(f"デバイス登録に失敗しました (HTTP {response.status_code}): {response.text}")
                return None

        except Exception as e:
            print(f"デバイス登録中にエラーが発生しました: {e}")
            return None

    def get_device_info(self, access_token: str, device_id: str) -> Optional[Dict[str, Any]]:
        """
        デバイス情報を取得

        Args:
            access_token: JWTアクセストークン
            device_id: デバイスID

        Returns:
            デバイス情報
        """
        try:
            url = f"{self.server_url}/api/v2/devices/{device_id}"
            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"デバイス情報取得に失敗しました (HTTP {response.status_code}): {response.text}")
                return None

        except Exception as e:
            print(f"デバイス情報取得中にエラーが発生しました: {e}")
            return None

    def generate_config_file(self, device_info: Dict[str, Any], output_file: str):
        """
        設定ファイルを生成

        Args:
            device_info: デバイス情報
            output_file: 出力ファイルパス
        """
        try:
            # デバイストークンの生成（メタデータから取得）
            device_token = device_info.get('metadata', {}).get('device_token')
            if not device_token:
                print("警告: デバイストークンが見つかりません")
                device_token = f"device_{device_info['device_id']}_PLEASE_SET_TOKEN"

            config = {
                "device_id": device_info['device_id'],
                "server_url": self.server_url,
                "device_token": device_token,
                "collection_interval": 300,
                "collection_duration": 60,
                "base_duration": 180,
                "channel_width": "80MHz",
                "location": device_info.get('location', 'unknown'),
                "network_interface": "wlan0",
                "csi_port": 5500,
                "upload_timeout": 60,
                "health_check_interval": 3600,
                "delete_after_upload": False
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"設定ファイルを生成しました: {output_file}")

        except Exception as e:
            print(f"設定ファイル生成中にエラーが発生しました: {e}")


def main():
    parser = argparse.ArgumentParser(description="デバイス登録スクリプト")
    parser.add_argument("--server", type=str, default="http://192.168.101.168:8000", help="APIサーバーURL")
    parser.add_argument("--device-id", type=str, required=True, help="デバイスID")
    parser.add_argument("--device-name", type=str, help="デバイス名")
    parser.add_argument("--location", type=str, default="lab", help="設置場所")
    parser.add_argument("--config-output", type=str, default="config/device_config_v2.json", help="設定ファイル出力パス")
    parser.add_argument("--username", type=str, help="ユーザー名")

    args = parser.parse_args()

    # デバイス登録クラスの初期化
    registration = DeviceRegistration(args.server)

    # ユーザー認証
    username = args.username
    if not username:
        username = input("ユーザー名: ")

    password = getpass.getpass("パスワード: ")

    access_token = registration.login(username, password)
    if not access_token:
        print("認証に失敗しました")
        sys.exit(1)

    # デバイス情報の構築
    device_info = {
        "device_id": args.device_id,
        "device_name": args.device_name or args.device_id,
        "device_type": "raspberry_pi",
        "location": args.location,
        "description": f"CSI測定デバイス ({args.device_id})",
        "metadata": {
            "hardware_type": "Raspberry Pi",
            "software_version": "v2.0",
            "network_interface": "wlan0",
            "csi_port": 5500
        }
    }

    # デバイス登録
    print(f"デバイスを登録しています: {args.device_id}")
    result = registration.register_device(access_token, device_info)

    if not result:
        print("デバイス登録に失敗しました")
        sys.exit(1)

    # 詳細なデバイス情報を取得
    device_details = registration.get_device_info(access_token, args.device_id)
    if device_details:
        print(f"デバイス詳細情報:")
        print(f"  ID: {device_details.get('device_id')}")
        print(f"  名前: {device_details.get('device_name')}")
        print(f"  タイプ: {device_details.get('device_type')}")
        print(f"  場所: {device_details.get('location')}")
        print(f"  ステータス: {device_details.get('status')}")

        # 設定ファイルの生成
        registration.generate_config_file(device_details, args.config_output)

        print("\n✅ デバイス登録が完了しました!")
        print(f"設定ファイル: {args.config_output}")
        print("\n次のステップ:")
        print("1. 生成された設定ファイルを確認してください")
        print("2. デバイストークンが正しく設定されているか確認してください")
        print("3. main_improved.py を使用してCSIデータの収集を開始してください")
        print(f"   python3 main_improved.py --config {args.config_output} --mode test")

    else:
        print("デバイス情報の取得に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()