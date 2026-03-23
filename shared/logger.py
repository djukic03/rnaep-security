import logging
import graypy

def get_logger(service_name: str, graylog_host: str = "graylog"):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    graylog = graypy.GELFUDPHandler(graylog_host, 12201)
    logger.addHandler(graylog)

    console = logging.StreamHandler()
    logger.addHandler(console)

    return logger