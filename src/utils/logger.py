import time
import logging
from typing import List

class ExecutionLogger:
    def __init__(self, log_file: str = "execution_log.txt"):
        self.log_file = log_file
        self.start_time = time.time()
        self.logs: List[str] = []
        self.logger = logging.getLogger("ExecutionLogger")

    def log(self, message: str, level: str = "INFO"):
        """Log a message with a timestamp relative to the start time."""
        elapsed = time.time() - self.start_time
        timestamped_message = f"[{elapsed:.2f}s] {message}"
        self.logs.append(timestamped_message)
        
        if level == "INFO":
            self.logger.info(timestamped_message)
        elif level == "WARNING":
            self.logger.warning(timestamped_message)
        elif level == "ERROR":
            self.logger.error(timestamped_message)
        
        # Also print to console for immediate feedback
        print(timestamped_message)

    def save(self):
        """Save the collected logs to a file."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.logs))
            self.logger.info(f"Logs saved to {self.log_file}")
        except Exception as e:
            self.logger.error(f"Failed to save logs: {e}")

    def get_logs(self) -> str:
        return "\n".join(self.logs)
