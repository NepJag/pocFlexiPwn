#!/usr/bin/env python3
"""
Filesystem Monitor - Detección Externa de Cambios
Compatible con macOS, Linux y Windows usando watchdog
"""

import yaml
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class RuleBasedEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor
        super().__init__()

    def on_created(self, event):
        if not event.is_directory:
            self.monitor.handle_event(event.src_path, 'CREATE')

    def on_modified(self, event):
        if not event.is_directory:
            self.monitor.handle_event(event.src_path, 'MODIFY')

    def on_deleted(self, event):
        if not event.is_directory:
            self.monitor.handle_event(event.src_path, 'DELETE')

    def on_moved(self, event):
        if not event.is_directory:
            self.monitor.handle_event(event.dest_path, 'MOVED_TO')


class FilesystemMonitor:
    def __init__(self, rule_file, watch_path):
        self.rule = self.load_rule(rule_file)
        self.watch_path = Path(watch_path).resolve()
        self.matched_targets = set()
        self.running = False

    def load_rule(self, rule_file):
        """Carga regla YAML"""
        with open(rule_file, 'r') as f:
            return yaml.safe_load(f)

    def normalize_path(self, path):
        """Normaliza path para comparación"""
        return str(Path(path).resolve())

    def get_target_for_path(self, file_path):
        """Busca si un path corresponde a algún target"""
        normalized_path = self.normalize_path(file_path)

        for target in self.rule['targets']:
            # Path esperado = watch_path + target_path
            target_path = self.watch_path / target['path'].lstrip('/')
            normalized_target = self.normalize_path(target_path)

            if normalized_path == normalized_target:
                return target

        return None

    def handle_event(self, file_path, event_type):
        """Procesa un evento del filesystem"""
        target = self.get_target_for_path(file_path)

        if target and event_type in target['events']:
            timestamp = datetime.now().strftime("%H:%M:%S")
            rel_path = Path(file_path).relative_to(self.watch_path)

            print(f"[{timestamp}] 🎯 Evento detectado!")
            print(f"   Archivo: /{rel_path}")
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

    def setup_watches(self):
        """Muestra información de los targets a monitorear"""
        print(f"📂 Monitoreando: {self.watch_path}")
        print(f"📋 Regla: {self.rule['title']}\n")

        for target in self.rule['targets']:
            target_path = self.watch_path / target['path'].lstrip('/')

            # Crear directorio padre si no existe
            target_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"👁️  Watching: {target['path']}")
            print(f"   Eventos: {', '.join(target['events'])}")
            print(f"   {target['description']}\n")

    def monitor(self):
        """Loop principal de monitoreo"""
        self.setup_watches()

        print("=" * 60)
        print("🔍 Monitoreo activo - Esperando cambios en filesystem...")
        print("=" * 60 + "\n")

        # Crear observer y event handler
        event_handler = RuleBasedEventHandler(self)
        observer = Observer()

        # Watch recursivo del directorio completo
        observer.schedule(event_handler, str(self.watch_path), recursive=True)

        observer.start()
        self.running = True

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoreo detenido")
        finally:
            observer.stop()
            observer.join()

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
            rel_path = Path(target).relative_to(self.watch_path)
            print(f"  - /{rel_path}")
        print("\n✅ Ejercicio completado exitosamente!")
        print("=" * 60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Uso: python3 monitor.py <rule_file> <watch_path>")
        sys.exit(1)

    monitor = FilesystemMonitor(
        rule_file=sys.argv[1],
        watch_path=sys.argv[2]
    )

    monitor.monitor()