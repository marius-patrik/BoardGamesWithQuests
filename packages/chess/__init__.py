"""Game-specific chess implementation; declarative data in config.json."""


def build_configuration():
    from .runtime import build_configuration as compose

    return compose()
