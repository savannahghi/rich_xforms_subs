from logging.config import dictConfig
from typing import Any, Dict, Mapping, Optional

import yaml
from yaml import Loader

# =============================================================================
# CONSTANTS
# =============================================================================

_DEFAULT_CONFIG: Dict[str, Any] = {
    "main_pipeline": {
        "transport": "app.lib.transports.http.HTTPTransport",
    },
    "http_transport": {
        "transport_adapter": "app.lib.transports.http.ODKCentralHTTPTransportAdapter",
        "connect_timeout": 60,  # 1 minute
        "read_timeout": 300,  # 5 minutes
    },
    # TODO: Remove log handlers before going to production.
    "logging": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": (
                    "%(levelname)s: %(asctime)s %(module)s "
                    "%(process)d %(thread)d %(message)s"
                )
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
}


config: Mapping[str, Any] = None  # type: ignore


# =============================================================================
# HELPERS
# =============================================================================

def _load_config_file(config_file_path: str) -> Mapping[str, Any]:
    with open(config_file_path, "rb") as config_file:
        return yaml.load(config_file, Loader=Loader)


def _setup_logger(logging_config: Dict[str, Any]) -> None:
    dictConfig(logging_config)


def setup(
        default_config: Optional[Dict[str, Any]] = None,
        config_file_path: Optional[str] = None
) -> None:
    """Setup the application and prepare it for use."""
    # This should include things such as:
    # 1. Loading the configuration
    # 2. Setting up the default loggers
    # 3. Initializing external services, etc
    configuration: Dict[str, Any] = default_config or _DEFAULT_CONFIG
    if config_file_path:
        _config_updates = _load_config_file(config_file_path)
        configuration.update(_config_updates)
    if "logging" in configuration:
        _setup_logger(configuration["logging"])
    global config
    config = configuration
