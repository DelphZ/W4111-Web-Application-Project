import os
import pymysql
import pymysql.err
from typing import List, Dict, Union, Optional
from dotenv import load_dotenv
from pathlib import Path
from .AbstractBaseDataService import AbstractBaseDataService

load_dotenv()

class MySQLDataService(AbstractBaseDataService):
    def __init__(self, config: dict = None):
        super().__init__(config)
        if config is None:
            config = {}
        self.table = config.get("table_name")
        pk_config = config.get("primary_key_field", "id")
        self.pk_columns = [k.strip() for k in pk_config.split(",")]

        self.db_config = {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "db": os.getenv("DB_SCHEMA", "classicmodels"),
            "cursorclass": pymysql.cursors.DictCursor,
            "autocommit": True
        }
    def _get_connection(self):
        return pymysql.connect(**self.db_config)
    def _unpack_key(self, primary_key: str) -> tuple:
        if len(self.pk_columns) > 1:
            # We use pipe '|' as delimiter because product codes might have underscores
            values = primary_key.split("|")
            if len(values) != len(self.pk_columns):
                raise ValueError(f"Composite key mismatch. Expected {len(self.pk_columns)} values separated by '|', got {len(values)}.")
            return tuple(values)
        return (primary_key,)
    
    def retrieveByPrimaryKey(self, primary_key: str) -> dict:
        where_clause = " AND ".join([f"{col} = %s" for col in self.pk_columns])
        sql = f"SELECT * FROM {self.table} WHERE {where_clause}"
        values = self._unpack_key(primary_key)
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                result = cursor.fetchone()
                return result if result else {}
    
    def retrieveByTemplate(self, template: dict) -> List[dict]:
        sql = f"SELECT * FROM {self.table}"
        values = []
        
        if template:
            conditions = []
            for col, val in template.items():
                conditions.append(f"{col} = %s")
                values.append(val)
            sql += " WHERE " + " AND ".join(conditions)
            
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(values))
                return cursor.fetchall()
    
    def create(self, payload: dict) -> str:
        columns = ', '.join(payload.keys())
        placeholders = ', '.join(['%s'] * len(payload))
        sql = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, tuple(payload.values()))
                    
                    # 1. Auto-Increment ID (e.g., Customers/Orders)
                    if cursor.lastrowid:
                        return str(cursor.lastrowid)
                    
                    # 2. Composite/Manual Key (e.g., OrderDetails)
                    # If no auto-id, return the key from the payload itself
                    key_parts = [str(payload.get(k)) for k in self.pk_columns]
                    return "|".join(key_parts)
        except pymysql.err.Error as e:
            raise ValueError(f"Database Error (Constraint or Data Invalid): {e}")

    
    def updateByPrimaryKey(self, primary_key: str, payload: dict) -> int:
        # 1. Safety: Remove Primary Keys from payload
        # (Prevents "IntegrityError: Cannot update Foreign Key" crashes)
        safe_payload = payload.copy()
        for pk in self.pk_columns:
            if pk in safe_payload:
                del safe_payload[pk]

        if not safe_payload:
            return 0
            
        set_clause = ', '.join([f"{col} = %s" for col in safe_payload.keys()])
        where_clause = " AND ".join([f"{col} = %s" for col in self.pk_columns])
        
        sql = f"UPDATE {self.table} SET {set_clause} WHERE {where_clause}"
        
        pk_values = self._unpack_key(primary_key)
        values = list(safe_payload.values()) + list(pk_values)
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, tuple(values))
                    return cursor.rowcount
        except pymysql.err.Error as e:
            raise ValueError(f"Update failed due to database constraint: {e}")

    def deleteByPrimaryKey(self, primary_key: str) -> int:
        where_clause = " AND ".join([f"{col} = %s" for col in self.pk_columns])
        sql = f"DELETE FROM {self.table} WHERE {where_clause}"
        
        values = self._unpack_key(primary_key)
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
                    return cursor.rowcount
        except pymysql.err.Error as e:
            raise ValueError(f"Cannot delete item. It is referenced by other records: {e}")
