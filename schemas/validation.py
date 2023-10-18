from typing import Optional

import pycountry
def validate_country_code(country_code: Optional[str] = None):
    """
    Validates the country code.
    Args:
        country_code (str): Country code to validate.

    Returns:
        bool: True if the country code is valid, False otherwise.

    Raises:
        KeyError: If the country code is invalid.

    """
    try:
        pycountry.countries.get(alpha_2=country_code)
    except KeyError:
        return False
    return True
