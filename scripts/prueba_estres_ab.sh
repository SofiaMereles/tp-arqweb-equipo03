#!/bin/bash
echo "=== Prueba de carga con Apache Benchmark (ab) ==="
ab -n 1000 -c 10 -f TLS1.3 https://127.0.0.1/login
