import logging


class ConsoleFormatter(logging.Formatter):

    COLOR_CODES = {
        logging.DEBUG: "\033[97m",          # White
        logging.INFO: "\033[93m",           # Yellow
        logging.WARNING: "\033[38;5;214m",  # Orange
        logging.ERROR: "\033[91m",          # Red
        logging.CRITICAL: "\033[95m"        # Magenta
    }
    RESET_CODE = "\033[0m"

    def format(self, record):
        levelname_padded = f"{record.levelname}:".ljust(9)
        log_msg = f"{levelname_padded} {record.getMessage()}"
        color_code = self.COLOR_CODES.get(record.levelno, "")
        log_msg = f"{color_code}{log_msg}{self.RESET_CODE}"
        return log_msg
