#!/usr/bin/env python3
"""
Filesystem Monitor - Inspección de Contenedores Docker
"""

import yaml
import time
import subprocess
import fnmatch
from pathlib import Path
from datetime import datetime


class DockerFilesystemMonitor:
    def __init__(self, rule_file, container_name):
        self.rule = self.load_rule(rule_file)
        self.container_name = container_name
        self.file_states = {}  # {path: last_mtime}
        self.matched_targets = set()
        self.running = False

    def load_rule(self, rule_file):
        """Carga regla YAML"""
        with open(rule_file, 'r') as f:
            return yaml.safe_load(f)

    def container_exists(self):
        """Verifica si el contenedor existe y está corriendo"""
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={self.container_name}', '--format', '{{.Names}}'],
            capture_output=True, text=True
        )
        return self.container_name in result.stdout

    def get_file_mtime(self, path):
        """Obtiene timestamp de modificación desde el contenedor"""
        result = subprocess.run(
            ['docker', 'exec', '--user', 'root', self.container_name, 'stat', '-c', '%Y', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        if result.returncode == 0:
            try:
                return int(result.stdout.strip())
            except ValueError:
                return None
        return None

    def list_directory_files(self, dir_path, pattern=None):
        """Lista archivos en un directorio del contenedor"""
        result = subprocess.run(
            ['docker', 'exec', '--user', 'root', self.container_name, 'find', dir_path,
             '-maxdepth', '1', '-type', 'f'],
            stdout=subprocess.PIPE,  # ✅ Explícito
            stderr=subprocess.DEVNULL,
            text=True
        )

        if result.returncode != 0:
            return []

        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]

        # Filtrar por patrón si existe
        if pattern:
            files = [f for f in files if fnmatch.fnmatch(Path(f).name, pattern)]

        return files

    def check_target(self, target):
        """Verifica un target específico"""
        path = target['path']
        events = target['events']

        # Si es un directorio, buscar archivos que coincidan con el patrón
        if path.endswith('/'):
            pattern = target.get('pattern')
            current_files = self.list_directory_files(path.rstrip('/'), pattern)

            # Inicializar estado si es primera vez
            if path not in self.file_states:
                self.file_states[path] = {}
                for file_path in current_files:
                    mtime = self.get_file_mtime(file_path)
                    if mtime:
                        self.file_states[path][file_path] = mtime
                return False

            # Detectar nuevos archivos (CREATE)
            if 'CREATE' in events:
                for file_path in current_files:
                    if file_path not in self.file_states[path]:
                        mtime = self.get_file_mtime(file_path)
                        if mtime:
                            self.file_states[path][file_path] = mtime
                            self.handle_detection(file_path, 'CREATE', target)
                            return True

            # Detectar modificaciones (MODIFY, MOVED_TO)
            if any(event in events for event in ['MODIFY', 'MOVED_TO']):
                for file_path in current_files:
                    current_mtime = self.get_file_mtime(file_path)
                    if file_path in self.file_states[path]:
                        if current_mtime and current_mtime > self.file_states[path][file_path]:
                            self.file_states[path][file_path] = current_mtime
                            self.handle_detection(file_path, 'MODIFY', target)
                            return True
        else:
            # Archivo específico
            current_mtime = self.get_file_mtime(path)

            # Primera vez viendo este archivo
            if path not in self.file_states:
                if current_mtime and 'CREATE' in events:
                    self.file_states[path] = current_mtime
                    self.handle_detection(path, 'CREATE', target)
                    return True
                elif current_mtime:
                    self.file_states[path] = current_mtime
                return False

            # Archivo modificado
            if current_mtime and current_mtime > self.file_states[path]:
                if any(event in events for event in ['MODIFY', 'MOVED_TO']):
                    self.file_states[path] = current_mtime
                    self.handle_detection(path, 'MODIFY', target)
                    return True

        return False

    def handle_detection(self, file_path, event_type, target):
        """Procesa una detección de cambio"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"[{timestamp}] 🎯 Evento detectado!")
        print(f"   Archivo: {file_path}")
        print(f"   Evento: {event_type}")
        print(f"   Descripción: {target['description']}\n")

        self.matched_targets.add(file_path)

        # Evaluar condición
        if self.evaluate_condition():
            self.alert_success()
            self.running = False

    def evaluate_condition(self):
        """Evalúa si se cumple la condición de la regla"""
        condition = self.rule.get('condition', 'any')

        if condition == 'any':
            return len(self.matched_targets) > 0
        elif condition == 'all':
            return len(self.matched_targets) == len(self.rule['targets'])

        return False

    def setup_monitoring(self):
        """Muestra información de los targets a monitorear"""
        print(f"🐳 Contenedor: {self.container_name}")
        print(f"📋 Regla: {self.rule['title']}\n")

        for target in self.rule['targets']:
            print(f"👁️  Watching: {target['path']}")
            print(f"   Eventos: {', '.join(target['events'])}")
            if target.get('pattern'):
                print(f"   Patrón: {target['pattern']}")
            print(f"   {target['description']}\n")

    def monitor(self):
        """Loop principal de monitoreo"""
        print("=" * 60)
        print("🔍 Esperando contenedor...")
        print("=" * 60 + "\n")

        # Esperar a que el contenedor esté disponible
        while not self.container_exists():
            time.sleep(1)

        print(f"✓ Contenedor '{self.container_name}' detectado\n")
        self.setup_monitoring()

        print("=" * 60)
        print("🔍 Monitoreo activo - Inspeccionando filesystem...")
        print("=" * 60 + "\n")

        self.running = True

        try:
            while self.running:
                if not self.container_exists():
                    print("\n⚠️  Contenedor detenido")
                    break

                # Verificar cada target
                for target in self.rule['targets']:
                    self.check_target(target)

                time.sleep(2)  # Polling cada 2 segundos

        except KeyboardInterrupt:
            print("\n\n👋 Monitoreo detenido")

        return len(self.matched_targets) > 0

    def alert_success(self):
        """Muestra alerta de ejercicio completado"""
        print("\n" + "=" * 60)
        print("🚨 ALERTA: Escalación de privilegios detectada!")
        print("=" * 60)
        print(f"Regla: {self.rule['title']}")
        print(f"Descripción: {self.rule['description']}")
        print(f"Nivel: {self.rule['level']}")
        print(f"\nArchivos comprometidos: {len(self.matched_targets)}")
        for target in self.matched_targets:
            print(f"  - {target}")
        print("\n✅ Ejercicio completado exitosamente!")
        print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Uso: python3 monitor.py <rule_file> <container_name>")
        sys.exit(1)

    monitor = DockerFilesystemMonitor(
        rule_file=sys.argv[1],
        container_name=sys.argv[2]
    )

    monitor.monitor()