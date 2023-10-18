import re

from marshmallow import Schema, fields, validate, validates, ValidationError, post_dump, post_load, EXCLUDE

from schemas.validation import validate_country_code


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
    number_of_pieces = fields.Int(data_key="NumberofPieces", required=True)
    items = fields.Nested(ItemsSchema(), data_key="Items", required=True)

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
    product_code = fields.Str(data_key='ProductCode')
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
