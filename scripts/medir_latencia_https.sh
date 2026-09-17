#!/bin/bash
echo "=== Mediciones de rendimiento sobre https://bookstack.local ==="
for i in {1..10}; do
  echo -n "Medicion $i: "
  curl -k -s -w "DNS: %{time_namelookup}s | Connect: %{time_connect}s | TLS: %{time_appconnect}s | Total: %{time_total}s\n" -o /dev/null https://bookstack.local
done
