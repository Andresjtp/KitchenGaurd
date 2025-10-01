"""
Database models for KitchenGuard application
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Product model matching the database schema"""

    id: Optional[int] = None
    name: str = ""
    category: str = ""
    current_stock: int = 0
    unit_cost: float = 0.0
    supplier: str = ""

    def to_dict(self):
        """Convert product to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "current_stock": self.current_stock,
            "unit_cost": self.unit_cost,
            "supplier": self.supplier,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create product from dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            category=data.get("category", ""),
            current_stock=data.get("current_stock", 0),
            unit_cost=data.get("unit_cost", 0.0),
            supplier=data.get("supplier", ""),
        )
