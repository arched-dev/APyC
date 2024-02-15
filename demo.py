import os
from datetime import time
from pprint import pprint

from dotenv import load_dotenv

from apc import Address, APC, Item
load_dotenv()

# Create an Address object with all attributes, making sure it matches your company details exactly as APC have listed,
# if not it could be classified as a third party delivery.
comp = Address(
    company_name="My Test Co",
    address_line1="1 Test Road",
    address_line2="",
    city="Testington",
    county="Testfordshire",
    postal_code="EN1 1LR",
    phone_number="01775 659565",
    open_from=time(9, 0),
    open_to=time(17, 0),
)

# Create an APC object with your company details, your APC credentials are read from the environment with the following
# keys: APC_USERNAME, APC_PASSWORD
apc = APC(comp)

# You can also pass the credentials directly to the APC object with the `username` and `password` arguments.
# apc = APC(comp, username="your_apc_username", password="your_apc_password")

# Get the possible shipping services for a given postcode and a list of items.
order_items = [Item(weight=1)]
services = apc.service.get_shipping_services("PO16 7GZ", items=order_items)

# Filter the services to get the parcel services.
parcels = services.filter(services.item_type == "PARCEL")

# print all services
pprint(parcels)

# Get the service code for the first parcel service.
service_code = parcels[0]["service_code"]

# Create an Address object with the customer/delivery details.
customer_address = Address(
    "Test Recipient Ltd",
    "1 Test Lane",
    "Tester",
    "PO16 7GZ",
    person_name="Mr Test",
    mobile_number="07553656595",
)

# get the finalised `delivery` object
delivery = apc.order.make_delivery(
    service_code,
    customer_address,
    items=[Item(weight=1)],
    ship_reference="INV12565",
    delivery_instructions="Please leave in side porch",
    order_value=250.00,
    goods_description="Baz's foo bars",
)

pprint(delivery)
