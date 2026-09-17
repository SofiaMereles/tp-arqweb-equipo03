#!/bin/bash
echo "=== Captura de tráfico tcpdump ==="
sudo tcpdump -i any -w /tmp/transaccion_tp3.pcap "port 443 or port 80"
