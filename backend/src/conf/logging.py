import logging


class LoggerNameFilter(logging.Filter):
    def filter(self, record):
        parts = record.name.split('.')
        if len(parts) > 2:
            record.name = '.'.join(parts[2:])
        return True


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger()
    logger.addFilter(LoggerNameFilter())
    return logger


logger = setup_logging()
