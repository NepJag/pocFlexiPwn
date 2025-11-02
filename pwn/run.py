#!/usr/bin/env python3
"""
PoC Runner - Sistema de Detección de Cambios en Filesystem
"""

import subprocess
import time
import shutil
from pathlib import Path


def cleanup():
    """Limpia recursos previos"""
    # Detener contenedor si existe
    subprocess.run(['docker', 'stop', 'vuln-privesc'],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(['docker', 'rm', 'vuln-privesc'],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # Limpiar directorio monitoreado
    monitor_path = Path('./monitored_fs')
    if monitor_path.exists():
        shutil.rmtree(monitor_path)


def setup():
    """Prepara el entorno"""
    print("🔧 Preparando entorno...\n")

    # Crear directorio de monitoreo
    monitor_path = Path('./monitored_fs')
    monitor_path.mkdir(exist_ok=True)

    # Estructura de directorios esperada
    (monitor_path / 'root').mkdir(exist_ok=True)
    (monitor_path / 'etc').mkdir(exist_ok=True)

    # Crear archivos base
    (monitor_path / 'etc/passwd').write_text("root:x:0:0:root:/root:/bin/bash\n")

    print(f"✓ Directorio de monitoreo: {monitor_path.absolute()}\n")

    return monitor_path


def build_container():
    """Construye la imagen del contenedor vulnerable"""
    print("🐳 Construyendo imagen vulnerable...")
    result = subprocess.run(
        ['docker', 'build', '-t', 'vuln-privesc', 'vulnerable-container/'],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print("❌ Error construyendo imagen:")
        print(result.stderr)
        return False

    print("✓ Imagen construida\n")
    return True


def start_container(monitor_path):
    """Inicia el contenedor vulnerable"""
    print("🚀 Iniciando contenedor vulnerable...")

    # Bind mount del filesystem a monitorear
    result = subprocess.Popen([
        'docker', 'run', '-it',
        '--name', 'vuln-privesc',
        '-v', f'{monitor_path.absolute()}/root:/root',
        '-v', f'{monitor_path.absolute()}/etc:/etc_shared',
        'vuln-privesc'
    ])

    return result


def main():
    print("🎯 PoC: Detección de Cambios en Filesystem\n")
    print("=" * 60 + "\n")

    # Limpieza
    cleanup()

    # Setup
    monitor_path = setup()

    # Build
    if not build_container():
        return

    # Iniciar monitor en background
    print("👁️  Iniciando monitor de filesystem...\n")
    monitor_process = subprocess.Popen([
        'python3', 'monitor.py',
        'rules/privesc-detection.yml',
        str(monitor_path.absolute())
    ])

    time.sleep(2)

    # Instrucciones
    print("\n" + "=" * 60)
    print("✨ PoC Listo - Sistema de Monitoreo Activo")
    print("=" * 60)
    print("\n📍 Iniciar contenedor en otra terminal:")
    print(f"   docker run -it --name vuln-privesc \\")
    print(f"     -v {monitor_path.absolute()}/root:/root \\")
    print(f"     vuln-privesc")
    print("\n🎯 Objetivo: Crear el archivo /root/pwned.txt")
    print("\n💡 Pistas:")
    print("   1. Revisa permisos sudo: sudo -l")
    print("   2. Vim puede ejecutar comandos: :!comando")
    print("   3. Desde vim con sudo: :!touch /root/pwned.txt")
    print("\n⏳ El monitor detectará automáticamente el cambio...\n")

    try:
        monitor_process.wait()
    except KeyboardInterrupt:
        print("\n\n👋 Apagando...")
    finally:
        monitor_process.terminate()
        cleanup()


if __name__ == "__main__":
    main()