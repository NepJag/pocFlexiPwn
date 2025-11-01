import json
import yaml
import time
from collections import deque

class SigmaLikeValidator:
    def __init__(self, rule_file, log_file):
        self.rule = self.load_rule(rule_file)
        self.log_file = log_file
        self.event_buffer = deque(maxlen=100)  # Últimos 100 eventos
        self.matched = False
        
    def load_rule(self, rule_file):
        """Carga regla YAML"""
        with open(rule_file, 'r') as f:
            return yaml.safe_load(f)
    
    def parse_log_line(self, line):
        """Parsea línea de log JSON"""
        try:
            return json.loads(line.strip())
        except:
            return None
    
    def match_selection(self, event, selection):
        """Verifica si un evento cumple con una selección"""
        for key, value in selection.items():
            if key not in event:
                return False
            if event[key] != value:
                return False
        return True
    
    def evaluate_condition(self):
        """Evalúa la condición de la regla sobre el buffer de eventos"""
        detection = self.rule['detection']

        # Para este PoC: condition = "selection_sqli_chars and selection_success"
        # Buscamos ambos eventos en el buffer
        
        sqli_chars_found = False
        success_found = False
        
        for event in self.event_buffer:
            if self.match_selection(event, detection['selection_sqli_chars']):
                sqli_chars_found = True
            
            if self.match_selection(event, detection['selection_success']):
                success_found = True
        
        return sqli_chars_found and success_found
    
    def monitor(self):
        """Monitorea el archivo de logs continuamente"""
        print(f"🔍 Logs de monitoreo: {self.log_file}")
        print(f"📋 Regla: {self.rule['title']}")
        print(f"⚠️ Nivel: {self.rule['level']}\n")
        
        with open(self.log_file, 'r') as f:
            # Ir al final del archivo
            f.seek(0, 2)
            
            while not self.matched:
                line = f.readline()
                
                if line:
                    event = self.parse_log_line(line)
                    if event:
                        self.event_buffer.append(event)
                        print(f"📝 Evento: {event['event_type']}")
                        
                        # Evaluar regla
                        if self.evaluate_condition():
                            self.matched = True
                            print("\n" + "="*60)
                            print("🚨 Alerta: Inyección SQL detectada!")
                            print(f"Regla: {self.rule['title']}")
                            print(f"Descripción: {self.rule['description']}")
                            print("="*60)
                            print("\n✅ Ejercicio completado!")
                            return True
                else:
                    time.sleep(0.5)  # Esperar nuevos logs

if __name__ == "__main__":
    validator = SigmaLikeValidator(
        rule_file='rules/sqli-detection.yml',
        log_file='/tmp/webapp.log'
    )
    validator.monitor()