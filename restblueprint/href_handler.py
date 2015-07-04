from collections import defaultdict


class HrefHandler:
    def __init__(self, href_type: str, path: str, pattern: str, value_key, get_values_func=None, set_data_func=None):
        self.href_type = href_type
        self.path = path.split('.')
        self.pattern = pattern.lstrip('/')
        self.value_keys = value_key if isinstance(value_key, list) else [value_key]
        self.base_url = ''
        self.get_values_func = get_values_func or self._get_values
        self.set_data_func = set_data_func or self._set_data

    @property
    def full_pattern(self):
        return '{0}/{1}'.format(self.base_url.rstrip('/'), self.pattern.lstrip('/'))

    @staticmethod
    def _get_values(data: dict, parent_data: dict, value_keys: list):
        return [data.get(i) for i in value_keys]

    def get_values(self, data: dict, parent_data: dict):
        return self.get_values_func(data, parent_data, self.value_keys)

    @staticmethod
    def _set_data(data: dict, parent_data: dict, key: str, host: str, values: list, pattern: str):
        data[key] = host + pattern.format(*values)

    def set_data(self, data: dict, parent_data: dict, key: str, host: str, values: list):
        if all([i is not None for i in values]):
            self.set_data_func(data, parent_data, key, host, values, self.full_pattern)


class HrefHandlers:
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is None:
            cls.__it__ = it = object.__new__(cls)
            it.__init__()
            it.handlers = defaultdict(list)
        return it

    def __init__(self):
        pass

    def add_handler(self, handler: HrefHandler):
        self.handlers[handler.href_type].append(handler)

    def resolve(self, data, hrefs: dict, request):
        """
        Resolves all hrefs of provided data using request's information
        :param data: list or dict being processed
        :param request: original http request containing the host information in order to build the hrefs
        """
        if isinstance(data, list):
            for i in data:
                self.resolve(i, hrefs, request)
        elif isinstance(data, dict):
            href_type = hrefs['type']
            # resolve hrefs
            for handler in self.handlers[href_type]:
                for next_data, key in self.navigate(data, handler.path):
                    # calculate href and set it to the data
                    values = handler.get_values(next_data, data)
                    host = '{0}://{1}'.format(request.protocol, request.host)
                    handler.set_data(next_data, data, key, host, values)
            # resolve inners
            if 'inner' in hrefs:
                for path, inner_hrefs in hrefs['inner']:
                    for inner_data, key in self.navigate(data, path.split('.')):
                        if key in inner_data:
                            self.resolve(inner_data[key], inner_hrefs, request)

    def navigate(self, data: dict, path: list):
        """
        Navigates through the data dictionary according to the provided path.
        This method will navigate basically through lists and dictionaries.
        The keys used during navigation are separated by '.'

        Example:
        data = { 'children': [{'name': 'a'}, {'name': 'b'}] }
        Then calling navigate(data, 'children.name') will yield
        [(data['children'][0], 'name'), (data['children'][1], 'name')]

        :param data: the provided dictionary
        :param path: path to navigate
        :return: yields a list of dicts and the end of the path (key to be accessed)
        """
        if len(path) == 1:
            yield data, path[0]
        else:
            key = path[0]
            if key in data:
                next_data = data[key]
                if isinstance(next_data, list):
                    for i in next_data:
                        for j, next_path in self.navigate(i, path[1:]):
                            yield j, next_path
                else:
                    for i, next_path in self.navigate(next_data, path[1:]):
                        yield i, next_path
