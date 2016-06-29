class HrefType:
    def __init__(self, name, handlers: list, inner_types=list()):
        self.name = name
        self.handlers = handlers
        self.inner_types = inner_types


class HrefHandler:
    parent_placeholder = '$parent'

    def __init__(self, path: str, pattern: str, value_key, href_depth=0, get_values_func=None, set_data_func=None):
        self.path = path.split('.')
        self.pattern = pattern.lstrip('/')
        self.value_keys = value_key if isinstance(value_key, list) else [value_key]
        self.href_depth = href_depth
        self.get_values_func = get_values_func or self._get_values
        self.set_data_func = set_data_func or self._set_data
        self.full_pattern = self.pattern

    def set_full_pattern(self, url_prefix: str):
        self.full_pattern = '{0}/{1}'.format(url_prefix.rstrip('/'), self.pattern)

    @staticmethod
    def _get_values(data: dict, parent_data: dict, value_keys: list):
        values = []
        for key in value_keys:
            if key.startswith(HrefHandler.parent_placeholder + '.'):
                value = parent_data.get(key[len(HrefHandler.parent_placeholder) + 1:])
            else:
                value = data.get(key)
            values.append(value)
        return values

    def get_values(self, data: dict, parent_data: dict):
        return self.get_values_func(data, parent_data, self.value_keys)

    @staticmethod
    def _set_data(data: dict, parent_data: dict, key: str, base_url: str, values: list, pattern: str):
        data[key] = '{0}/{1}'.format(base_url, pattern.lstrip('/').format(*values))

    def set_data(self, data: dict, parent_data: dict, key: str, base_url: str, values: list):
        if all([i is not None for i in values]):
            self.set_data_func(data, parent_data, key, base_url, values, self.full_pattern)


class HrefTypes:
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is None:
            cls.__it__ = it = object.__new__(cls)
            it.__init__()
            it.href_types = {}
            it.use_https = False
        return it

    def __init__(self):
        pass

    def add_type(self, href_type: HrefType):
        if href_type.name in self.href_types:
            raise Exception('HrefType already exists: {0}'.format(href_type.name))
        self.href_types[href_type.name] = href_type

    def resolve(self, data, href_type_name: str, request):
        href_type = self.href_types[href_type_name]
        protocol = 'https' if HrefTypes().use_https else request.protocol
        base_url = '{0}://{1}'.format(protocol, request.host)
        self._resolve(data, href_type, base_url)

    def _resolve(self, data, href_type: HrefType, base_url: str):
        """
        Resolves all hrefs of provided data using request's information
        :param data: list or dict being processed
        :param base_url: host base url
        """
        if isinstance(data, list):
            for i in data:
                self._resolve(i, href_type, base_url)
        elif isinstance(data, dict):
            # resolve hrefs
            for handler in href_type.handlers:
                for next_data, key in self.navigate(data, handler.path):
                    # calculate href and set it to the data
                    values = handler.get_values(next_data, data)
                    handler.set_data(next_data, data, key, base_url, values)
            # resolve inners
            for path, inner_type in href_type.inner_types:
                inner_href_type = self.href_types[inner_type]
                for inner_data, key in self.navigate(data, path.split('.')):
                    if key in inner_data:
                        self._resolve(inner_data[key], inner_href_type, base_url)

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
