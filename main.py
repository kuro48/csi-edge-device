#!/usr/bin/env python3
"""
エッジデバイス（Raspberry Pi）メインスクリプト（最小限版）
tcpdumpでCSIを取得 → PCAPファイルをPOSTするだけの機能
"""

import json
import os
import sys
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Any
import schedule

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.csi_collection.csi_collector import CSICollector
from scripts.http_client.data_sender import DataSender

class EdgeDeviceManager:
    """エッジデバイス管理クラス（最小限版）"""
    
    def __init__(self, config_path: str):
        """
        エッジデバイスマネージャーの初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        
        # コンポーネントの初期化
        self.csi_collector = CSICollector(self.config)
        self.data_sender = DataSender(self.config)
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
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
        log_dir = self.config['storage']['logs_dir']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'edge_device_{timestamp}.log')
        
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Edge Device Manager initialized (minimal version)")
        
    def _setup_directories(self):
        """必要なディレクトリの作成"""
        storage_config = self.config['storage']
        directories = [
            storage_config['base_dir'],
            storage_config['raw_csi_dir'],
            storage_config['baseline_dir'],
            storage_config['logs_dir']
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"ディレクトリを作成しました: {directory}")
                
    def collect_and_send_csi(self) -> bool:
        """
        CSIデータの収集と送信（最小限版）
        
        Returns:
            成功フラグ
        """
        try:
            self.logger.info("CSIデータの収集と送信を開始します")
            
            # ネットワークインターフェースの確認
            if not self.csi_collector.check_interface():
                self.logger.error("ネットワークインターフェースが利用できません")
                return False
            
            # CSIデータの収集
            raw_csi_dir = self.config['storage']['raw_csi_dir']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(raw_csi_dir, f"csi_data_{timestamp}.pcap")
            
            window_size = self.config['csi_collection']['window_size']
            success, error_msg = self.csi_collector.collect(window_size, output_file)
            
            if not success:
                self.logger.error(f"CSIデータの収集に失敗しました: {error_msg}")
                return False
                
            self.logger.info("CSIデータの収集が完了しました")
            
            # サーバーへの送信
            metadata = {
                'type': 'csi_measurement',
                'timestamp': int(time.time()),
                'device_id': self.config['device']['id'],
                'collection_duration': window_size,
                'channel_width': self.config['csi_collection']['channel_width'],
                'location': self.config['device']['location']
            }
            
            if self.data_sender.send_csi_data(output_file, metadata):
                self.logger.info("CSIデータの送信が完了しました")
                return True
            else:
                self.logger.error("CSIデータの送信に失敗しました")
                return False
                
        except Exception as e:
            self.logger.error(f"CSIデータ収集・送信中にエラーが発生: {e}")
            return False
            
    def collect_baseline(self) -> bool:
        """
        ベースラインCSIデータの収集と送信
        
        Returns:
            成功フラグ
        """
        try:
            self.logger.info("ベースラインCSIデータの収集を開始します")
            
            baseline_dir = self.config['storage']['baseline_dir']
            duration = self.config['csi_collection']['baseline_duration']
            
            success = self.csi_collector.collect_baseline(duration, baseline_dir)
            
            if success:
                self.logger.info("ベースラインCSIデータの収集が完了しました")
                # サーバーに送信
                if self.data_sender.send_baseline_data(baseline_dir):
                    self.logger.info("ベースラインデータの送信が完了しました")
                else:
                    self.logger.warning("ベースラインデータの送信に失敗しました")
                return True
            else:
                self.logger.error("ベースラインCSIデータの収集に失敗しました")
                return False
                
        except Exception as e:
            self.logger.error(f"ベースライン収集中にエラーが発生: {e}")
            return False
            
    def run_scheduled_tasks(self):
        """スケジュールされたタスクの実行"""
        try:
            # ベースライン収集のスケジュール（1日1回）
            schedule.every().day.at("02:00").do(self.collect_baseline)
            
            # CSIデータ収集のスケジュール（設定された間隔で）
            collection_interval = self.config['schedule']['data_collection_interval']
            schedule.every(collection_interval).seconds.do(self.collect_and_send_csi)
            
            self.logger.info("スケジュールされたタスクを開始しました")
            self.logger.info(f"CSIデータ収集間隔: {collection_interval}秒")
            
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("スケジュールされたタスクを停止しました")
        except Exception as e:
            self.logger.error(f"スケジュールタスク実行中にエラーが発生: {e}")
            
    def check_server_connection(self) -> bool:
        """サーバー接続の確認"""
        return self.data_sender.check_server_status()

def main():
    parser = argparse.ArgumentParser(description="エッジデバイスメインスクリプト（最小限版）")
    parser.add_argument("--config", type=str, default="config/device_config.json",
                      help="設定ファイルのパス")
    parser.add_argument("--mode", type=str, choices=["baseline", "collect", "schedule"],
                      default="schedule", help="実行モード")
    
    args = parser.parse_args()
    
    # エッジデバイスマネージャーの初期化
    manager = EdgeDeviceManager(args.config)
    
    # サーバー接続の確認
    if not manager.check_server_connection():
        manager.logger.warning("サーバーに接続できません。オフライン動作を継続します。")
    
    # モードに応じた実行
    if args.mode == "baseline":
        manager.collect_baseline()
    elif args.mode == "collect":
        manager.collect_and_send_csi()
    elif args.mode == "schedule":
        manager.run_scheduled_tasks()

if __name__ == "__main__":
    main() 