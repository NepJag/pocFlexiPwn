import subprocess
import time
import os

def cleanup():
    """Limpia archivos temporales"""
    for f in ['/tmp/webapp.log', '/tmp/users.db']:
        if os.path.exists(f):
            os.remove(f)

def main():
    print("🎯 PoC: Validación automática de SQLi\n")
    
    # Limpiar
    cleanup()
    
    # Crear archivo de logs vacío
    open('/tmp/webapp.log', 'w').close()
    
    # 1. Iniciar app vulnerable
    print("1️⃣ Iniciando app vulnerable...")
    app_process = subprocess.Popen(['python3', 'vulnerable-app.py'])
    time.sleep(2)
    
    # 2. Iniciar validador en background
    print("2️⃣ Iniciando validador...")
    validator_process = subprocess.Popen(['python3', 'validator.py'])
    
    print("\n" + "="*60)
    print("✨ PoC Lista")
    print("="*60)
    print("\n📍 Visitar: http://localhost:5000")
    print("\n💉 Intentar SQLi:")
    print("   Usuario: admin' OR '1'='1' -- ")
    print("   Contraseña: cualquier cosa")
    print("\n⏳ Esperando vulneración...\n")
    
    try:
        validator_process.wait()
    except KeyboardInterrupt:
        print("\n\n👋 Apagando...")
    finally:
        app_process.terminate()
        validator_process.terminate()
        cleanup()

if __name__ == "__main__":
    main()