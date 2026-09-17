# Proyecto Integrador ARQ-WEB 2026 - Equipo 03

Despliegue, conectividad, seguridad TLS 1.3, resiliencia y observabilidad de una aplicación web (BookStack) sobre LNMP.

**Integrantes**
- Sofia Mereles
- Alba Martinez
- Guillermo Gonzalez

**Especificaciones del Entorno**
- **Sistema Operativo:** Ubuntu Server 26.04.1 LTS (VMware Workstation - Modo Bridged)
- **Servidor Web:** Nginx 1.28.3 (Proxy Inverso con Terminación TLS 1.3)
- **Backend:** PHP 8.5-FPM (Unix Domain Socket)
- **Base de Datos:** MariaDB 11.8+ (Restringido a 127.0.0.1)
- **Dominio Local (FQDN):** `https://bookstack.local`


**Estructura del Repositorio**
.
├── config/                  # Configuraciones de Nginx y exportación de reglas UFW
├── scripts/                 # Scripts de prueba (curl HTTPS, Apache Benchmark, tcpdump)
├── docs/                    # Informe integrador en PDF y diagramas de arquitectura
├── .env.example             # Plantilla de variables de entorno de la aplicación
├── .gitignore               # Exclusión de claves privadas, certs y archivos pesados
└── README.md                # Documentación principal del repositorio

**Ejecución de Pruebas Experimentales**
Para validar el comportamiento del sistema, ejecute los scripts automáticos desde la raíz del proyecto:

```bash
# 1. Medir rendimiento y latencia HTTPS (10 iteraciones)
./scripts/medir_latencia_https.sh

# 2. Prueba de carga concurrente (1,000 peticiones / 10 clientes)
./scripts/prueba_estres_ab.sh

# 3. Captura de tráfico de red en puertos 80 y 443
./scripts/captura_tcpdump.sh

**Documentación Completa**
El informe en PDF con las evidencias experimentales, la matriz de pruebas, las pruebas de tolerancia a fallos y los Registros de Decisiones de Arquitectura (ADR) se encuentra disponible en la carpeta docs/.
