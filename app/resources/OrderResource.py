from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService
from pydantic import BaseModel, Field
from datetime import date

class Order(BaseModel):
    orderNumber: int | None = None
    
    orderDate: date
    requiredDate: date
    shippedDate: date | None = None
    
    status: str
    comments: str | None = None
    customerNumber: int  # Foreign Key

class OrderCollection(BaseModel):
    items: list[Order] = Field(default_factory=list)

class OrderResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        service_config: dict = {
            "table_name": str(cfg.get("table_name", "orders")),
            "primary_key_field": str(cfg.get("primary_key_field", "orderNumber")),
        }
        self._service = MySQLDataService(service_config)

    def get(self, template: dict) -> OrderCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderCollection(
            items=[Order.model_validate(r) for r in rows]
        )

    def get_by_id(self, id: str) -> Order:
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(f"No order with orderNumber {id!r}")
        return Order.model_validate(row)

    def post(self, new_data: Order) -> str:
        data = new_data.model_dump()

        id_value = data.get("orderNumber")
        if id_value is None or str(id_value).strip() == "":
            if data.get("orderNumber") is None:
                # LOGIC: Find the current max ID and add 1
                sql = "SELECT MAX(orderNumber) as max_order_num FROM orders"
                with self._service._get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(sql)
                        row = cursor.fetchone()
                        next_id = (row["max_order_num"] or 0) + 1
                        data["orderNumber"] = next_id
        return self._service.create(data)

    def put(self, id: str, new_data: Order) -> int:
        data = new_data.model_dump()
        data["orderNumber"] = int(id)
        return self._service.updateByPrimaryKey(id, data)

    def delete(self, id: str) -> int:
        return self._service.deleteByPrimaryKey(id)