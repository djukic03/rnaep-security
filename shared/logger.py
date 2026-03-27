import logging
import graypy
from prometheus_fastapi_instrumentator import Instrumentator

def get_logger(service_name: str, graylog_host: str = "graylog"):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    graylog = graypy.GELFUDPHandler(graylog_host, 12201)
    logger.addHandler(graylog)

    console = logging.StreamHandler()
    logger.addHandler(console)

    return logger

def setup_metrics(app, service_name: str):
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app)
