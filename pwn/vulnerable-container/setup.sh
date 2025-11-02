#!/bin/bash
# Script para preparar el ambiente dentro del contenedor
# (Si necesitamos configuración adicional post-inicio)

echo "Contenedor vulnerable iniciado"
echo "Usuario actual: $(whoami)"
echo "Permisos sudo disponibles:"
sudo -l