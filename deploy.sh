#!/bin/bash

# CSI Edge Device Deployment Script
# Usage: ./deploy.sh [raspberry_pi_ip]

if [ $# -eq 0 ]; then
    echo "Usage: ./deploy.sh [raspberry_pi_ip]"
    echo "Example: ./deploy.sh 192.168.1.100"
    exit 1
fi

PI_IP=$1
PI_USER="pi"
REMOTE_DIR="/home/pi/csi-edge-device"

echo "=== Deploying CSI Edge Device to $PI_IP ==="

# リモートディレクトリの作成
echo "Creating remote directory..."
ssh $PI_USER@$PI_IP "mkdir -p $REMOTE_DIR"

# ファイルの転送
echo "Transferring files..."
scp -r . $PI_USER@$PI_IP:$REMOTE_DIR/

# リモートでのセットアップ実行
echo "Running setup on Raspberry Pi..."
ssh $PI_USER@$PI_IP "cd $REMOTE_DIR && chmod +x setup.sh && ./setup.sh"

# systemdサービスの設定
echo "Setting up systemd service..."
ssh $PI_USER@$PI_IP "sudo cp $REMOTE_DIR/systemd/csi-edge-device.service /etc/systemd/system/"
ssh $PI_USER@$PI_IP "sudo systemctl daemon-reload"
ssh $PI_USER@$PI_IP "sudo systemctl enable csi-edge-device.service"

echo "=== Deployment Complete ==="
echo "To start the service:"
echo "ssh $PI_USER@$PI_IP 'sudo systemctl start csi-edge-device.service'"
echo ""
echo "To check status:"
echo "ssh $PI_USER@$PI_IP 'sudo systemctl status csi-edge-device.service'"
echo ""
echo "To view logs:"
echo "ssh $PI_USER@$PI_IP 'sudo journalctl -u csi-edge-device.service -f'" 