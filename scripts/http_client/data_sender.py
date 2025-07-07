#!/usr/bin/env python3
"""
データ送信クラス（簡素化版）
PCAPファイルをサーバーにPOSTする機能のみ
"""

import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DataSender:
    """データ送信クラス（簡素化版）"""
    
    def __init__(self, config: dict):
        """
        データ送信クラスの初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.server_url = config['server']['url']
        self.api_key = config['server']['api_key']
        self.timeout = config['server']['timeout']
        self.retry_attempts = config['server']['retry_attempts']
        self.retry_delay = config['server']['retry_delay']
        
    def send_csi_data(self, pcap_file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        CSIデータ（PCAPファイル）の送信
        
        Args:
            pcap_file_path: PCAPファイルのパス
            metadata: メタデータ
            
        Returns:
            送信成功フラグ
        """
        try:
            logger.info(f"CSIデータの送信を開始: {pcap_file_path}")
            
            # ファイルの存在確認
            if not os.path.exists(pcap_file_path):
                logger.error(f"PCAPファイルが存在しません: {pcap_file_path}")
                return False
            
            # ファイルサイズの確認
            file_size = os.path.getsize(pcap_file_path)
            if file_size == 0:
                logger.error(f"PCAPファイルが空です: {pcap_file_path}")
                return False
            
            logger.info(f"ファイルサイズ: {file_size} bytes")
            
            # ファイルの送信
            return self._send_file_with_retry(
                pcap_file_path, 
                metadata, 
                '/breathing-analysis/upload-csi'
            )
            
        except Exception as e:
            logger.error(f"CSIデータ送信中にエラーが発生: {e}")
            return False
    
    def send_baseline_data(self, baseline_dir: str) -> bool:
        """
        ベースラインデータの送信
        
        Args:
            baseline_dir: ベースラインデータのディレクトリ
            
        Returns:
            送信成功フラグ
        """
        try:
            logger.info(f"ベースラインデータの送信を開始: {baseline_dir}")
            
            if not os.path.exists(baseline_dir):
                logger.error(f"ベースラインディレクトリが存在しません: {baseline_dir}")
                return False
            
            # ベースラインファイルの検索
            baseline_files = [f for f in os.listdir(baseline_dir) 
                            if f.startswith('baseline_') and f.endswith('.pcap')]
            
            if not baseline_files:
                logger.warning(f"ベースラインファイルが見つかりません: {baseline_dir}")
                return False
            
            # 最新のベースラインファイルを送信
            latest_file = sorted(baseline_files)[-1]
            file_path = os.path.join(baseline_dir, latest_file)
            
            metadata = {
                'type': 'baseline',
                'timestamp': int(time.time()),
                'device_id': self.config['device']['id'],
                'location': self.config['device']['location'],
                'channel_width': self.config['csi_collection']['channel_width']
            }
            
            return self._send_file_with_retry(
                file_path, 
                metadata, 
                '/breathing-analysis/upload-csi'
            )
            
        except Exception as e:
            logger.error(f"ベースラインデータ送信中にエラーが発生: {e}")
            return False
    
    def _send_file_with_retry(self, file_path: str, metadata: Dict[str, Any], endpoint: str) -> bool:
        """
        ファイル送信（リトライ機能付き）
        
        Args:
            file_path: 送信ファイルのパス
            metadata: メタデータ
            endpoint: APIエンドポイント
            
        Returns:
            送信成功フラグ
        """
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"送信試行 {attempt + 1}/{self.retry_attempts}")
                
                # ファイルの準備
                with open(file_path, 'rb') as f:
                    files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                    data = {'metadata': json.dumps(metadata)}
                    headers = {'X-API-Key': self.api_key}
                
                # リクエストの送信
                url = f"{self.server_url}{endpoint}"
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"ファイル送信が成功しました: {result.get('message', 'Success')}")
                    return True
                else:
                    logger.warning(f"送信失敗 (HTTP {response.status_code}): {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"送信タイムアウト (試行 {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"接続エラー (試行 {attempt + 1})")
            except Exception as e:
                logger.error(f"送信中にエラーが発生 (試行 {attempt + 1}): {e}")
            
            # リトライ前の待機
            if attempt < self.retry_attempts - 1:
                logger.info(f"{self.retry_delay}秒後にリトライします...")
                time.sleep(self.retry_delay)
        
        logger.error(f"ファイル送信が失敗しました: {file_path}")
        return False
    
    def check_server_status(self) -> bool:
        """
        サーバーの状態確認
        
        Returns:
            接続可能フラグ
        """
        try:
            url = f"{self.server_url}/breathing-analysis/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                logger.info("サーバーに正常に接続できました")
                return True
            else:
                logger.warning(f"サーバー応答エラー: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("サーバー接続がタイムアウトしました")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("サーバーに接続できません")
            return False
        except Exception as e:
            logger.error(f"サーバー状態確認中にエラーが発生: {e}")
            return False 