#!/usr/bin/env python3
"""
エッジデバイス（Raspberry Pi）メインスクリプト（改良版）
現在のAPIサーバー（v2）に対応
- デバイス専用トークン認証
- 改良されたメタデータ形式
- エラーハンドリングの強化
"""

import json
import os
import sys
import time
import argparse
import logging
from datetime import datetime
import schedule
import subprocess
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EdgeDeviceManager:
    """エッジデバイス管理クラス（APIサーバーv2対応版）"""

    def __init__(self, config_path: str):
        """
        エッジデバイスマネージャーの初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self._validate_config()

    def _load_config(self, config_path: str) -> dict:
        """設定ファイルの読み込み"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """ロギングの設定"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'edge_device_{timestamp}.log')

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Edge Device Manager initialized (API v2 compatible)")

    def _setup_directories(self):
        """必要なディレクトリの作成"""
        directories = ["data", "logs"]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"ディレクトリを作成しました: {directory}")

    def _validate_config(self):
        """設定ファイルの検証"""
        required_fields = ['device_id', 'server_url', 'device_token']

        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"必須設定項目が不足しています: {field}")

        # デバイストークンの形式チェック
        if not self.config['device_token'].startswith('device_'):
            raise ValueError("デバイストークンの形式が正しくありません")

        self.logger.info("設定ファイルの検証が完了しました")

    def collect_and_send_csi(self) -> bool:
        """
        CSIデータの収集と送信（通常データ）

        Returns:
            成功フラグ
        """
        try:
            self.logger.info("CSIデータの収集と送信を開始します")

            # CSIデータの収集
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/csi_data_{timestamp}.pcap"

            # tcpdumpでCSIデータを収集（設定可能な時間）
            collection_duration = self.config.get('collection_duration', 60)
            success = self._collect_csi_data(output_file, collection_duration)

            if not success:
                self.logger.error("CSIデータの収集に失敗しました")
                return False

            self.logger.info("CSIデータの収集が完了しました")

            # サーバーへの送信
            success = self._send_csi_data(output_file, "csi_measurement")

            if success:
                self.logger.info("CSIデータの送信が完了しました")
                # 送信成功後、ローカルファイルを削除（オプション）
                if self.config.get('delete_after_upload', False):
                    os.remove(output_file)
                    self.logger.info(f"送信済みファイルを削除しました: {output_file}")
                return True
            else:
                self.logger.error("CSIデータの送信に失敗しました")
                return False

        except Exception as e:
            self.logger.error(f"CSIデータ収集・送信中にエラーが発生: {e}")
            return False

    def collect_base(self) -> bool:
        """
        ベースCSIデータの収集と送信（手動実行）

        Returns:
            成功フラグ
        """
        try:
            self.logger.info("ベースCSIデータの収集を開始します")

            # ベースCSIデータの収集
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/base_{timestamp}.pcap"

            # 設定された時間でベースを収集
            base_duration = self.config.get('base_duration', 180)
            success = self._collect_csi_data(output_file, base_duration)

            if not success:
                self.logger.error("ベースCSIデータの収集に失敗しました")
                return False

            self.logger.info("ベースCSIデータの収集が完了しました")

            # サーバーへの送信
            success = self._send_csi_data(output_file, "base")

            if success:
                self.logger.info("ベースデータの送信が完了しました")
                # 送信成功後、ローカルファイルを削除（オプション）
                if self.config.get('delete_after_upload', False):
                    os.remove(output_file)
                    self.logger.info(f"送信済みファイルを削除しました: {output_file}")
                return True
            else:
                self.logger.error("ベースデータの送信に失敗しました")
                return False

        except Exception as e:
            self.logger.error(f"ベース収集中にエラーが発生: {e}")
            return False

    def _collect_csi_data(self, output_file: str, duration: int) -> bool:
        """
        tcpdumpでCSIデータを収集

        Args:
            output_file: 出力ファイルパス
            duration: 収集時間（秒）

        Returns:
            成功フラグ
        """
        try:
            # 出力ディレクトリの作成
            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # tcpdumpコマンドの実行
            interface = self.config.get('network_interface', 'wlan0')
            port = self.config.get('csi_port', 5500)

            cmd = [
                'sudo', 'tcpdump',
                '-i', interface,
                '-w', output_file,
                '-G', str(duration),
                '-W', '1',
                f'udp port {port}'
            ]

            self.logger.info(f"実行コマンド: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                self.logger.error(f"tcpdump実行エラー: {stderr}")
                return False

            # ファイルサイズの確認
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                self.logger.error("PCAPファイルが作成されていないか、空です")
                return False

            file_size = os.path.getsize(output_file)
            self.logger.info(f"CSIデータの収集が完了: {output_file} ({file_size} bytes)")
            return True

        except Exception as e:
            self.logger.error(f"CSIデータ収集中にエラーが発生: {e}")
            return False

    def _send_csi_data(self, pcap_file_path: str, data_type: str = "csi_measurement") -> bool:
        """
        CSIデータをサーバーに送信（APIサーバーv2対応）

        Args:
            pcap_file_path: PCAPファイルのパス
            data_type: データタイプ（"csi_measurement" または "base"）

        Returns:
            送信成功フラグ
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(pcap_file_path):
                self.logger.error(f"PCAPファイルが存在しません: {pcap_file_path}")
                return False

            file_size = os.path.getsize(pcap_file_path)

            # 収集時間の決定
            if data_type == "base":
                collection_duration = self.config.get('base_duration', 180)
            else:
                collection_duration = self.config.get('collection_duration', 60)

            # メタデータの作成（APIサーバーv2形式）
            collection_start_time = datetime.now()
            metadata = {
                'type': data_type,
                'timestamp': int(time.time()),
                'collection_duration': collection_duration,
                'channel_width': self.config.get('channel_width', '80MHz'),
                'location': self.config.get('location', 'unknown'),
                'network_interface': self.config.get('network_interface', 'wlan0'),
                'csi_port': self.config.get('csi_port', 5500),
                'file_size': file_size
            }

            # リクエストの準備
            url = f"{self.config['server_url']}/api/v2/csi-data/upload"

            # ファイルの送信
            with open(pcap_file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(pcap_file_path), f, 'application/octet-stream')
                }
                data = {
                    'device_id': self.config['device_id'],
                    'collection_start_time': collection_start_time.isoformat(),
                    'collection_duration': collection_duration,
                    'metadata': json.dumps(metadata)
                }

                self.logger.info(f"ファイル送信開始: {url}")

                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    timeout=self.config.get('upload_timeout', 60)
                )

            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"ファイル送信が成功しました: {result.get('id', 'Success')}")

                # 追加情報のログ出力
                if 'ipfs_hash' in result:
                    self.logger.info(f"IPFSハッシュ: {result['ipfs_hash']}")
                if 'status' in result:
                    self.logger.info(f"処理ステータス: {result['status']}")

                return True
            else:
                self.logger.warning(f"送信失敗 (HTTP {response.status_code}): {response.text}")
                return False

        except requests.exceptions.Timeout:
            self.logger.error("ファイル送信がタイムアウトしました")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error("サーバーへの接続に失敗しました")
            return False
        except Exception as e:
            self.logger.error(f"CSIデータ送信中にエラーが発生: {e}")
            return False

    def test_connection(self) -> bool:
        """
        サーバーへの接続テスト

        Returns:
            接続成功フラグ
        """
        try:
            url = f"{self.config['server_url']}/health"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                self.logger.info("サーバー接続テストが成功しました")
                return True
            else:
                self.logger.warning(f"サーバー接続テストが失敗しました (HTTP {response.status_code})")
                return False

        except Exception as e:
            self.logger.error(f"サーバー接続テスト中にエラーが発生: {e}")
            return False

    def get_device_status(self) -> Optional[Dict[str, Any]]:
        """
        デバイスの状態取得

        Returns:
            デバイス状態情報
        """
        try:
            url = f"{self.config['server_url']}/api/v2/devices/{self.config['device_id']}"
            headers = {
                'Authorization': f"Bearer {self.config['device_token']}"
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                device_info = response.json()
                self.logger.info("デバイス状態の取得が成功しました")
                return device_info
            else:
                self.logger.warning(f"デバイス状態取得が失敗しました (HTTP {response.status_code})")
                return None

        except Exception as e:
            self.logger.error(f"デバイス状態取得中にエラーが発生: {e}")
            return None

    def run_scheduled_tasks(self):
        """スケジュールされたタスクの実行（通常データのみ）"""
        try:
            # 接続テスト
            if not self.test_connection():
                self.logger.error("サーバーに接続できません。終了します。")
                return

            # CSIデータ収集のスケジュール（ベースは含まない）
            collection_interval = self.config.get('collection_interval', 300)
            schedule.every(collection_interval).seconds.do(self.collect_and_send_csi)

            # 定期的な接続チェック（オプション）
            health_check_interval = self.config.get('health_check_interval', 3600)  # 1時間
            schedule.every(health_check_interval).seconds.do(self.test_connection)

            self.logger.info("スケジュールされたタスクを開始しました")
            self.logger.info(f"CSIデータ収集間隔: {collection_interval}秒")
            self.logger.info(f"ヘルスチェック間隔: {health_check_interval}秒")
            self.logger.info("ベース収集は手動実行してください")

            while True:
                schedule.run_pending()
                time.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("スケジュールされたタスクを停止しました")
        except Exception as e:
            self.logger.error(f"スケジュールタスク実行中にエラーが発生: {e}")


def main():
    parser = argparse.ArgumentParser(description="エッジデバイスメインスクリプト（APIサーバーv2対応）")
    parser.add_argument("--config", type=str, default="config/device_config_v2.json", help="設定ファイルのパス")
    parser.add_argument("--mode", type=str, choices=["collect", "base", "schedule", "test"], default="schedule", help="実行モード")

    args = parser.parse_args()

    # エッジデバイスマネージャーの初期化
    try:
        manager = EdgeDeviceManager(args.config)
    except Exception as e:
        print(f"初期化に失敗しました: {e}")
        sys.exit(1)

    # モードに応じた実行
    if args.mode == "collect":
        success = manager.collect_and_send_csi()
        sys.exit(0 if success else 1)
    elif args.mode == "base":
        success = manager.collect_base()
        sys.exit(0 if success else 1)
    elif args.mode == "test":
        success = manager.test_connection()
        if success:
            device_status = manager.get_device_status()
            if device_status:
                print(f"デバイス状態: {json.dumps(device_status, indent=2, ensure_ascii=False)}")
        sys.exit(0 if success else 1)
    elif args.mode == "schedule":
        manager.run_scheduled_tasks()


if __name__ == "__main__":
    main()