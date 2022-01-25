def convert_to_degrees(tag):
    """
    Convert the `exifread` GPS coordinate IfdTag object to degrees in float format.

    :param tag:
    :type tag: exifread.classes.IfdTag
    :rtype: float
    """
    degrees = convert_to_float(tag, 0)
    minutes = convert_to_float(tag, 1)
    seconds = convert_to_float(tag, 2)

    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def convert_to_float(tag, index=0):
    """
    Convert `exifread` IfdTag object to float.

    :param tag:
    :param index:
    :return:
    """
    return float(tag.values[index].num) / float(tag.values[index].den)
