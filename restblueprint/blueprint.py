from .href_type import HrefTypes


def register_blueprint(tornado_app, prefix: str, blueprint):
    for path, target in blueprint.url_patterns:
        tornado_app.add_handlers('.*$', ([join(prefix, path), target],))

    if getattr(blueprint, 'inner_blueprints', None):
        for path, inner in blueprint.inner_blueprints:
            register_blueprint(tornado_app, join(prefix, path), inner)

    href_types = HrefTypes()
    if getattr(blueprint, 'href_types', None):
        for href_type in blueprint.href_types:
            href_type.set_url_prefix(prefix)
            href_types.add_type(href_type)


def join(base: str, path: str):
    return '{0}/{1}'.format(base.rstrip('/'), path.lstrip('/'))
