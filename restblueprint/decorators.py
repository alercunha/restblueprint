import datetime
import types
import json
import functools
import jsonschema

from .href_type import HrefTypes


def json_handler(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return None


def write_result_to_handler(result, handler, href_type: str=None):
    # evaluate enumerator if needed
    if isinstance(result, types.GeneratorType):
        result = list(result)

    # write result if any
    if result is not None:
        if href_type:
            HrefTypes().resolve(result, href_type, handler.request)
        indent = 1 if handler.get_query_argument('pretty', None) == 'true' else None
        handler.set_header('Content-Type', 'application/json')
        handler.write(json.dumps(result, default=json_handler, sort_keys=True, indent=indent))
    else:
        handler.set_header('Content-Type', 'text/plain')
        handler.set_status(204)


def jsoncall(method=None, input_schema: dict=None, href_type: str=None):
    # If called without method, we've been called with optional arguments.
    # We return a decorator with the optional arguments filled in.
    # Next time round we'll be decorating method.
    if method is None:
        return functools.partial(jsoncall, input_schema=input_schema, href_type=href_type)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        body = self.request.body
        self.request.jsoncall = True

        # decode json body and validate
        if body is not None:
            decoded = body.decode()
            if decoded:
                body = json.loads(decoded)
                if input_schema is not None:
                    jsonschema.validate(body, input_schema)
                self.request.body = body

        # call the actual handler method
        result = method(self, *args, **kwargs)
        # write result
        write_result_to_handler(result, self, href_type)

    return wrapper


def jsonout(method=None, href_type: str=None, async: bool=False):
    # If called without method, we've been called with optional arguments.
    # We return a decorator with the optional arguments filled in.
    # Next time round we'll be decorating method.
    if method is None:
        return functools.partial(jsonout, href_type=href_type, async=async)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.request.jsoncall = True

        # call the actual method
        result = method(self, *args, **kwargs)
        # write result
        write_result_to_handler(result, self, href_type)
        # if coming from async call then must finish request manually
        if async:
            self.finish()

    return wrapper
