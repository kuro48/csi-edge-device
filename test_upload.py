#!/usr/bin/env python3
"""
既存のpcapファイルをアップロードするテストスクリプト
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import requests


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="CSIデータアップロードテスト")
    parser.add_argument("--config", type=str, default="config/device_config.json", help="設定ファイルのパス")
    parser.add_argument("--file", type=str, required=True, help="アップロードするpcapファイルのパス")
    args = parser.parse_args()

    config = load_config(args.config)
    file_path = Path(args.file)

    if not file_path.exists():
        raise SystemExit(f"ファイルが見つかりません: {file_path}")

    server_url = config["server_url"].rstrip("/")
    endpoint = f"{server_url}/api/v2/csi-data/upload"

    metadata = {
        "type": "csi_measurement",
        "device_id": config.get("device_id"),
        "channel_width": config.get("channel_width"),
        "location": config.get("location"),
        "network_interface": config.get("network_interface"),
        "csi_port": config.get("csi_port")
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, "application/vnd.tcpdump.pcap")
        }
        data = {
            "collection_start_time": datetime.now().isoformat(),
            "collection_duration": config.get("collection_duration", 60),
            "metadata": json.dumps(metadata)
        }

        response = requests.post(endpoint, files=files, data=data, timeout=60, verify=False)

    if response.status_code != 200:
        raise SystemExit(f"アップロードに失敗しました: {response.status_code} {response.text}")

    result = response.json()
    print("✅ アップロード成功")
    print(f"  id: {result.get('id', 'N/A')}")


if __name__ == "__main__":
    main()
