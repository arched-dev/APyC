import base64
import datetime
import os
from datetime import time
from typing import List, Dict, Optional, Any, Union

import requests
from marshmallow import ValidationError, Schema
from requests import RequestException

from apc.schemas.dataclasses import Item, Address
from apc.schemas.exceptions import ApiFieldException
from apc.schemas.models import Services
from apc.schemas.schemas import (
    ServiceCheckSchema,
    CarrierSchema,
    ExtendedFullOrderSchema,
    OrderOutputApiResponseSchema,
)
from apc.schemas.utilities import camel_to_snake, nested_lookup


class _BaseApi:
    base_url: str
    _username: str
    _password: str

    def __init__(
        self, username: str, password: str, is_sandbox: Optional[bool] = False
    ):
        self.base_url = (
            "https://apc-training.hypaship.com/api/3.0"
            if is_sandbox
            else "https://apc.hypaship.com/api/3.0"
        )
        self._password = password
        self._username = username

    def validate(self):
        if self._password is None or not isinstance(self._password, str):
            raise ValueError("The password supplied does not appear valid.")
        if self._username is None or not isinstance(self._username, str):
            raise ValueError("The username supplied does not appear valid.")

    def make_request(
        self,
        url: str,
        method: str = "GET",
        url_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        out_schema: Optional[Schema] = None,
        output_base: Optional[List[str]] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        The main calling function to get from the APC Api.

        Args:
            url (str): The endpoint URL.
            method (str): One of GET, POST, PUT. Defaults to "GET".
            url_params (Optional[Dict[str, Any]]): A dictionary of URL parameters.
            body (Optional[Dict[str, Any]]): A dictionary containing the body request.
            schema (Optional[Schema]): A schema to serialize the response from the API.

        Returns:
            response (Union[Dict[str, Any], List[Dict[str, Any]]]): the api response
        """
        try:
            # Determine the HTTP method to use+

            # Base64 encode the username and password for the 'remote-user' header
            auth_string = f"{self._username}:{self._password}"
            auth_string_base64 = base64.b64encode(auth_string.encode("utf-8")).decode(
                "utf-8"
            )

            # Create the headers dictionary
            headers = {
                "Content-Type": "application/json",
                "remote-user": f"Basic {auth_string_base64}",
            }

            call_func = getattr(requests, method.lower(), None)
            if call_func is None:
                raise ValueError("HTTP Method unknown, cannot continue.")

            # Construct the full URL
            call_url = self.base_url + url

            # Perform the API call
            response = call_func(
                call_url, params=url_params, json=body, headers=headers
            )

            # Check if the request was successful
            response.raise_for_status()

            # Deserialize the response if a schema is provided
            # Deserialize the response if an in_schema is provided
            deserialized_data = response.json()
            self._handle_error_response(deserialized_data)

            # Use nested_lookup to find the relevant part of the response
            if output_base:
                result = nested_lookup(deserialized_data, output_base)
            else:
                result = deserialized_data
            if isinstance(result, list):
                return out_schema().load(data=result, many=True)
            return out_schema().load(data=result)

        except RequestException as re:
            raise ConnectionError(f"Request failed: {re}")

    def _handle_error_response(self, jresp: Dict[str, Any]):
        """
        Handle a response from
        Args:
            jresp (Dict): The response from the API

        Returns:
            None

        Raises:
            ValidationError
        """

        main_key = list(jresp.keys())[0]

        if jresp[main_key]["Messages"]["Code"] == "ERROR":
            child_key = main_key[:-1] if main_key.endswith("s") else None
            error_text = ""

            if child_key:
                error_value = jresp[main_key][child_key]
                if "Messages" in error_value:
                    if "Description" in error_value["Messages"]:
                        error_text += f"{error_value['Messages']['Description']} : "
                    if "ErrorFields" in error_value["Messages"]:
                        errors = error_value["Messages"]["ErrorFields"]
                        if not isinstance(errors, list):
                            errors = [errors]
                        for error in errors:
                            if "ErrorField" in error:
                                error_text += f"FIELD {camel_to_snake(error['ErrorField']['FieldName'])}"
                                error_text += (
                                    f" - {error['ErrorField']['ErrorMessage']}"
                                )
            else:
                error_text = str(jresp)

            raise ApiFieldException(f"API returned error: {error_text}")


class _Service:
    endpoint: str = "/ServiceAvailability.json"
    _company: Address
    _api: _BaseApi

    def __init__(self, api: _BaseApi, company: Address):
        self._company = company
        self._api = api

    def get_shipping_services(
        self,
        delivery_postal_code: str,
        items: Union[Item, List[Item]],
        delivery_country_code: Optional[str] = "GB",
        is_fragile: Optional[bool] = False,
        order_value: Optional[int] = None,
        collection_date: Optional[datetime.date] = None,
        ready_at: Optional[time] = None,
        closed_at: Optional[time] = None,
        collection_postal_code: Optional[str] = None,
        collection_country_code: Optional[str] = None,
    ):
        """
        Retrieves available shipping services based on the input parameters.

        Args:
            delivery_postal_code (str): Postal code for the delivery address.
            items (Union[Item, List[Item]]): List of `Item` dataclasses, describing each item in the shipment.
            delivery_country_code (Optional[str]): Country code for the delivery address. Defaults to GB
            is_fragile (Optional[bool]): Is the parcel fragile?
            order_value (Optional[int]): Total value of the parcel in GBP.
            collection_date (str): Date the shipment will be collected. Defaults to today.
            ready_at (str): Time when the shipment will be ready for collection. Defaults to your main opening hours.
            closed_at (str): Time after which the shipment cannot be collected. Defaults to your main opening hours.
            collection_postal_code (str): Postal code for the collection address, defaults to your main collection address.
            collection_country_code (str): Country code for the collection address, defaults to your main collection address.

        Returns:
            JSON: Available shipping services (Mocked for this example).

        """
        if collection_date is None:
            collection_date = datetime.datetime.now().date()

        if ready_at is None:
            ready_at = self._company.open_from
        if closed_at is None:
            closed_at = self._company.open_to
        if collection_postal_code is None:
            collection_postal_code = self._company.postal_code
        if collection_country_code is None:
            collection_country_code = self._company.country_code

        if not isinstance(items, list):
            items = [items]
        number_of_pieces = len(items)

        # Construct the data dictionary
        data = {
            "orders": {
                "order": {
                    "collection_date": collection_date,
                    "ready_at": ready_at,
                    "closed_at": closed_at,
                    "collection": {
                        "postal_code": collection_postal_code,
                        "country_code": collection_country_code,
                    },
                    "delivery": {
                        "postal_code": delivery_postal_code,
                        "country_code": delivery_country_code,
                    },
                    "goods_info": {"goods_value": order_value, "fragile": is_fragile},
                    "shipment_details": {
                        "numberof_pieces": number_of_pieces,
                        "items": {"item": [item.to_dict() for item in items]},
                    },
                }
            }
        }

        # Validate the data using the Marshmallow schemas
        try:
            result = ServiceCheckSchema().dump(data)
        except ValidationError as err:
            print(f"Validation errors: {err}")
            return None

        api_response: List[Dict] = self._api.make_request(
            url=self.endpoint,
            method="POST",
            body=result,
            out_schema=CarrierSchema,
            output_base=["ServiceAvailability", "Services", "Service"],
        )
        return Services(api_response)


class _Order:
    endpoint: str = "/Orders.json"
    _company: Address  # Assuming Address is defined elsewhere
    _api: _BaseApi  # Assuming _BaseApi is defined elsewhere

    def __init__(self, api: _BaseApi, company: Address):
        self._company = company
        self._api = api

    def _validate_address(self, address, name: str):
        """
        Validates an address making sure it is the correct type.
        Args:
            address (Address): The address object
            name (str): The type of address

        Returns:

        """
        if address and not isinstance(address, Address):
            raise ValueError(f"{name} must be an `Address` object")

    def make_delivery(
        self,
        service_code: str,
        delivery_address: Address,
        items: Union[Item, List[Item]],
        ship_reference: Optional[str] = None,
        collection_date: Optional[datetime.date] = datetime.date.today(),
        delivery_instructions: Optional[str] = None,
        is_fragile: Optional[bool] = False,
        needs_increased_liability: Optional[bool] = False,
        order_value: Optional[float] = None,
        goods_description: Optional[str] = None,
    ):
        """
        Books a delivery.

        Args:
            service_code (str): The APC Service code to use
            delivery_address (Address): the address the goods are to be delivered to
            items (Union[Item, List[Item]]): A list or single `Item` which represents a single parcel.
            ship_reference (Optional[str]): Optional reference for the label. e.g Invoice number or customer reference.
            collection_date (Optional[date]): The date of the collection. Defaults to today
            delivery_instructions (Optional[str]): Optional delivery instructions for the parcel.
            is_fragile:
            needs_increased_liability:
            order_value:
            goods_description:

        Returns:

        """
        return self._make_shipment_base(
            is_collection=False,
            service_code=service_code,
            customer_address=delivery_address,
            collection_date=collection_date,
            items=items,
            ship_reference=ship_reference,
            delivery_instructions=delivery_instructions,
            is_fragile=is_fragile,
            needs_increased_liability=needs_increased_liability,
            order_value=order_value,
            goods_description=goods_description,
        )

    def make_collection(
        self,
        service_code: str,
        collection_address: Address,
        items: Union[Item, List[Item]],
        ship_reference: Optional[str] = None,
        collection_date: Optional[datetime.date] = datetime.date.today(),
        collection_instructions: Optional[str] = None,
        is_fragile: Optional[bool] = False,
        needs_increased_liability: Optional[bool] = False,
        order_value: Optional[float] = None,
        goods_description: Optional[str] = None,
    ):
        """
        Books a shipment.

        Args:
            service_code (str): The APC Service code to use
            collection_address (Address): the address the goods are to be delivered to
            items (Union[Item, List[Item]]): A list or single `Item` which represents a single parcel.
            ship_reference (Optional[str]): Optional reference for the label. e.g Invoice number or customer reference.
            collection_date (Optional[date]): The date of the collection. Defaults to today
            collection_instructions (Optional[str]): Optional delivery instructions for the parcel.
            collection_address (Optional[Address]): Collection address if differs from your business address
            is_fragile:
            needs_increased_liability:
            order_value:
            goods_description:

        Returns:

        """
        return self._make_shipment_base(
            is_collection=True,
            service_code=service_code,
            customer_address=collection_address,
            collection_date=collection_date,
            items=items,
            delivery_instructions=collection_instructions,
            ship_reference=ship_reference,
            collection_address=collection_address,
            is_fragile=is_fragile,
            needs_increased_liability=needs_increased_liability,
            order_value=order_value,
            goods_description=goods_description,
        )

    def _make_shipment_base(
        self,
        service_code: str,
        customer_address: Address,
        collection_date: datetime.date,
        items: Union[Item, List[Item]],
        is_collection: Optional[bool] = False,
        ship_reference: Optional[str] = None,
        delivery_instructions: Optional[str] = None,
        collection_address: Optional[Address] = None,
        is_fragile: Optional[bool] = False,
        needs_increased_liability: Optional[bool] = False,
        order_value: Optional[float] = None,
        goods_description: Optional[str] = None,
    ):
        """
        Books a shipment.

        Args:
            service_code (str): The APC Service code to use
            customer_address (Address): the address the goods are to be delivered to
            collection_date (date): The date of the collection
            items (Union[Item, List[Item]]): A list or single `Item` which represents a single parcel.
            is_collection (Optional[bool]): If true, it reverses the
            ship_reference (Optional[str]): Optional reference for the label. e.g Invoice number or customer reference.
            delivery_instructions (Optional[str]): Optional delivery instructions for the parcel.
            collection_address (Optional[Address]): Collection address if differs from your business address
            is_fragile:
            needs_increased_liability:
            order_value:
            goods_description:

        Returns:

        """
        # Centralized validation
        self._validate_address(collection_address, "Collection address")
        self._validate_address(customer_address, "Customer address")

        # sets the number of pieces from the length of the items list
        if not isinstance(items, list):
            items = [items]
        number_of_pieces = len(items)

        # Defaulting collection address to company address if not provided
        collection_address = collection_address or self._company.to_dict()

        # Prepare delivery address dictionary
        delivery_address = customer_address.to_dict()
        if delivery_instructions:
            delivery_address["delivery_instructions"] = delivery_instructions

        # Reverse collection and delivery address for collections
        if is_collection:
            delivery_address, collection_address = collection_address, delivery_address

        # Construct the data dictionary
        data = {
            "orders": {
                "order": {
                    "service_code": service_code,
                    "ship_reference": ship_reference,
                    "collection_date": collection_date,
                    "ready_at": self._company.open_from,
                    "closed_at": self._company.open_to,
                    "collection": collection_address,
                    "delivery": delivery_address,
                    "goods_info": {
                        "goods_description": goods_description,
                        "goods_value": order_value,
                        "fragile": is_fragile,
                        "increased_liability": needs_increased_liability,
                    },
                    "shipment_details": {
                        "number_of_pieces": number_of_pieces,
                        "items": {"item": [item.to_dict() for item in items]},
                    },
                }
            }
        }

        # Data Validation
        try:
            validated_data = ExtendedFullOrderSchema().dump(data)
        except ValidationError as err:
            raise ValidationError(f"Validation errors: {err}")

        # API call
        api_response: Dict = self._api.make_request(
            url=self.endpoint,
            method="POST",
            body=validated_data,
            output_base=["Orders", "Order"],
            out_schema=OrderOutputApiResponseSchema
        )

        # Return deserialized API response
        return api_response


class APC:
    """Base class for interacting with the APC Api.

    Attributes:
        company (Company): A dataclass object containing company details.
        username (str): The username for API access.
        password (str): The password for API access.
        is_sandbox (bool): A flag to specify if the API is in sandbox mode.
    """

    company: Address
    _api: _BaseApi
    service: _Service
    order: _Order

    def __init__(
        self, company: Address, username:Optional[str] = None, password: Optional[str] = None, is_sandbox: bool = False
    ):

        if not username:
            username = os.environ.get("APC_USERNAME")

        if not password:
            password = os.environ.get("APC_PASSWORD")

        self.company = company
        self._api = _BaseApi(
            username, password, is_sandbox
        )  # Create an instance of _BaseApi
        self.service = _Service(self._api, self.company)
        self.order = _Order(self._api, self.company)
        self.validate()

    def __repr__(self):
        """
        String representation of the APC API object.
        """
        return f"<APC API company='{self.company.company_name}'>"

    def validate(self):
        """
        Companies use the default address dataclass but need to have and opening and closing time which it doesn't
        validate for on its own.

        Returns:


        """
        if not self.company.open_from:
            raise ValueError(
                "The sending company must have an 'open from' time supplied as a python `time` object"
            )
        if not self.company.open_to:
            raise ValueError(
                "The sending company must have an 'open to' time supplied as a python `time` object"
            )
