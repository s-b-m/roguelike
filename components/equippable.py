from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item


class Equippable(BaseComponent):
    parent: Item
    
    def __init__(
        self,
        equipment_type: EquipmentType,
        power_bonus: int = 0,
        defense_bonus: int = 0,
        hitpoints_bonus: int = 0,
        multiplier: float = 1.0,
    ):
        self.equipment_type = equipment_type
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.hitpoints_bonus = hitpoints_bonus
        self.multiplier = multiplier


class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)


class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)


class LeatherChest(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR_CHEST, defense_bonus=1)


class LeatherLegs(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR_LEGS, defense_bonus=1)


class ChainChest(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR_CHEST, defense_bonus=3)


class ChainLegs(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR_LEGS, defense_bonus=2)


class PowerAmulet(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.JEWELRY, multiplier=1.25)


class HealthRing(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.JEWELRY, hitpoints_bonus=15)