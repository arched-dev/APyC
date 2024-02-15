import re

def camel_to_snake(name):
    # Insert an underscore before each uppercase letter followed by a lowercase letter
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert an underscore before each uppercase letter that follows a lowercase letter or number
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def nested_lookup(d, keys):
    """
    Lookup a key in a nested dictionary.
    Args:
        d (dict): Dictionary to lookup.
        keys (list): List of keys to lookup.

    Returns:
        The value of the key if found, None otherwise.
    """
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return None
    return d
