from .href_type import HrefTypes


def register_blueprint(tornado_app, prefix: str, blueprint):
    _register_blueprint(tornado_app, [prefix], blueprint)


def _register_blueprint(tornado_app, prefixes: list, blueprint):
    for path, target in blueprint.url_patterns:
        tornado_app.add_handlers('.*$', ([join(prefixes + [path]), target],))

    if getattr(blueprint, 'inner_blueprints', None):
        for path, inner in blueprint.inner_blueprints:
            _register_blueprint(tornado_app, prefixes + [path], inner)

    href_types = HrefTypes()
    if getattr(blueprint, 'href_types', None):
        for href_type in blueprint.href_types:
            for handler in href_type.handlers:
                url_prefix = join(prefixes[0:len(prefixes) - handler.href_depth])
                handler.set_full_pattern(url_prefix)
            href_types.add_type(href_type)


def join(prefixes: list):
    if len(prefixes) == 0:
        raise Exception('List of prefixes cannot be empty')
    if len(prefixes) == 1:
        return prefixes[0]
    path = '{0}/{1}'.format(prefixes[0].rstrip('/'), prefixes[1].lstrip('/'))
    return join([path] + prefixes[2:])


def use_https(use: bool):
    HrefTypes().use_https = use
