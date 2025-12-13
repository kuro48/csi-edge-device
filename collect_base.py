#!/usr/bin/env python3
"""
Base CSI Collection Script
ベースCSI（基準データ）の収集とアップロード
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

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


class BaseCSICollector:
    """ベースCSI収集・アップロードクラス"""

    def __init__(self, config_path: str = "config/device_config.json"):
        """初期化"""
        self.config = self._load_config(config_path)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        logger.info(f"Base CSI Collector initialized")
        logger.info(f"Server: {self.config['server_url']}")
        logger.info(f"Base Duration: {self.config.get('base_duration', 60)}s")

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

    def collect_base_csi(self) -> str:
        """ベースCSIデータ収集（人物がいない状態で実行）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"base_csi_{timestamp}.pcap"
        filepath = self.data_dir / filename

        interface = self.config.get('network_interface', 'wlan0')
        duration = self.config.get('base_duration', 60)  # デフォルト180秒
        port = self.config.get('csi_port', 5500)

        logger.info("=" * 60)
        logger.info("⚠️  IMPORTANT: Ensure NO PERSON is in the monitoring area")
        logger.info("=" * 60)
        logger.info(f"Starting BASE CSI collection: {duration}s on {interface}:{port}")
        logger.info(f"Collection will take approximately {duration / 60:.1f} minutes")
        logger.info("=" * 60)

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

            # 収集開始
            start_time = datetime.now()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # プログレス表示
            self._show_progress(duration)

            # 終了待ち
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"tcpdump error: {stderr}")
                return None

            if filepath.exists() and filepath.stat().st_size > 0:
                size = filepath.stat().st_size
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Base CSI data collected successfully")
                logger.info(f"   File: {filename}")
                logger.info(f"   Size: {size:,} bytes ({size / 1024 / 1024:.2f} MB)")
                logger.info(f"   Duration: {elapsed:.1f}s")
                return str(filepath)
            else:
                logger.error("❌ Base CSI data file not created or empty")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to collect base CSI data: {e}")
            return None

    def _show_progress(self, duration: int):
        """収集進捗表示"""
        logger.info("Collection in progress...")
        logger.info("(This process will run for the configured duration)")

        # 進捗表示用のカウントダウン（オプション）
        intervals = [25, 50, 75, 90, 100]
        for percent in intervals:
            wait_time = duration * percent / 100
            if percent < 100:
                logger.info(f"   {percent}% checkpoint will occur at {wait_time:.0f}s")

    def upload_base_csi(self, filepath: str) -> bool:
        """ベースCSIデータをサーバーにアップロード"""
        if not filepath or not Path(filepath).exists():
            logger.error("❌ Base CSI data file not found")
            return False

        try:
            server_url = self.config['server_url'].rstrip('/')
            endpoint = f"{server_url}/api/v2/base-csi/register"

            logger.info("=" * 60)
            logger.info(f"Uploading BASE CSI to {endpoint}...")
            logger.info("=" * 60)

            # ファイルアップロード（バックエンドのベースCSI登録APIに合わせる）
            with open(filepath, 'rb') as f:
                files = {
                    'file': (Path(filepath).name, f, 'application/vnd.tcpdump.pcap')
                }

                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=self.config.get('upload_timeout', 60),
                    verify=False  # SSL検証を無効化（開発環境用）
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Upload successful")
                    logger.info(f"   File: {Path(filepath).name}")
                    logger.info(f"   Base CSI ID: {result.get('id', 'N/A')}")
                    logger.info(f"   Name: {result.get('name', 'N/A')}")
                    return True
                else:
                    logger.error("❌ Upload failed")
                    logger.error(f"   Status: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to upload base CSI data: {e}")
            return False

    def run(self):
        """ベースCSI収集とアップロードを実行"""
        logger.info("=" * 60)
        logger.info("🎯 BASE CSI COLLECTION AND UPLOAD")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📋 Instructions:")
        logger.info("   1. Ensure NO PERSON is in the monitoring area")
        logger.info("   2. Keep the environment stable during collection")
        logger.info("   3. Do not move objects or change room configuration")
        logger.info("")
        logger.info("⏱️  Waiting 5 seconds before starting...")
        logger.info("   Press Ctrl+C to cancel if needed")
        logger.info("")

        try:
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("❌ Cancelled by user")
            return False

        # ベースCSIデータ収集
        filepath = self.collect_base_csi()

        if filepath:
            # サーバーにアップロード
            success = self.upload_base_csi(filepath)

            if success:
                logger.info("")
                logger.info("=" * 60)
                logger.info("✅ BASE CSI COLLECTION AND UPLOAD COMPLETED")
                logger.info("=" * 60)

                # 送信成功後、ローカルファイルを削除（オプション）
                if self.config.get('delete_after_upload', False):
                    Path(filepath).unlink()
                    logger.info(f"🗑️  Deleted local file: {filepath}")

                return True
            else:
                logger.error("")
                logger.error("=" * 60)
                logger.error("❌ UPLOAD FAILED - Base CSI file saved locally")
                logger.error(f"   Location: {filepath}")
                logger.error("=" * 60)
                return False
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error("❌ BASE CSI COLLECTION FAILED")
            logger.error("=" * 60)
            return False


def main():
    """メイン処理"""
    try:
        collector = BaseCSICollector()
        collector.run()

    except KeyboardInterrupt:
        logger.info("")
        logger.info("❌ Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
