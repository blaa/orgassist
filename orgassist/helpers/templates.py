import os
import jinja2
from orgassist import log
from orgassist.config import ConfigError

def get_default_template(filename, module_file):
    """
    Compute template path and check existance.

    Default templates are located within modules in a "templates" subdirectory.
    """
    base_path = os.path.dirname(os.path.abspath(module_file))
    base_path = os.path.join(base_path, 'templates')
    path = os.path.join(base_path, filename)
    try:
        log.debug("Trying template: %s", path)
        with open(path) as handle:
            handle.read()
    except IOError:
        raise ConfigError('Unable to open template file: ' +
                          path)
    return path


def get_template(path, content=None):
    """
    Read file and create template.

    Use content if not None.
    """
    if content is not None:
        assert path is None
    else:
        assert path is not None
        with open(path, 'r') as handle:
            content = handle.read()
    template = jinja2.Template(content,
                               trim_blocks=True,
                               lstrip_blocks=True)
    return template
