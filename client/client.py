import base64
import datetime
from datetime import time
from typing import List, Dict, Optional, Any

import requests
from marshmallow import ValidationError, Schema
from requests import RequestException

from schemas.dataclasses import Item, Address
from schemas.schemas import ServiceCheckSchema, CarrierSchema


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
        schema: Optional[Schema] = None,
    ) -> Dict[str, Any]:
        """
        The main calling function to get from the APC Api.

        Args:
            url (str): The endpoint URL.
            method (str): One of GET, POST, PUT. Defaults to "GET".
            url_params (Optional[Dict[str, Any]]): A dictionary of URL parameters.
            body (Optional[Dict[str, Any]]): A dictionary containing the body request.
            schema (Optional[Schema]): A schema to serialize the response from the API.

        Returns:
            Dict: The response from the API, optionally serialized via a schema.
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
            if schema:
                try:
                    return schema().load(response.json())
                except ValidationError as ve:
                    raise ValueError(f"Schema validation error: {ve}")

            jresp = response.json()
            if (
                "ServiceAvailability" in jresp
                and "Services" in jresp["ServiceAvailability"]
                and "Service" in jresp["ServiceAvailability"]["Services"]
            ):
                return CarrierSchema().load(
                    jresp["ServiceAvailability"]["Services"]["Service"], many=True
                )
            else:
                return {}
        except RequestException as re:
            raise ConnectionError(f"Request failed: {re}")


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
        number_of_pieces: int,
        items: List[Item],
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
            number_of_pieces (int): The number of pieces in the shipment.
            items (List[Item]): List of `Item` dataclasses, describing each item in the shipment.
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

        if number_of_pieces != len(items):
            raise ValueError(
                "The number of pieces must match the number of items supplied."
            )

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

        api_response = self._api.make_request(
            url=self.endpoint, method="POST", body=result
        )
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

    def __init__(
        self, company: Address, username: str, password: str, is_sandbox: bool = False
    ):
        self.company = company
        self._api = _BaseApi(
            username, password, is_sandbox
        )  # Create an instance of _BaseApi
        self.service = _Service(self._api, self.company)
        self.validate()

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


comp = Address(
    "Lewis Ltd", "Station Approach", "Cheshunt", "EN8 9AX", time(9, 0), time(17, 0)
)
apc = APC(comp, "4426@apchertsovernight.com", "hol4426")

services = apc.service.get_shipping_services("SG18 0NS", 1, [Item(weight=1)])
print(services)
