import unittest
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
EXISTING_CUSTOMER_ID = 103 
EXISTING_PRODUCT_CODE = "S18_3482"


class TestAPI(unittest.TestCase):

    # customers

    def test_1_get_customers_list(self):
        """fetch list of customers"""
        response = requests.get(f"{BASE_URL}/customers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)

    def test_2_create_customer_validation_error(self):
        """error: create customer missing required field"""
        payload = {"city": "New York"} # Missing customerName
        response = requests.post(f"{BASE_URL}/customers", json=payload)
        self.assertEqual(response.status_code, 422) # Validation Error

    def test_3_customer_lifecycle(self):
        """Normal: Create -> Get -> Update -> Delete"""
        # create
        payload = {
            "customerNumber": 2021,
            "customerName": "Unit Test Corp",
            "contactLastName": "Tester",
            "contactFirstName": "Joe",
            "phone": "555-0199",
            "addressLine1": "123 Code Lane",
            "city": "Testville",
            "country": "USA"
        }
        create_res = requests.post(f"{BASE_URL}/customers", json=payload)
        self.assertEqual(create_res.status_code, 200)
        new_id = create_res.json()
        print(f"   [Info] Created Customer ID: {new_id}")

        # get
        get_res = requests.get(f"{BASE_URL}/customers/{new_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["customerName"], "Unit Test Corp")
        self.assertEqual(get_res.json()["city"], "Testville")

        # update
        update_payload = payload.copy()
        update_payload["customerName"] = "Updated Corp"
        put_res = requests.put(f"{BASE_URL}/customers/{new_id}", json=update_payload)
        self.assertEqual(put_res.status_code, 200)

        # verify get
        get_res = requests.get(f"{BASE_URL}/customers/{new_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["customerName"], "Updated Corp")
        
        # D. DELETE
        del_res = requests.delete(f"{BASE_URL}/customers/{new_id}")
        self.assertEqual(del_res.status_code, 200)

        # E. VERIFY DELETE (Error Case)
        check_res = requests.get(f"{BASE_URL}/customers/{new_id}")
        self.assertEqual(check_res.status_code, 404)

    def test_4_get_customer_404(self):
        """Error: Get non-existent customer"""
        response = requests.get(f"{BASE_URL}/customers/99999999")
        self.assertEqual(response.status_code, 404)

    # ==========================================
    # 2. ORDERS
    # ==========================================

    def test_5_get_orders_list(self):
        """Normal: List orders"""
        response = requests.get(f"{BASE_URL}/orders")
        self.assertEqual(response.status_code, 200)

    def test_6_order_lifecycle(self):
        """Normal: Create -> Get -> Update -> Delete"""
        # A. CREATE (Requires valid customerNumber)
        payload = {
            "orderDate": "2025-01-01",
            "requiredDate": "2025-01-10",
            "status": "In Process",
            "customerNumber": EXISTING_CUSTOMER_ID
        }
        create_res = requests.post(f"{BASE_URL}/orders", json=payload)
        self.assertEqual(create_res.status_code, 200)
        new_id = create_res.json()
        print(f"   [Info] Created Order ID: {new_id}")

        # B. GET
        get_res = requests.get(f"{BASE_URL}/orders/{new_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["status"], "In Process")

        # C. UPDATE
        payload["status"] = "Shipped"
        put_res = requests.put(f"{BASE_URL}/orders/{new_id}", json=payload)
        self.assertEqual(put_res.status_code, 200)

        # D. DELETE
        del_res = requests.delete(f"{BASE_URL}/orders/{new_id}")
        self.assertEqual(del_res.status_code, 200)
    
    def test_7_update_order_404(self):
        """Error: Update non-existent order"""
        payload = {
            "orderDate": "2025-01-01", 
            "requiredDate": "2025-01-10", 
            "status": "In Process", 
            "customerNumber": EXISTING_CUSTOMER_ID
        }
        response = requests.put(f"{BASE_URL}/orders/9999213", json=payload)
        self.assertEqual(response.status_code, 404)

    # ==========================================
    # 3. ORDER DETAILS (Composite Key)
    # ==========================================

    def test_8_order_detail_lifecycle(self):
        """Normal: Create -> Get -> Update -> Delete (Composite)"""
        
        # Setup: We need a temporary Order to hold the detail
        order_payload = {
            "orderDate": "2025-05-05",
            "requiredDate": "2025-05-10",
            "status": "In Process",
            "customerNumber": EXISTING_CUSTOMER_ID
        }
        order_id = requests.post(f"{BASE_URL}/orders", json=order_payload).json()
        product_id = EXISTING_PRODUCT_CODE
        
        try:
            # A. CREATE DETAIL
            detail_payload = {
                "orderNumber": int(order_id),
                "productCode": product_id,
                "quantityOrdered": 50,
                "priceEach": 100.00,
                "orderLineNumber": 1
            }
            create_res = requests.post(f"{BASE_URL}/orderdetails", json=detail_payload)
            self.assertEqual(create_res.status_code, 200)

            # B. GET SPECIFIC (Composite URL)
            url = f"{BASE_URL}/orders/{order_id}/orderdetails/{product_id}"
            get_res = requests.get(url)
            self.assertEqual(get_res.status_code, 200)
            self.assertEqual(get_res.json()["quantityOrdered"], 50)

            # C. UPDATE
            detail_payload["quantityOrdered"] = 99
            put_res = requests.put(url, json=detail_payload)
            self.assertEqual(put_res.status_code, 200)

            # D. DELETE
            del_res = requests.delete(url)
            self.assertEqual(del_res.status_code, 200)
            
            # E. CONFIRM GONE
            check = requests.get(url)
            self.assertEqual(check.status_code, 404)

        finally:
            # Cleanup the temporary order
            requests.delete(f"{BASE_URL}/orders/{order_id}")

    def test_9_create_detail_invalid_fk(self):
        """Error: Create detail for non-existent Order"""
        payload = {
            "orderNumber": 99999999, 
            "productCode": EXISTING_PRODUCT_CODE,
            "quantityOrdered": 10,
            "priceEach": 10.00,
            "orderLineNumber": 1
        }
        # This should fail at DB level (Foreign Key Constraint, which is invalid input) -> 400
        response = requests.post(f"{BASE_URL}/orderdetails", json=payload)
        self.assertEqual(response.status_code, 400)

    # Test customer bad request
    def test_customer_missing_required_field(self):
        """
        Expect 422: Trying to create a customer without 'customerName'.
        """
        payload = {
            "contactLastName": "Doe",
            "phone": "555-0000",
            "city": "Nowhere"
            # MISSING: customerName
        }
        response = requests.post(f"{BASE_URL}/customers", json=payload)
        
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())
        print(f"\n[Customer] Missing Field Test: {response.status_code} OK")

    def test_customer_invalid_data_type(self):
        """
        Expect 422: Sending a String for 'creditLimit' which expects a Float/Int.
        """
        payload = {
            "customerName": "Bad Type Corp",
            "contactLastName": "Doe",
            "contactFirstName": "John",
            "phone": "555-1234",
            "addressLine1": "123 Street",
            "city": "City",
            "country": "USA",
            "creditLimit": "ONE MILLION DOLLARS"  # <--- INVALID TYPE
        }
        response = requests.post(f"{BASE_URL}/customers", json=payload)
        
        self.assertEqual(response.status_code, 422)
        print(f"[Customer] Invalid Type Test: {response.status_code} OK")

    # ==========================================
    # 2. ORDERS (Foreign Key Errors -> 400/500)
    # ==========================================

    def test_create_order_unknown_customer(self):
        """
        Expect 400: Creating an order for a customer ID that doesn't exist.
        This triggers a Foreign Key Constraint failure in MySQL.
        """
        payload = {
            "orderDate": "2025-01-01",
            "requiredDate": "2025-01-10",
            "status": "In Process",
            "customerNumber": 99999999  # <--- NON-EXISTENT CUSTOMER
        }
        response = requests.post(f"{BASE_URL}/orders", json=payload)
        
        # This should be 400 (Bad Request)
        self.assertEqual(response.status_code, 400)
        print(f"[Order] Invalid FK Test: Returned {response.status_code}")

    def test_update_order_invalid_date_format(self):
        """
        Expect 422: Sending 'INVALID-DATE' instead of YYYY-MM-DD.
        """
        payload = {
            "orderDate": "THIS-IS-NOT-A-DATE", # <--- INVALID DATE
            "requiredDate": "2025-01-10",
            "status": "In Process",
            "customerNumber": EXISTING_CUSTOMER_ID
        }
        # Need a valid order ID to try updating. We'll just use a dummy one 
        # because validation happens BEFORE the DB lookup.
        response = requests.put(f"{BASE_URL}/orders/10100", json=payload)
        
        self.assertEqual(response.status_code, 422)
        print(f"[Order] Invalid Date Test: {response.status_code} OK")

    # ==========================================
    # 3. ORDER DETAILS (Integrity Errors -> 400)
    # ==========================================

    def test_create_detail_unknown_product(self):
        """
        Expect 400: Adding a product that does not exist to an order.
        """
        # First, create a temporary valid order to hold the detail
        order_payload = {
            "orderDate": "2025-01-01", "requiredDate": "2025-01-10",
            "status": "In Process", "customerNumber": EXISTING_CUSTOMER_ID
        }
        order_id = requests.post(f"{BASE_URL}/orders", json=order_payload).json()

        try:
            detail_payload = {
                "orderNumber": order_id,
                "productCode": "INVALID_CODE_999", # NON-EXISTENT PRODUCT
                "quantityOrdered": 10,
                "priceEach": 50.00,
                "orderLineNumber": 1
            }
            response = requests.post(f"{BASE_URL}/orderdetails", json=detail_payload)
            
            self.assertEqual(response.status_code, 400)
            print(f"[OrderDetail] Invalid Product Test: Returned {response.status_code}")

        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/orders/{order_id}")

    def test_create_duplicate_detail(self):
        """
        Expect 400: Adding the SAME product to the SAME order twice.
        This violates the Composite Primary Key (orderNumber, productCode).
        """
        # Setup: Create order
        order_payload = {
            "orderDate": "2025-01-01", "requiredDate": "2025-01-10",
            "status": "In Process", "customerNumber": EXISTING_CUSTOMER_ID
        }
        order_id = requests.post(f"{BASE_URL}/orders", json=order_payload).json()

        try:
            detail_payload = {
                "orderNumber": order_id,
                "productCode": EXISTING_PRODUCT_CODE,
                "quantityOrdered": 10,
                "priceEach": 50.00,
                "orderLineNumber": 1
            }
            
            # 1. First Insert (Should Succeed)
            res1 = requests.post(f"{BASE_URL}/orderdetails", json=detail_payload)
            self.assertEqual(res1.status_code, 200)
            
            # 2. Second Insert (Should Fail - Duplicate Key)
            res2 = requests.post(f"{BASE_URL}/orderdetails", json=detail_payload)
            self.assertEqual(res2.status_code, 400)
            print(f"[OrderDetail] Duplicate Entry Test: Returned {res2.status_code}")

        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/orders/{order_id}")

if __name__ == "__main__":
    unittest.main()
