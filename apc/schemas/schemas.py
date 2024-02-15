from marshmallow import Schema, fields, validate, validates, ValidationError, post_dump, post_load, EXCLUDE, pre_load

from apc.schemas.validation import validate_country_code


# Function to check if country code is valid


class ItemSchema(Schema):
    type = fields.Str(data_key="Type", default="ALL")
    weight = fields.Float(data_key="Weight",
                          required=True,
                          validate=validate.Range(min=0, max=100, error="You must supply a weight greater than 0."))
    length = fields.Float(data_key="Length")
    width = fields.Float(data_key="Width")
    height = fields.Float(data_key="Height")
    value = fields.Float(data_key="Value")


class ItemsSchema(Schema):
    item = fields.List(fields.Nested(ItemSchema), data_key="Item", required=True)

    @post_dump
    def handle_single_item(self, data, **kwargs):
        if len(data['Item']) == 1:
            data['Item'] = data['Item'][0]
        return data
class ShipmentDetailsSchema(Schema):
    number_of_pieces = fields.Int(data_key="NumberOfPieces", required=True)
    items = fields.Nested(ItemsSchema(), data_key="Items", required=True)
    volumetric_weight = fields.Float(data_key="VolumetricWeight", required=True, allow_none=True)
    total_weight = fields.Float(data_key="TotalWeight", required=True, allow_none=True)


class AddressSchema(Schema):
    postal_code = fields.Str(data_key="PostalCode", required=True, validate=validate.Regexp(
        r"^(([A-Z]{1,2}[0-9][A-Z0-9]?|ASCN|STHL|TDCU|BBND|[BFS]IQQ|PCRN|TKCA) ?[0-9][A-Z]{2}|BFPO ?[0-9]{1,4}|(KY[0-9]|MSR|VG|AI)[ -]?[0-9]{4}|[A-Z]{2} ?[0-9]{2}|GE ?CX|GIR ?0A{2}|SAN ?TA1)$"),
                            error="Invalid Postal Code format.")
    country_code = fields.Str(data_key="CountryCode", required=True, validate=validate.Length(equal=2))

    @validates("country_code")
    def validate_country(self, value):
        if not validate_country_code(value):
            raise ValidationError(f"Invalid country code: {value}")

class GoodsInfoSchema(Schema):
    order_value = fields.Float(data_key="GoodsValue")
    fragile = fields.Bool(data_key="Fragile")

class OrderSchema(Schema):
    collection_date = fields.Date(data_key="CollectionDate", required=True, format="%d/%m/%Y")
    ready_at = fields.Time(data_key="ReadyAt", required=True, format="%H:%M")
    closed_at = fields.Time(data_key="ClosedAt", required=True, format="%H:%M")
    collection = fields.Nested(AddressSchema, data_key="Collection", required=True)
    delivery = fields.Nested(AddressSchema, data_key="Delivery", required=True)
    goods_info = fields.Nested(GoodsInfoSchema, data_key="GoodsInfo")
    shipment_details = fields.Nested(ShipmentDetailsSchema, data_key="ShipmentDetails", required=True)

class OrdersSchema(Schema):
    order = fields.Nested(OrderSchema, data_key="Order", required=True)

class ServiceCheckSchema(Schema):
    orders = fields.Nested(OrdersSchema, data_key="Orders", required=True)

class CarrierSchema(Schema):

    class Meta:
        unknown = EXCLUDE  # This line will ignore unknown fields during loading

    carrier = fields.Str(data_key='Carrier')
    service_name = fields.Str(data_key='ServiceName')
    service_code = fields.Str(data_key='ProductCode')
    min_transit_days = fields.Int(data_key='MinTransitDays')
    max_transit_days = fields.Int(data_key='MaxTransitDays')
    tracked = fields.Boolean(data_key='Tracked')
    signed = fields.Boolean(data_key='Signed')
    max_compensation = fields.Float(data_key='MaxCompensation')
    max_item_length = fields.Int(data_key='MaxItemLength')
    max_item_width = fields.Int(data_key='MaxItemWidth')
    max_item_height = fields.Int(data_key='MaxItemHeight')
    item_type = fields.Str(data_key='ItemType')
    delivery_group = fields.Str(data_key='DeliveryGroup')
    collection_date = fields.DateTime(data_key='CollectionDate', format="%d/%m/%Y")
    estimated_delivery_date = fields.DateTime(data_key='EstimatedDeliveryDate', format="%d/%m/%Y")
    latest_booking_date_time = fields.DateTime(data_key='LatestBookingDateTime', format="%d/%m/%Y %H:%M")
    rule_match = fields.DateTime(data_key='@RuleMatch', dump_only=True)
    rule_match_name = fields.DateTime(data_key='@RuleMatchName', dump_only=True)

    @post_load
    def remove_missing_fields(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class ContactSchema(Schema):
    person_name = fields.Str(data_key="PersonName", required=True)
    phone_number = fields.Str(data_key="PhoneNumber", allow_none=True)
    email = fields.Email(data_key="Email", validate=validate.Email(error="Not a valid email address"), allow_none=True)
    mobile_number = fields.Str(data_key="MobileNumber")



class ExtendedItemSchemaSchema(ItemSchema):  # Inherits from your existing GoodsInfoSchema

    item_number = fields.Int(data_key="ItemNumber", load_only=True)
    reference = fields.Str(data_key="Reference", load_only=True, allow_none=True)
    tracking_number = fields.Str(data_key="TrackingNumber", load_only=True)

class ExtendedItemsSchema(ItemsSchema):
    item = fields.List(fields.Nested(ExtendedItemSchemaSchema), data_key="Item", required=True)

    @pre_load
    def ensure_item_is_list(self, data, **kwargs):
        item = data.get("Item")
        if item is not None and not isinstance(item, list):
            data["Item"] = [item]
        return data

    @post_dump
    def handle_single_item(self, data, **kwargs):
        if len(data['Item']) == 1:
            data['Item'] = data['Item'][0]
        return data

class ExtendedShipmentDetailsSchema(ShipmentDetailsSchema):
    number_of_pieces = fields.Int(data_key="NumberOfPieces", required=True)
    items = fields.Nested(ExtendedItemsSchema(), data_key="Items", required=True)


class ExtendedAddressSchema(AddressSchema):  # Inherits from your existing AddressSchema
    company_name = fields.Str(data_key="CompanyName")
    address_line1 = fields.Str(data_key="AddressLine1", required=True)
    address_line2 = fields.Str(data_key="AddressLine2", allow_none=True)
    city = fields.Str(data_key="City", required=True)
    county = fields.Str(data_key="County", allow_none=True)
    county_name = fields.Str(data_key="CountryName", allow_none=True)
    safe_place = fields.Str(data_key="Safeplace", allow_none=True)
    contact = fields.Nested(ContactSchema, data_key="Contact")
    instructions = fields.Str(data_key="Instructions", allow_none=True)

class ExtendedGoodsInfoSchema(GoodsInfoSchema):  # Inherits from your existing GoodsInfoSchema
    goods_description = fields.Str(data_key="GoodsDescription")
    security = fields.Bool(data_key="Security")
    increased_liability = fields.Bool(data_key="IncreasedLiability")
    premium = fields.Bool(data_key="Premium")
    non_conveyorable = fields.Bool(data_key="NonConv")
    premium_insurance = fields.Bool(data_key="PremiumInsurance")
    charge_on_delivery = fields.Float(data_key="ChargeOnDelivery")


class ExtendedOrderSchema(OrderSchema):  # Inherits from your existing OrderSchema
    service_code = fields.Str(data_key="ProductCode", required=True)
    ship_reference = fields.Str(data_key="Reference", required=True)
    collection = fields.Nested(ExtendedAddressSchema, data_key="Collection", required=True)
    delivery = fields.Nested(ExtendedAddressSchema, data_key="Delivery", required=True)
    goods_info = fields.Nested(ExtendedGoodsInfoSchema, data_key="GoodsInfo")
    shipment_details = fields.Nested(ShipmentDetailsSchema, data_key="ShipmentDetails", required=True)

class ExtendedOrdersSchema(Schema):
    order = fields.Nested(ExtendedOrderSchema, data_key="Order", required=True)

class ExtendedFullOrderSchema(Schema):
    orders = fields.Nested(ExtendedOrdersSchema, data_key="Orders", required=True)


class OrderOutputMessagesSchema(Schema):
    code = fields.Str(data_key="Code")
    description = fields.Str(data_key="Description")

class OrderOutputDepotsSchema(Schema):
    request_depot = fields.Str(data_key="RequestDepot")
    collecting_depot = fields.Str(data_key="CollectingDepot")
    delivery_depot = fields.Str(data_key="DeliveryDepot")
    route = fields.Str(data_key="Route")
    is_scottish = fields.Bool(data_key="IsScottish")
    zone = fields.Str(data_key="Zone")
    delivery_route = fields.Str(data_key="DeliveryRoute")
    seg_code = fields.Str(data_key="SegCode")
    presort = fields.Str(data_key="Presort")
    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields during loading

class OrderOutputApiResponseSchema(Schema):

    class Meta:
        unknown = EXCLUDE  # Ignore unknown fields during loading

    messages = fields.Nested(OrderOutputMessagesSchema, data_key="Messages")
    collection_date = fields.Date(data_key="CollectionDate", allow_none=True,format="%d/%m/%Y")
    open_from = fields.Time(data_key="ReadyAt", allow_none=True,format="%H:%M")
    open_to = fields.Time(data_key="ClosedAt", allow_none=True,format="%H:%M")
    delivery_date = fields.Date(data_key="DeliveryDate", allow_none=True,format="%d/%m/%Y")
    product_code = fields.Str(data_key="ProductCode")
    network_name = fields.Str(data_key="NetworkName")
    item_option = fields.Str(data_key="ItemOption")
    order_number = fields.Str(data_key="OrderNumber")
    way_bill = fields.Str(data_key="WayBill")
    barcode = fields.Str(data_key="Barcode")
    reference = fields.Str(data_key="Reference")
    adult_signature = fields.Bool(data_key="AdultSignature", allow_none=True)
    depots = fields.Nested(OrderOutputDepotsSchema, data_key="Depots")
    collection = fields.Nested(ExtendedAddressSchema, data_key="Collection")
    delivery = fields.Nested(ExtendedAddressSchema, data_key="Delivery")
    goods_info = fields.Nested(ExtendedGoodsInfoSchema, data_key="GoodsInfo")
    shipment_details = fields.Nested(ExtendedShipmentDetailsSchema, data_key="ShipmentDetails")
