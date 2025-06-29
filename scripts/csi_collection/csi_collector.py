#!/usr/bin/env python3
"""
CSIデータ収集クラス（簡素化版）
tcpdumpを使用してCSIデータを収集し、PCAPファイルとして保存
"""

import os
import subprocess
import time
import logging
from typing import Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CSICollector:
    """CSIデータ収集クラス（簡素化版）"""
    
    def __init__(self, config: dict):
        """
        CSIコレクターの初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.interface = config['csi_collection']['interface']
        self.port = config['csi_collection']['port']
        
    def collect(self, duration: int, output_file: str) -> Tuple[bool, Optional[str]]:
        """
        CSIデータの収集
        
        Args:
            duration: 収集時間（秒）
            output_file: 出力ファイルパス
            
        Returns:
            (成功フラグ, エラーメッセージ)
        """
        try:
            logger.info(f"CSIデータの収集を開始: {duration}秒, 出力: {output_file}")
            
            # 出力ディレクトリの作成
            output_dir = os.path.dirname(output_file)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # tcpdumpコマンドの構築
            cmd = [
                'sudo', 'tcpdump',
                '-i', self.interface,
                '-w', output_file,
                '-G', str(duration),  # 指定時間で自動停止
                '-W', '1',  # 1ファイルのみ作成
                f'udp port {self.port}'  # 指定ポートのUDPパケットのみ
            ]
            
            logger.info(f"実行コマンド: {' '.join(cmd)}")
            
            # tcpdumpの実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # プロセスの完了を待機
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"tcpdump実行エラー: {stderr}"
                logger.error(error_msg)
                return False, error_msg
            
            # ファイルサイズの確認
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                error_msg = "PCAPファイルが作成されていないか、空です"
                logger.error(error_msg)
                return False, error_msg
            
            logger.info(f"CSIデータの収集が完了: {output_file} ({os.path.getsize(output_file)} bytes)")
            return True, None
            
        except Exception as e:
            error_msg = f"CSIデータ収集中にエラーが発生: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def collect_baseline(self, duration: int, output_dir: str) -> bool:
        """
        ベースラインCSIデータの収集
        
        Args:
            duration: 収集時間（秒）
            output_dir: 出力ディレクトリ
            
        Returns:
            成功フラグ
        """
        try:
            logger.info(f"ベースラインCSIデータの収集を開始: {duration}秒")
            
            # 出力ディレクトリの作成
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # ファイル名の生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"baseline_{timestamp}.pcap")
            
            # CSIデータの収集
            success, error_msg = self.collect(duration, output_file)
            
            if success:
                logger.info(f"ベースラインCSIデータの収集が完了: {output_file}")
                return True
            else:
                logger.error(f"ベースラインCSIデータの収集に失敗: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"ベースライン収集中にエラーが発生: {e}")
            return False
    
    def check_interface(self) -> bool:
        """
        ネットワークインターフェースの確認
        
        Returns:
            利用可能フラグ
        """
        try:
            cmd = ['ip', 'link', 'show', self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"インターフェース確認中にエラーが発生: {e}")
            return False
    
    def get_interface_status(self) -> dict:
        """
        ネットワークインターフェースの状態取得
        
        Returns:
            インターフェース情報
        """
        try:
            cmd = ['ip', 'link', 'show', self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'available': False, 'error': result.stderr}
            
            # インターフェース情報の解析
            lines = result.stdout.strip().split('\n')
            if not lines:
                return {'available': False, 'error': 'No interface information'}
            
            # 状態の確認
            status_line = lines[0]
            is_up = 'UP' in status_line
            
            return {
                'available': True,
                'interface': self.interface,
                'status': 'UP' if is_up else 'DOWN',
                'is_up': is_up
            }
            
        except Exception as e:
            logger.error(f"インターフェース状態取得中にエラーが発生: {e}")
            return {'available': False, 'error': str(e)} 