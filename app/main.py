from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

if __package__ in (None, ""):
    # Supports running this file directly (e.g., PyCharm "main.py" debug config).
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.resources.HarryPotterResource import (
        HarryPotterCharacter,
        HarryPotterCollection,
        HarryPotterResource,
    )
    from app.resources.CustomerResource import CustomerResource, Customer, CustomerCollection
    from app.resources.OrderResource import OrderResource, Order, OrderCollection
    from app.resources.OrderDetailsResource import OrderDetailsResource, OrderDetail, OrderDetailCollection
else:
    from .resources.HarryPotterResource import (
        HarryPotterCharacter,
        HarryPotterCollection,
        HarryPotterResource,
    )
    from .resources.CustomerResource import CustomerResource, Customer, CustomerCollection
    from .resources.OrderResource import OrderResource, Order, OrderCollection
    from .resources.OrderDetailsResource import OrderDetailsResource, OrderDetail, OrderDetailCollection


def _get_app_name() -> str:
    # Keep settings minimal in this starter; use environment variables when needed.
    return os.getenv("APP_NAME", "Starter FastAPI App")


app = FastAPI(title=_get_app_name(), version="0.1.0")
harry_potter_resource = HarryPotterResource()
customer_resource = CustomerResource()
order_resource = OrderResource()
order_details_resource = OrderDetailsResource()


class EchoRequest(BaseModel):
    message: str


@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/echo", tags=["echo"])
def echo(payload: EchoRequest) -> EchoRequest:
    return payload


@app.get("/harry-potter", tags=["harry-potter"])
def get_harry_potter_characters(
    first_name: str | None = None,
    last_name: str | None = None,
    house_name: str | None = None,
) -> HarryPotterCollection:
    template: dict = {}
    if first_name is not None:
        template["first_name"] = first_name
    if last_name is not None:
        template["last_name"] = last_name
    if house_name is not None:
        template["house_name"] = house_name
    return harry_potter_resource.get(template)


@app.get("/harry-potter/{character_id}", tags=["harry-potter"])
def get_harry_potter_character_by_id(character_id: str) -> HarryPotterCharacter:
    try:
        return harry_potter_resource.get_by_id(character_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/harry-potter", tags=["harry-potter"])
def create_harry_potter_character(new_data: HarryPotterCharacter) -> str:
    new_id = harry_potter_resource.post(new_data)
    return str(new_id)


@app.put("/harry-potter/{character_id}", tags=["harry-potter"])
def update_harry_potter_character(
    character_id: str, new_data: HarryPotterCharacter
) -> dict[str, int]:
    try:
        updated = harry_potter_resource.put(character_id, new_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"updated": updated}


@app.delete("/harry-potter/{character_id}", tags=["harry-potter"])
def delete_harry_potter_character(character_id: str) -> dict[str, int]:
    deleted = harry_potter_resource.delete(character_id)
    return {"deleted": deleted}

# Customer router:

@app.get("/customers", tags=["customers"])
def get_customers(
    customerName: str | None = None,
    country: str | None = None,
    city: str | None = None,
) -> CustomerCollection:
    # Build the template based on provided query params
    template = {}
    if customerName:
        template["customerName"] = customerName
    if country:
        template["country"] = country
    if city:
        template["city"] = city
    return customer_resource.get(template)

@app.post("/customers", tags=["customers"])
def create_customer(new_data: Customer) -> str:
    try:
        return customer_resource.post(new_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/customers/{customer_id}", tags=["customers"])
def get_customer_by_id(customer_id: int) -> Customer:
    try:
        return customer_resource.get_by_id(str(customer_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.put("/customers/{customer_id}", tags=["customers"])
def update_customer(customer_id: int, new_data: Customer) -> dict[str, int]:
    try:
        rows_updated = customer_resource.put(str(customer_id), new_data)
        if rows_updated == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"updated": rows_updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/customers/{customer_id}", tags=["customers"])
def delete_customer(customer_id: int) -> dict[str, int]:
    rows_deleted = customer_resource.delete(str(customer_id))
    return {"deleted": rows_deleted}

# Orders router:
@app.get("/orders", tags=["orders"])
def get_orders(
    status: str | None = None,
    customerNumber: int | None = None
) -> OrderCollection:
    template = {}
    if status:
        template["status"] = status
    if customerNumber:
        template["customerNumber"] = customerNumber
    return order_resource.get(template)

@app.post("/orders", tags=["orders"])
def create_order(new_data: Order) -> str:
    try:
        return order_resource.post(new_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/{order_id}", tags=["orders"])
def get_order_by_id(order_id: int) -> Order:
    try:
        return order_resource.get_by_id(str(order_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.put("/orders/{order_id}", tags=["orders"])
def update_order(order_id: int, new_data: Order) -> dict[str, int]:
    try:
        # Ensure the object matches the URL
        new_data.orderNumber = order_id
        rows_updated = order_resource.put(str(order_id), new_data)
        if rows_updated == 0:
            raise HTTPException(status_code=404, detail="Orders not found")
        return {"updated": rows_updated}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/orders/{order_id}", tags=["orders"])
def delete_order(order_id: int) -> dict[str, int]:
    rows_deleted = order_resource.delete(str(order_id))
    return {"deleted": rows_deleted}

# OrderDetails:
@app.get("/orderdetails", tags=["order_details"])
def get_order_details(orderNumber: int | None = None) -> OrderDetailCollection:
    template = {}
    if orderNumber:
        template["orderNumber"] = orderNumber
    return order_details_resource.get(template)

@app.post("/orderdetails", tags=["order_details"])
def create_order_detail(new_data: OrderDetail) -> str:
    try:
        return order_details_resource.post(new_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# url pattern: /orders/{order_id}/orderdetails/{product_id}
@app.get("/orders/{order_id}/orderdetails/{product_id}", tags=["order_details"])
def get_order_detail_item(order_id: int, product_id: str) -> OrderDetail:
    try:
        # Construct the composite key required by the Service
        composite_key = f"{order_id}|{product_id}"
        return order_details_resource.get_by_id(composite_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.put("/orders/{order_id}/orderdetails/{product_id}", tags=["order_details"])
def update_order_detail_item(order_id: int, product_id: str, new_data: OrderDetail) -> dict[str, int]:
    try:
        composite_key = f"{order_id}|{product_id}"
        new_data.orderNumber = order_id
        new_data.productCode = product_id
        
        rows = order_details_resource.put(composite_key, new_data)
        if rows == 0:
            raise HTTPException(status_code=404, detail="Order details not found")
        return {"updated": rows}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/orders/{order_id}/orderdetails/{product_id}", tags=["order_details"])
def delete_order_detail_item(order_id: int, product_id: str) -> dict[str, int]:
    composite_key = f"{order_id}|{product_id}"
    rows = order_details_resource.delete(composite_key)
    return {"deleted": rows}

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)

