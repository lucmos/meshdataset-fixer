from typing import Optional, Any
import os


def get_env(env_name: str, default: Optional[Any] = None) -> str:
    """
    Read an environment variable.
    Raises errors if it is not defined or empty.

    :param env_name: the name of the environment variable
    :param default: default value if env_name is not defined
    :return: the value of the environment variable
    """
    if env_name not in os.environ:
        if default:
            return default
        raise KeyError(f"{env_name} not defined")
    env_value: str = os.environ[env_name]
    if not env_value:
        if default:
            return default
        raise KeyError(f"{env_name} has yet to be configured")
    return env_value
