#!/usr/bin/env python3
"""
エッジデバイス（Raspberry Pi）メインスクリプト（簡素化版）
tcpdumpでCSIを取得 → PCAPファイルをPOSTするだけの機能
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

logger = logging.getLogger(__name__)

class EdgeDeviceManager:
    """エッジデバイス管理クラス（簡素化版）"""
    
    def __init__(self, config_path: str):
        """
        エッジデバイスマネージャーの初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        
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
        self.logger.info("Edge Device Manager initialized (simplified version)")
        
    def _setup_directories(self):
        """必要なディレクトリの作成"""
        directories = ["data", "logs"]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"ディレクトリを作成しました: {directory}")
                
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
            
            # tcpdumpでCSIデータを収集（60秒間）
            success = self._collect_csi_data(output_file, 60)
            
            if not success:
                self.logger.error("CSIデータの収集に失敗しました")
                return False
                
            self.logger.info("CSIデータの収集が完了しました")
            
            # サーバーへの送信
            success = self._send_csi_data(output_file, "csi_measurement")
            
            if success:
                self.logger.info("CSIデータの送信が完了しました")
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
            cmd = [
                'sudo', 'tcpdump',
                '-i', 'wlan0',
                '-w', output_file,
                '-G', str(duration),
                '-W', '1',
                'udp port 5500'
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
            
            self.logger.info(f"CSIデータの収集が完了: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSIデータ収集中にエラーが発生: {e}")
            return False
    
    def _send_csi_data(self, pcap_file_path: str, data_type: str = "csi_measurement") -> bool:
        """
        CSIデータをサーバーに送信
        
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
            
            # メタデータの作成
            metadata = {
                'type': data_type,
                'device_id': self.config['device_id'],
                'timestamp': int(time.time()),
                'collection_duration': 60 if data_type == "csi_measurement" else self.config.get('base_duration', 180),
                'channel_width': self.config.get('channel_width', '80MHz'),
                'location': self.config.get('location', 'unknown')
            }
            
            # ファイルの送信
            with open(pcap_file_path, 'rb') as f:
                files = {'file': (os.path.basename(pcap_file_path), f, 'application/octet-stream')}
                data = {'metadata': json.dumps(metadata)}
                headers = {'Authorization': f"Bearer {self.config['api_key']}"}
                
                response = requests.post(
                    f"{self.config['server_url']}/breathing-analysis/upload-csi",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"ファイル送信が成功しました: {result.get('message', 'Success')}")
                if result.get('ipfs_hash'):
                    self.logger.info(f"IPFSハッシュ: {result['ipfs_hash']}")
                return True
            else:
                self.logger.warning(f"送信失敗 (HTTP {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"CSIデータ送信中にエラーが発生: {e}")
            return False
            
    def run_scheduled_tasks(self):
        """スケジュールされたタスクの実行（通常データのみ）"""
        try:
            # CSIデータ収集のスケジュール（ベースは含まない）
            collection_interval = self.config['collection_interval']
            schedule.every(collection_interval).seconds.do(self.collect_and_send_csi)
            
            self.logger.info("スケジュールされたタスクを開始しました")
            self.logger.info(f"CSIデータ収集間隔: {collection_interval}秒")
            self.logger.info("ベース収集は手動実行してください")
            
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("スケジュールされたタスクを停止しました")
        except Exception as e:
            self.logger.error(f"スケジュールタスク実行中にエラーが発生: {e}")

def main():
    parser = argparse.ArgumentParser(description="エッジデバイスメインスクリプト")
    parser.add_argument("--config", type=str, default="config/device_config.json", help="設定ファイルのパス")
    parser.add_argument("--mode", type=str, choices=["collect", "base", "schedule"], default="schedule", help="実行モード")
    
    args = parser.parse_args()
    
    # エッジデバイスマネージャーの初期化
    manager = EdgeDeviceManager(args.config)
    
    # モードに応じた実行
    if args.mode == "collect":
        manager.collect_and_send_csi()
    elif args.mode == "base":
        manager.collect_base()
    elif args.mode == "schedule":
        manager.run_scheduled_tasks()

if __name__ == "__main__":
    main()