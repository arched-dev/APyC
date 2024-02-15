from typing import List, Callable, Union

from marshmallow import Schema

from apc.schemas.schemas import CarrierSchema


class QueryableAttribute:
    def __init__(self, name: str) -> None:
        self.name = name

    def _normalize(self, value):
        return value.lower() if isinstance(value, str) else value

    def __eq__(self, other: Union[int, str, bool]) -> Callable:
        return lambda obj: self._normalize(obj.get(self.name)) == self._normalize(other)

    def __ne__(self, other: Union[int, str, bool]) -> Callable:
        return lambda obj: self._normalize(obj.get(self.name)) != self._normalize(other)

    def __lt__(self, other: Union[int, str, bool]) -> Callable:
        return lambda obj: self._normalize(obj.get(self.name)) < self._normalize(other)

    def __le__(self, other: Union[int, str, bool]) -> Callable:
        return lambda obj: self._normalize(obj.get(self.name)) <= self._normalize(other)

    def __gt__(self, other: Union[int, str, bool]) -> Callable:
        return lambda obj: self._normalize(obj.get(self.name)) > self._normalize(other)

    def __ge__(self, other: Union[int, str, bool]) -> Callable:
        return lambda obj: self._normalize(obj.get(self.name)) >= self._normalize(other)

    def like(self, pattern: str) -> Callable:
        """
        Check if the attribute value is like the given pattern.
        Args:
            pattern (str): The pattern to check against.

        Returns:
            A function that returns True if the attribute value is like the given pattern, False otherwise.
        """
        return lambda obj: self._normalize(pattern) in self._normalize(obj.get(self.name, ''))

    def startswith(self, prefix: str) -> Callable:
        """
        Check if the attribute value starts with the given prefix.
        Args:
            prefix (str): The prefix to check against.
        Returns:
            A function that returns True if the attribute value starts with the given prefix, False otherwise.
        """
        return lambda obj: self._normalize(obj.get(self.name, '')).startswith(self._normalize(prefix))

    def endswith(self, suffix: str) -> Callable:
        """
        Check if the attribute value ends with the given suffix.
        Args:
            suffix (str): The suffix to check against.

        Returns:
            A function that returns True if the attribute value ends with the given suffix, False otherwise.
        """
        return lambda obj: self._normalize(obj.get(self.name, '')).endswith(self._normalize(suffix))

    def is_null(self) -> Callable:
        """
        Check if the attribute value is null.
        Returns:
            A function that returns True if the attribute value is null, False otherwise.

        """
        return lambda obj: obj.get(self.name) is None

    def is_not_null(self) -> Callable:
        """
        Check if the attribute value is not null.
        Returns:
            A function that returns True if the attribute value is not null, False otherwise.
        """
        return lambda obj: obj.get(self.name) is not None

class Query:

    def __init__(self, records: List[dict], schema: Schema) -> None:
        """Initialize a Query object.

        Args:
            records (List[dict]): The records to query.
        """
        self.records = records
        self.set_queryable_attributes(schema)

    def set_queryable_attributes(self, schema: Schema) -> None:
        for field_name in schema().fields.keys():
            setattr(self, field_name, QueryableAttribute(field_name))

    def __getattr__(self, attr: str) -> QueryableAttribute:
        """Dynamic attribute access.

        Args:
            attr (str): Attribute name.

        Returns:
            QueryableAttribute: Queryable attribute object.
        """
        return QueryableAttribute(attr)

    def __getitem__(self, index: int) -> dict:
        """Get an item from the records' list by its index."""
        return self.records[index]

    def __repr__(self) -> str:
        """String representation of the query object."""
        return repr(self.records)

    def filter(self, *conditions: Callable) -> "Query":
        """
        Filter the list of records by the given conditions.

        Args:
            *conditions: List of conditions to filter by.

        Returns:
            A new instance of the class containing the filtered records.
        """
        filtered = self.records
        for condition in conditions:
            filtered = [record for record in filtered if condition(record)]
        return self.__class__(filtered)

class Services(Query):
    """Class representing a list of services."""
    duration: QueryableAttribute
    carrier: QueryableAttribute
    service_name: QueryableAttribute
    service_code: QueryableAttribute
    min_transit_days: QueryableAttribute
    max_transit_days: QueryableAttribute
    tracked: QueryableAttribute
    signed: QueryableAttribute
    max_compensation: QueryableAttribute
    max_item_length: QueryableAttribute
    max_item_width: QueryableAttribute
    max_item_height: QueryableAttribute
    item_type: QueryableAttribute
    delivery_group: QueryableAttribute
    collection_date: QueryableAttribute
    estimated_delivery_date: QueryableAttribute
    latest_booking_date_time: QueryableAttribute
    def __init__(self, services: List[dict]):
        super().__init__(services, CarrierSchema)
