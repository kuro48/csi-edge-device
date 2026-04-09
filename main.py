#!/usr/bin/env python3
"""
CSI Edge Device - Simplified Version
シンプルなCSIデータ収集とアップロード
"""

import argparse
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import urllib3

# SSL警告を抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

        logger.info("CSI Collector initialized")
        logger.info(f"Server: {self.config['server_url']}")
        logger.info(f"Device ID: {self.config['device_id']}")

    def _load_config(self, config_path: str) -> dict:
        """設定ファイル読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Config loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _request_kwargs(self, timeout: Optional[int] = None) -> Dict[str, Any]:
        """HTTPリクエスト共通設定"""
        return {
            'timeout': timeout or self.config.get('upload_timeout', 60),
            'verify': False,
        }

    def _build_metadata(self) -> Dict[str, Any]:
        """アップロード用メタデータ作成"""
        metadata = {
            'type': 'csi_measurement',
            'device_id': self.config.get('device_id'),
            'channel_width': self.config.get('channel_width'),
            'location': self.config.get('location'),
            'network_interface': self.config.get('network_interface'),
            'csi_port': self.config.get('csi_port'),
        }
        return {k: v for k, v in metadata.items() if v is not None}

    def _delete_local_file(self, filepath: str) -> None:
        """送信成功後にローカルPCAPを削除"""
        try:
            Path(filepath).unlink(missing_ok=True)
            logger.info(f"Deleted local file: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to delete local file {filepath}: {e}")

    def collect_csi_data(self) -> Optional[str]:
        """CSIデータ収集（tcpdump使用）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"csi_data_{timestamp}.pcap"
        filepath = self.data_dir / filename

        interface = self.config.get('network_interface', 'wlan0')
        duration = self.config.get('collection_duration', 60)
        port = self.config.get('csi_port', 5500)

        logger.info(f"Starting CSI collection: {duration}s on {interface}:{port}")

        try:
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

            logger.error("CSI data file not created or empty")
            return None

        except Exception as e:
            logger.error(f"Failed to collect CSI data: {e}")
            return None

    def upload_csi_data(self, filepath: str) -> Optional[Dict[str, Any]]:
        """CSIデータをサーバーにアップロード"""
        if not filepath or not Path(filepath).exists():
            logger.error("CSI data file not found")
            return None

        try:
            server_url = self.config['server_url'].rstrip('/')
            endpoint = f"{server_url}/api/v2/csi-data/upload"

            with open(filepath, 'rb') as f:
                files = {
                    'file': (Path(filepath).name, f, 'application/vnd.tcpdump.pcap')
                }
                data = {
                    'collection_start_time': datetime.now().isoformat(),
                    'collection_duration': self.config.get('collection_duration', 60),
                    'metadata': json.dumps(self._build_metadata())
                }

                logger.info(f"Uploading to {endpoint}...")
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    **self._request_kwargs()
                )

            if response.status_code != 200:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return None

            result = response.json()
            csi_data_id = result.get('id')
            upload_status = result.get('status', 'unknown')
            logger.info(f"Upload successful: {Path(filepath).name}")
            logger.info(f"CSI data ID: {csi_data_id or 'N/A'}")
            logger.info(f"Upload status: {upload_status}")
            logger.info("Server-side analysis has started in the background")
            return result

        except Exception as e:
            logger.error(f"Failed to upload CSI data: {e}")
            return None

    def test_connection(self) -> bool:
        """サーバーのヘルスチェック"""
        try:
            server_url = self.config['server_url'].rstrip('/')
            endpoint = f"{server_url}/api/v2/health"
            response = requests.get(endpoint, **self._request_kwargs(timeout=10))
            if response.status_code == 200:
                logger.info("Server health check OK")
                return True
            logger.error(f"Health check failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def run_schedule(self) -> None:
        """定期収集モードで実行"""
        interval = self.config.get('collection_interval', 300)
        logger.info(f"Schedule mode started: interval={interval}s")
        while True:
            self.run()
            time.sleep(interval)

    def run(self) -> bool:
        """CSI収集とアップロードを実行"""
        logger.info("=" * 50)
        logger.info("Starting CSI collection and upload")
        logger.info("=" * 50)

        filepath = self.collect_csi_data()

        if not filepath:
            logger.error("CSI collection failed")
            return False

        result = self.upload_csi_data(filepath)
        if not result:
            logger.error("Upload failed")
            return False

        logger.info("CSI collection and upload completed successfully")
        self._delete_local_file(filepath)

        return True


def main():
    """メイン処理"""
    try:
        parser = argparse.ArgumentParser(description="CSI Edge Device Collector")
        parser.add_argument("--config", type=str, default="config/device_config.json", help="設定ファイルのパス")
        parser.add_argument("--mode", type=str, default="collect", choices=["collect", "schedule", "test"], help="実行モード")
        args = parser.parse_args()

        collector = SimpleCSICollector(config_path=args.config)

        if args.mode == "test":
            ok = collector.test_connection()
            raise SystemExit(0 if ok else 1)
        if args.mode == "schedule":
            collector.run_schedule()
        else:
            collector.run()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
