"""Decorators for imgparse functions that allow for memoization of EXIF/XMP data on subsequent calls."""

import functools
import inspect
import logging

from imgparse.getters import get_exif_data, get_xmp_data

GETTER_FUNCTIONS = {"exif_data": get_exif_data, "xmp_data": get_xmp_data}

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
    cooresponding positional and keyword argument collections
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

    def inner_get_if_needed(func):
        @functools.wraps(func)
        def wrapper_get_if_needed(*args, **kwargs):
            args = list(args)
            func_arg_list = inspect.getfullargspec(func).args or func.func_arg_list

            if get_from_args_or_kwargs(arg_to_get, func_arg_list, args, kwargs) is None:
                arg_value = getter(
                    *[
                        get_from_args_or_kwargs(arg, func_arg_list, args, kwargs)
                        for arg in getter_args
                    ]
                )
                set_in_args_or_kwargs(
                    arg_to_get, arg_value, func_arg_list, args, kwargs
                )

            return func(*args, **kwargs)

        return wrapper_get_if_needed

    return inner_get_if_needed


def cache(*args_to_cache, using):
    """
    Decorate a function to cache one or more of its input values for subsequent calls.

    If placed as a decorator to a function while "unapplied" (with passed-in arguments), it will
    only cache the given arguments for subsequent calls to that function only. However,
    if "applied" (passed arguments) separately and placed on a function in its applied form, the cached
    arguments will serve as persistent state that can be shared between any function that
    is decorated in this manner. Functions can be decorated with the applied form even if
    they do not take all the arguments that are in the cache, as these values will simply be skipped.

    :param args_to_cache: Names of arguments to cache, as strings
    :param using: Name of argument that, when its value matches that of the cache's value, indicates that the cache
                 may be applied.
    :return:
    """

    def cache_decorator(func):
        @functools.wraps(func)
        def cache_inner(*args, **kwargs):
            args = list(args)
            func_arg_list = inspect.getfullargspec(func).args or func.func_arg_list

            using_value = get_from_args_or_kwargs(using, func_arg_list, args, kwargs)
            if cache_decorator.using == using_value:
                for cache_arg in args_to_cache:
                    if cache_arg in cache_decorator.cache:
                        set_in_args_or_kwargs(
                            cache_arg,
                            cache_decorator.cache[cache_arg],
                            func_arg_list,
                            args,
                            kwargs,
                        )
            else:
                cache_decorator.cache = {}
                cache_decorator.using = using_value

            for cache_arg in args_to_cache:
                cache_arg_value = get_from_args_or_kwargs(
                    cache_arg, func_arg_list, args, kwargs
                )
                if cache_arg_value:
                    cache_decorator.cache[cache_arg] = cache_arg_value

            return func(*args, **kwargs)

        cache_inner.func_arg_list = inspect.getfullargspec(func).args
        return cache_inner

    cache_decorator.using = None
    cache_decorator.cache = {}
    return cache_decorator
