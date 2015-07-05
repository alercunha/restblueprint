import datetime
import types
import json
import functools
import jsonschema

from .href_handler import HrefHandlers


def json_handler(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return None


def write_result_to_handler(result, handler, hrefs: dict=None):
    # evaluate enumerator if needed
    if isinstance(result, types.GeneratorType):
        result = list(result)

    # write result if any
    if result is not None:
        if hrefs is not None:
            HrefHandlers().resolve(result, hrefs, handler.request)
        handler.set_header('Content-Type', 'application/json')
        handler.write(json.dumps(result, default=json_handler, sort_keys=True, indent=1))
    else:
        handler.set_header('Content-Type', 'text/plain')
        handler.set_status(204)


def jsoncall(method=None, input_schema: dict=None, hrefs: dict=None):
    # If called without method, we've been called with optional arguments.
    # We return a decorator with the optional arguments filled in.
    # Next time round we'll be decorating method.
    if method is None:
        return functools.partial(jsoncall, input_schema=input_schema, hrefs=hrefs)

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
        write_result_to_handler(result, self, hrefs)

    return wrapper


def jsonout(method=None, hrefs: dict=None, async: bool=False):
    # If called without method, we've been called with optional arguments.
    # We return a decorator with the optional arguments filled in.
    # Next time round we'll be decorating method.
    if method is None:
        return functools.partial(jsonout, hrefs=hrefs, async=async)

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.request.jsoncall = True

        # call the actual method
        result = method(self, *args, **kwargs)
        # write result
        write_result_to_handler(result, self, hrefs)
        # if coming from async call then must finish request manually
        if async:
            self.finish()

    return wrapper
