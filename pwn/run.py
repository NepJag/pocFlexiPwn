#!/usr/bin/env python3
"""
PoC Runner - Sistema de Detección de Cambios en Filesystem
"""

import subprocess
import time

def cleanup():
    """Limpia recursos previos"""
    subprocess.run(['docker', 'stop', 'vuln-privesc'],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(['docker', 'rm', 'vuln-privesc'],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


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


def main():
    print("🎯 PoC: Detección Genérica de Privilege Escalation\n")
    print("=" * 60 + "\n")

    cleanup()

    if not build_container():
        return

    print("👁️  Iniciando monitor de filesystem...\n")
    monitor_process = subprocess.Popen([
        'python3', 'monitor.py',
        'rules/privesc-detection.yml',
        'vuln-privesc'
    ])

    time.sleep(2)

    print("\n" + "=" * 60)
    print("✨ PoC Listo - Sistema de Monitoreo Activo")
    print("=" * 60)
    print("\n📍 Iniciar contenedor en otra terminal:")
    print("   docker run -it --name vuln-privesc vuln-privesc")
    print("\n🎯 Objetivos posibles (cualquiera activa la detección):")
    print("   1. Crear cualquier archivo .txt en /root/")
    print("   2. Modificar /etc/passwd")
    print("   3. Modificar /etc/shadow")
    print("   4. Agregar clave SSH en /root/.ssh/authorized_keys")
    print("\n💡 Pistas:")
    print("   • Revisa permisos sudo: sudo -l")
    print("   • Vim puede ejecutar comandos: :!comando")
    print("   • Ejemplos desde vim con sudo:")
    print("     :!touch /root/pwned.txt")
    print("     :!echo 'hacked' > /root/exploit.txt")
    print("     :!vim /etc/passwd")
    print("\n⏳ El monitor detectará automáticamente cualquier cambio...\n")

    try:
        monitor_process.wait()
    except KeyboardInterrupt:
        print("\n\n👋 Apagando...")
    finally:
        monitor_process.terminate()
        cleanup()


if __name__ == "__main__":
    main()