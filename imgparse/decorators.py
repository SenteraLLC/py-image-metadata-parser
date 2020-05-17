"""Decorators for imgparse functions that allow for memoization of EXIF/XMP data on subsequent calls."""

import functools
import inspect
import logging

from imgparse.getters import get_exif_data, get_xmp_data

GETTER_FUNCTIONS = {"exif_data": get_exif_data, "xmp_data": get_xmp_data}

logger = logging.getLogger(__name__)


def get_if_needed(*args_to_get, using):
    """
    Decorate a function to fetch one or more of its arguments if not passed.

    Throughout the library, nearly all public functions check to see if an exif_data and/or an xmp_data
    argument was passed, and if not, fetch it using the cooresponding get_*_data function. This decorator
    takes the place of that boilerplate, and is used by passing the parameters to fetch as arguments, like so:

    @get_if_needed('exif_data', 'xmp_data', using='image_path')
    def foo(image_path, exif_data=None):
    ...

    Currently, fetching 'exif_data' and 'xmp_data' is supported, but theoretically support for other
    arguments could be added by adding a "getter function" to the "GETTER_FUNCTIONS" constant dictionary.

    :param args_to_get: Arguments of the decorated function to fetch if not present, as strings
    :param using: Argument to pass to each of the arguments to fetch's getter function
    :return:
    """

    def inner_get_if_needed(func):
        @functools.wraps(func)
        def wrapper_get_if_needed(*args, **kwargs):
            args = list(args)

            def _get_from_args_or_kwargs(param_name):
                if kwargs.get(param_name, None):
                    return kwargs[param_name]
                else:
                    try:
                        return args[
                            wrapper_get_if_needed.func_arg_list.index(param_name)
                        ]
                    except IndexError:
                        return None

            def _set_in_args_or_kwargs(param_name, param_value):
                if kwargs.get(param_name, None):
                    kwargs[param_name] = param_value
                try:
                    args[
                        wrapper_get_if_needed.func_arg_list.index(param_name)
                    ] = param_value
                except IndexError:
                    kwargs[param_name] = param_value

            for arg_name in args_to_get:
                if not _get_from_args_or_kwargs(arg_name):
                    arg_value = GETTER_FUNCTIONS[arg_name](
                        _get_from_args_or_kwargs(using)
                    )
                    _set_in_args_or_kwargs(arg_name, arg_value)

            return func(*args, **kwargs)

        wrapper_get_if_needed.func_arg_list = inspect.getfullargspec(func).args
        return wrapper_get_if_needed

    return inner_get_if_needed
