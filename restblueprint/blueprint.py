from .href_handler import HrefHandlers


def register_blueprint(tornado_app, prefix: str, blueprint):
    for path, target in blueprint.url_patterns:
        tornado_app.add_handlers('.*$', ([join(prefix, path), target],))
    if getattr(blueprint, 'inner_blueprints', None):
        for path, inner in blueprint.inner_blueprints:
            register_blueprint(tornado_app, join(prefix, path), inner)
    if getattr(blueprint, 'href_handlers', None):
        href_handlers = HrefHandlers()
        for handler in blueprint.href_handlers:
            handler.base_url = prefix
            href_handlers.add_handler(handler)


def join(base: str, path: str):
    return '{0}/{1}'.format(base.rstrip('/'), path.lstrip('/'))
