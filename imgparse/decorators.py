"""Decorators for imgparse functions that allow for memoization of EXIF/XMP data on subsequent calls."""

import inspect
import logging

from decorator import decorate, decorator

logger = logging.getLogger(__name__)


def get_from_args_or_kwargs(param_name, arg_list, args, kwargs):
    """
    Get the value of a given input parameter from a function object.

    Takes as input a function argument list, along with the
    cooresponding positional and keyword argument collections
    of the function, and searches them to find the value.

    :param param_name: Name of function parameter to get the value of
    :param arg_list: Function argument list
    :param args: Values of function's positional arguments
    :param kwargs: Dict, in the form of {name: value}, for function's keyword arguments
    :return: **param_value** Value of input parameter name, or None if not found
    """
    if kwargs.get(param_name, None):
        return kwargs[param_name]
    else:
        try:
            return args[arg_list.index(param_name)]
        except (IndexError, ValueError):
            return None


def set_in_args_or_kwargs(param_name, param_value, arg_list, args, kwargs):
    """
    Set the value of a given input parameter of a function object to a given value.

    Takes as input a function argument list, along with the
    corresponding positional and keyword argument collections
    of the function, and places the input parameter value in the
    correct structure.

    :param param_name: Name of function parameter to set the value of
    :param param_value: Value to set for the given parameter name
    :param arg_list: Function argument list
    :param args: Values of function's positional arguments
    :param kwargs: Dict, in the form of {name: value}, for function's keyword arguments
    """
    if kwargs.get(param_name, None):
        kwargs[param_name] = param_value
    else:
        try:
            args[arg_list.index(param_name)] = param_value
        except IndexError:
            kwargs[param_name] = param_value
        except ValueError:
            pass


def get_if_needed(arg_to_get, getter, getter_args=None):
    """
    Decorate a function to fetch one of its arguments, if not passed.

    Throughout the library, nearly all public functions check to see if an exif_data and/or an xmp_data
    argument was passed, and if not, fetch it using the corresponding get_*_data function. This decorator
    takes the place of that boilerplate, and is used by passing the parameters to fetch as arguments, like so:

    @get_if_needed('exif_data', get_exif_data, getter_args=['image_path'])
    def foo(image_path, exif_data=None):
    ...

    :param arg_to_get: Argument of the decorated function to fetch if not present, as a string
    :param getter: The getter function that populates the ``arg_to_get`` within the passed in args/kwargs
    :param getter_args: Arguments to pass from the args/kwargs into the getter function, as a list of strings
    :return:
    """
    # Can't have an empty list as a default param
    if getter_args is None:
        getter_args = []

    @decorator
    def inner_get_if_needed(func, *args, **kwargs):
        args = list(args)
        func_arg_list = inspect.getfullargspec(func).args

        if get_from_args_or_kwargs(arg_to_get, func_arg_list, args, kwargs) is None:
            arg_value = getter(
                **{
                    arg: get_from_args_or_kwargs(arg, func_arg_list, args, kwargs)
                    for arg in getter_args
                }
            )
            set_in_args_or_kwargs(arg_to_get, arg_value, func_arg_list, args, kwargs)

        return func(*args, **kwargs)

    return inner_get_if_needed


def memoize(f):
    """
    Memoize the result of a wrapped function.

    A simple memoize implementation. It works by adding a .cache attribute
    to the decorated function. The cache will only store a single item, so
    any invocation of the wrapped function with different arguments will
    overwrite it.
    """
    f.cache = None
    f.key = None

    def _memoize(func, *args, **kw):
        if kw:  # frozenset is used to ensure hashability
            key = args, frozenset(kw.items())
        else:
            key = args

        cache = func.cache  # attribute added by memoize
        if key is not func.key:
            func.key = key
            cache = func(*args, **kw)
        return cache

    return decorate(f, _memoize)
