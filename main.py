#!/usr/bin/env python3
"""
CSI Edge Device - Simplified Version
シンプルなCSIデータ収集とアップロード
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

import requests

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleCSICollector:
    """シンプルなCSIデータ収集・アップロードクラス"""

    def __init__(self, config_path: str = "config/device_config.json"):
        """初期化"""
        self.config = self._load_config(config_path)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        logger.info(f"CSI Collector initialized")
        logger.info(f"Server: {self.config['server_url']}")
        logger.info(f"Device ID: {self.config['device_id']}")

    def _load_config(self, config_path: str) -> dict:
        """設定ファイル読み込み"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Config loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def collect_csi_data(self) -> str:
        """CSIデータ収集（tcpdump使用）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"csi_data_{timestamp}.pcap"
        filepath = self.data_dir / filename

        interface = self.config.get('network_interface', 'wlan0')
        duration = self.config.get('collection_duration', 60)
        port = self.config.get('csi_port', 5500)

        logger.info(f"Starting CSI collection: {duration}s on {interface}:{port}")

        try:
            # tcpdumpコマンド実行
            cmd = [
                'sudo', 'tcpdump',
                '-i', interface,
                '-w', str(filepath),
                '-G', str(duration),
                '-W', '1',
                f'udp port {port}'
            ]

            logger.info(f"Command: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"tcpdump error: {stderr}")
                return None

            if filepath.exists() and filepath.stat().st_size > 0:
                size = filepath.stat().st_size
                logger.info(f"CSI data collected: {filename} ({size} bytes)")
                return str(filepath)
            else:
                logger.error("CSI data file not created or empty")
                return None

        except Exception as e:
            logger.error(f"Failed to collect CSI data: {e}")
            return None

    def upload_csi_data(self, filepath: str) -> bool:
        """CSIデータをサーバーにアップロード"""
        if not filepath or not Path(filepath).exists():
            logger.error("CSI data file not found")
            return False

        try:
            server_url = self.config['server_url']
            device_id = self.config['device_id']
            endpoint = f"{server_url}/api/v2/csi-data/upload"

            # ファイルアップロード
            with open(filepath, 'rb') as f:
                files = {
                    'file': (Path(filepath).name, f, 'application/vnd.tcpdump.pcap')
                }
                data = {
                    'device_id': device_id,
                    'collection_start_time': datetime.now().isoformat(),
                    'collection_duration': self.config.get('collection_duration', 60)
                }

                logger.info(f"Uploading to {endpoint}...")
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Upload successful: {Path(filepath).name}")
                    logger.info(f"Response: {result.get('id', 'Success')}")
                    return True
                else:
                    logger.error(f"Upload failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to upload CSI data: {e}")
            return False

    def run(self):
        """CSI収集とアップロードを実行"""
        logger.info("=" * 50)
        logger.info("Starting CSI collection and upload")
        logger.info("=" * 50)

        # CSIデータ収集
        filepath = self.collect_csi_data()

        if filepath:
            # サーバーにアップロード
            success = self.upload_csi_data(filepath)

            if success:
                logger.info("CSI collection and upload completed successfully")

                # 送信成功後、ローカルファイルを削除（オプション）
                if self.config.get('delete_after_upload', False):
                    Path(filepath).unlink()
                    logger.info(f"Deleted local file: {filepath}")

                return True
            else:
                logger.error("Upload failed")
                return False
        else:
            logger.error("CSI collection failed")
            return False


def main():
    """メイン処理"""
    try:
        collector = SimpleCSICollector()
        collector.run()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
