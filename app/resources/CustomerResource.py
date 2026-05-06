from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService
from pydantic import BaseModel, Field

class Customer(BaseModel):
    customerNumber: int | None = None  
    
    customerName: str
    contactLastName: str
    contactFirstName: str
    phone: str
    addressLine1: str
    city: str
    country: str
    
    # Nullable fields using modern syntax
    addressLine2: str | None = None
    state: str | None = None
    postalCode: str | None = None
    salesRepEmployeeNumber: int | None = None
    creditLimit: float | None = None

class CustomerCollection(BaseModel):
    items: list[Customer] = Field(default_factory=list)

class CustomerResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        service_config: dict = {
            "table_name": str(cfg.get("table_name", "customers")),
            "primary_key_field": str(cfg.get("primary_key_field", "customerNumber")),
        }
        self._service = MySQLDataService(service_config)
    
    def get(self, template: dict) -> CustomerCollection:
        rows = self._service.retrieveByTemplate(template)
        return CustomerCollection(
            items=[Customer.model_validate(r) for r in rows]
        )
    
    def get_by_id(self, id: str) -> Customer:  # noqa: A002
        row = self._service.retrieveByPrimaryKey(str(id))
        if not row:
            raise ValueError(f"No customer with customerNumber {id!r}")
        return Customer.model_validate(row)

    def post(self, new_data: Customer) -> str:
        data = new_data.model_dump()
        id_value = data.get("customerNumber")
        if id_value is None or str(id_value).strip() == "":
            if data.get("customerNumber") is None:
                # LOGIC: Find the current max ID and add 1
                sql = "SELECT MAX(customerNumber) as max_id FROM customers"
                with self._service._get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        next_id = (row["max_id"] or 0) + 1
                        data["customerNumber"] = next_id
        return self._service.create(data)
    
    def delete(self, id: str) -> int:  # noqa: A002
        return self._service.deleteByPrimaryKey(str(id))

    def put(self, character_id: str, new_data: Customer) -> int:
        data = new_data.model_dump()
        data["customerNumber"] = int(character_id)
        return self._service.updateByPrimaryKey(character_id, data)


