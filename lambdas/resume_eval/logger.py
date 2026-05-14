import json
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self, function_name):
        self.function_name = function_name
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
    
    def _log(self, level, message, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "function_name": self.function_name,
            "level": level,
            "message": message,
            **kwargs
        }
        print(json.dumps(log_entry))
    
    def info(self, message, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def debug(self, message, **kwargs):
        self._log("DEBUG", message, **kwargs)
