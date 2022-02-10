import configparser


_SETTINGS_FILE = 'settings.ini'


def _read_settings_file(settings_file):
    try:
        _config.read(settings_file)
    except FileNotFoundError:
        pass


def get_style_from_settings_file() -> str:
    style = 'Fusion'
    try:
        style = _config['WindowSettings']['style']
    except KeyError:
        pass
    return style


def save_style_in_settings_file(style: str) -> None:
    _config['WindowSettings']['style'] = style
    with open(_SETTINGS_FILE, 'w') as configfile:
        _config.write(configfile)


_config = configparser.ConfigParser()
_read_settings_file(_SETTINGS_FILE)



