"""Decorators for imgparse functions that allow for memoization of EXIF/XMP data on subsequent calls."""

import functools
import inspect
import logging

from imgparse.getters import get_exif_data, get_xmp_data

GETTER_FUNCTIONS = {"exif_data": get_exif_data, "xmp_data": get_xmp_data}

logger = logging.getLogger(__name__)


# def get_exif_if_needed(func):
#
#     @functools.wraps(func)
#     def wrapper_get_exif(*args, **kwargs):
#         image_path = args[0] or kwargs['image_path']
#
#         if image_path != wrapper_get_exif.image_path:
#             wrapper_get_exif.exif_data = get_exif_data(image_path)
#             wrapper_get_exif.image_path = image_path
#
#         func(wrapper_get_exif.image_path,
#              wrapper_get_exif.exif_data)
#
#     wrapper_get_exif.image_path = None
#     wrapper_get_exif.exif_data = None
#
#     return wrapper_get_exif


# def cache(*cache_args: str, on: str):
#     def cache_func(func):
#         @functools.wraps(func)
#         def cache_wrapper(*args, **kwargs):
#
#             # First, find out which parameters were specified as args or kwargs:
#             pos_arg_list, kw_arg_list = [], []
#             for func_arg_name in inspect.getfullargspec(func).args:
#                 if func_arg_name in kwargs.keys():
#                     kw_arg_list.append(func_arg_name)
#                 else:
#                     pos_arg_list.append(func_arg_name)
#
#             # Find the parameter to cache on:
#             def _get_from_args_or_kwargs(param_name):
#                 return kwargs[param_name] if param_name in kw_arg_list else args[pos_arg_list.index(param_name)]
#
#             def _set_in_args_or_kwargs(param_name, param_value):
#                 if param_name in kw_arg_list:
#                     kwargs[param_name] = param_value
#                 else:
#                     args[pos_arg_list.index(param_name)] = param_value
#             current_param_value_to_cache_on = _get_from_args_or_kwargs(on)
#
#             if (cache_wrapper.param_value_to_cache_on == current_param_value_to_cache_on
#                 and cache_wrapper.param_value_to_cache_on is not None):
#
#                 # Loop through the cached values:
#                 for cached_arg_name, cached_value in cache_wrapper.cache.items():
#                     if cached_arg_name in kw_arg_list:
#                         kwargs[param]
#
#
#
#
#                 # Check if it was specified as keyword:
#                 if kwargs[cache_arg]:
#                     pass
#                 # Check if it was specified as positional:
#                 elif cache_arg in inspect.getfullargspec(func).args:
#                 pass
#             pass
#
#         cache_wrapper.param_value_to_cache_on = None
#         cache_wrapper.cache = dict.fromkeys(cache_args, None)
#
#         pass
#     pass


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
                func_arg_list = inspect.getfullargspec(func).args
                if kwargs.get(param_name, None):
                    return kwargs[param_name]
                else:
                    try:
                        return args[func_arg_list.index(param_name)]
                    except IndexError:
                        return None

            def _set_in_args_or_kwargs(param_name, param_value):
                func_arg_list = inspect.getfullargspec(func).args
                if kwargs.get(param_name, None):
                    kwargs[param_name] = param_value
                try:
                    args[func_arg_list.index(param_name)] = param_value
                except IndexError:
                    kwargs[param_name] = param_value

            for arg_name in args_to_get:
                if not _get_from_args_or_kwargs(arg_name):
                    arg_value = GETTER_FUNCTIONS[arg_name](
                        _get_from_args_or_kwargs(using)
                    )
                    _set_in_args_or_kwargs(arg_name, arg_value)

            return func(*args, **kwargs)

        return wrapper_get_if_needed

    return inner_get_if_needed
