from .AbstractBaseResource import AbstractBaseResource
from ..services.MySQLDataService import MySQLDataService
from pydantic import BaseModel, Field

class OrderDetail(BaseModel):
    orderNumber: int
    productCode: str
    quantityOrdered: int
    priceEach: float
    orderLineNumber: int

class OrderDetailCollection(BaseModel):
    items: list[OrderDetail]

class OrderDetailsResource(AbstractBaseResource):
    def __init__(self, config: dict | None = None) -> None:
        cfg = dict(config or {})
        super().__init__(cfg)
        service_config: dict = {
            "table_name": str(cfg.get("table_name", "orderdetails")),
            "primary_key_field": str(cfg.get("primary_key_field", "orderNumber, productCode")),
        }
        self._service = MySQLDataService(service_config)
    
    def post(self, new_data: OrderDetail) -> str:
        data = new_data.model_dump()
        return self._service.create(data)
    
    def get(self, template: dict) -> OrderDetailCollection:
        rows = self._service.retrieveByTemplate(template)
        return OrderDetailCollection(
            items=[OrderDetail.model_validate(r) for r in rows]
        )

    def get_by_id(self, id: str) -> OrderDetail:
        """
        We expects a composite key string like "10100|S10_1678"
        """
        row = self._service.retrieveByPrimaryKey(id)
        if not row:
            raise ValueError(f"No order detail found for key {id}")
        return OrderDetail.model_validate(row)
    
    def post(self, new_data: OrderDetail) -> str:
        data = new_data.model_dump()
        return self._service.create(data)

    def delete(self, id: str) -> int:
        """
        Expects "10100|S10_1678"
        """
        return self._service.deleteByPrimaryKey(id)

    def put(self, character_id: str, new_data: OrderDetail) -> int:
        """
        Expects character_id="10100|S10_1678"
        """
        data = new_data.model_dump()
        return self._service.updateByPrimaryKey(character_id, data)



