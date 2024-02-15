from datetime import time
from apc import Address, APC, Item


# Create an Address object with all attributes, making sure it matches your company details exactly as APC have listed,
# if not it could be classified as a third party delivery.
comp = Address(
    company_name="Coleman Bros Wholesale",
    address_line1="Wallpapers Ltd",
    address_line2="Station Approach, WIndmill Lane",
    city="Cheshunt",
    county="Herts",
    postal_code="EN8 9AX",
    phone_number="01992 632533",
    open_from=time(9, 0),
    open_to=time(17, 0),
)

# Create an APC object with your company details and your APC credentials.
apc = APC(comp, "4426@apchertsovernight.com", "hol4426")

# Get the possible shipping services for a given postcode and a list of items.
services = apc.service.get_shipping_services("SG18 0NS", [Item(weight=1)])

# Filter the services to get the parcel services.
parcels = services.filter(services.item_type == "PARCEL")

# Get the service code for the first parcel service.
service_code = parcels[0]["service_code"]

# Create an Address object with the customer/delivery details.
customer_address = Address(
    "Lewis Ltd",
    "43 Stratton Way",
    "Biggleswade",
    "SG18 0NS",
    person_name="Lewis Morris",
    mobile_number="07554202635",
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

delivery
