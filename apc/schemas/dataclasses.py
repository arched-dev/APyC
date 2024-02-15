from dataclasses import dataclass, asdict, field
from datetime import time
from enum import Enum
from typing import Optional

from apc.schemas.validation import validate_country_code


class ItemType(Enum):
    """Enumerates the acceptable item types."""

    LIMITED_QUANTITIES = "LIMITED QUANTITIES"
    LIQUIDS = "LIQUIDS"
    PACK = "PACK"
    PALLET = "PALLET"
    PARCEL = "PARCEL"
    ALL = "ALL"


@dataclass
class Item:

    """Represents an Item for shipping.

    Attributes:
        weight (float): Weight of the piece in KG. Required.
        type (Optional[ItemType]): Type of the item, must be one of ItemType enum values. Defaults to All.
        length (Optional[float]): Length of the piece in meters. Defaults to None.
        width (Optional[float]): Width of the piece in meters. Defaults to None.
        height (Optional[float]): Height of the piece in meters. Defaults to None.
        value (Optional[float]): Monetary value of the piece. Defaults to None.
    """

    weight: float
    type: Optional[ItemType] = field(default=ItemType.ALL)
    length: Optional[float] = field(default=None)
    width: Optional[float] = field(default=None)
    height: Optional[float] = field(default=None)
    value: Optional[float] = field(default=None)

    def __post_init__(self):
        if not isinstance(self.type, ItemType):
            raise ValueError(f"Invalid item type: {self.type}")
    def to_dict(self):

        out = asdict(self)
        out["type"] = out["type"].value
        return out


@dataclass
class Address:
    """Dataclass representing a company's details.

    Attributes:
        company_name (str): Name of the company.
        address_line1 (str): First line of the address.
        city (str): City name.
        postal_code (str): Postal code.
        open_from (str): Opening time of the company.
        open_to (str): Closing time of the company.
        address_line2 (Optional[str]): Second line of the address.
        county (Optional[str]): County name.
        country_code (Optional[str]): Country code. 2 Digit Alpha 2 code. Default to GB
        person_name (Optional[str]): Contact person's name.
        phone_number (Optional[str]): Contact person's phone number.
        email (Optional[str]): Contact person's email.
    """

    company_name: str
    address_line1: str
    city: str
    postal_code: str
    open_from: Optional[time] = field(default=None)
    open_to: Optional[time] = field(default=None)
    address_line2: Optional[str] = field(default=None)
    county: Optional[str] = field(default=None)
    country_code: Optional[str] = field(default="GB")
    person_name: Optional[str] = field(default=None)
    phone_number: Optional[str] = field(default=None)
    mobile_number: Optional[str] = field(default=None)
    email: Optional[str] = field(default=None)

    def __post_init__(self):
        """
        Validates the data class.
        Returns:
            None
        Raises:
            ValidationError: If the country code is invalid.
        """
        validate_country_code(self.country_code)
        if self.address_line1 is None or self.address_line1 == "":
            raise ValueError("Address line 1 is required.")
        if self.postal_code is None or self.postal_code == "":
            raise ValueError("Postal code is required.")
        if self.city is None or self.city == "":
            raise ValueError("City is required.")

    def to_dict(self):
        """Converts the Company object to a dictionary.

        Returns:
            dict: A dictionary representation of the Company object.
        """
        data = asdict(self)
        data["contact"] = {
            "person_name": data.pop("person_name"),
            "phone_number": data.pop("phone_number"),
            "mobile_number": data.pop("mobile_number"),
            "email": data.pop("email")
        }
        return data
