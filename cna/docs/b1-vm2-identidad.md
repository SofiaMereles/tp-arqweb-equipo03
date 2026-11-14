# B1 — Separación de identidad de VM-2

Aplicar únicamente en la consola de la VM de VMware llamada `cna-node1`, con red desconectada. VM-1 conserva su identidad. Este documento es un procedimiento; no marca sus pasos como ejecutados.

La configuración del clon se inspeccionó el 12/11/2026: 2 vCPU, 2048 MiB y `startConnected=FALSE` en ambas NIC. MAC nuevas: `00:0c:29:7f:f2:10` y `00:0c:29:7f:f2:1a`. El primer arranque aportado muestra hostname y machine-id heredados.

## Nombre e identificador del sistema

Guardar copia privada antes de cambiar los archivos:

```bash
sudo install -d -m 700 /root/b1-identidad-original
sudo cp -an /etc/hostname /etc/hosts /etc/machine-id /root/b1-identidad-original/
sudo hostnamectl set-hostname cna-node1
sudo sed -i '/^127\.0\.1\.1[[:space:]]/s/arqwebserver/cna-node1/g' /etc/hosts
hostnamectl --static
```

Debe mostrar `cna-node1`. Si algún comando falla, detener el procedimiento y revisar el error antes de continuar.

Después, dejar el identificador vacío para su generación en el próximo arranque y hacer que D-Bus use el mismo archivo. Mantener ambas NIC desconectadas e inmediatamente reiniciar:

```bash
sudo truncate -s 0 /etc/machine-id
sudo ln -sfn /etc/machine-id /var/lib/dbus/machine-id
sudo reboot
```

No invocar `systemd-machine-id-setup` sobre la instancia viva para asumir que produce otro ID: puede recuperar un valor existente. En el reinicio, systemd inicializa el archivo vacío sin copiar un archivo D-Bus heredado separado.

Tras iniciar sesión de nuevo en la consola:

```bash
hostnamectl --static
cat /etc/machine-id
ip -br link
```

Comprobar nombre `cna-node1`, ID de 32 caracteres distinto del de VM-1 y NIC todavía sin enlace. Guardar `PRE-B1-VM2-identidad-nueva.png` en la carpeta de preparación. La identidad SSH y conectividad se verificarán después, antes de considerar el clon listo como nodo independiente.

## Pendiente después de esta comprobación

- Regenerar claves de host SSH del clon, conservando una copia privada y verificando configuración y huellas públicas.
- Revisar nombres y configuración de red heredados; dar IP privada propia y comprobar conectividad.
- Probar restauración aislada antes de retirar del clon los servicios nativos duplicados.
- No copiar identificadores ni claves de VM-2 a VM-1; no publicar copias privadas.

## Fuentes

- [systemd: machine-id e inicialización con archivo vacío](https://www.freedesktop.org/software/systemd/man/248/machine-id.html).
- [systemd-machine-id-setup: reutilización del ID D-Bus](https://www.freedesktop.org/software/systemd/man/259/systemd-machine-id-setup.html).
- [OpenSSH: generación de claves de host mediante ssh-keygen -A](https://man.openbsd.org/ssh-keygen).
