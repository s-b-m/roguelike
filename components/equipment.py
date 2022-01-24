from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):
    parent: Actor

    def __init__(
        self, 
        weapon: Optional[Item] = None, 
        chest: Optional[Item]= None,
        legs: Optional[Item]= None,
        jewelry: Optional[Item]= None,
    ):
        self.weapon = weapon
        self.chest = chest
        self.legs = legs
        self.jewelry = jewelry

    @property
    def defense_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus
        if self.chest is not None and self.chest.equippable is not None:
            bonus += self.chest.equippable.defense_bonus
        if self.legs is not None and self.legs.equippable is not None:
            bonus += self.legs.equippable.defense_bonus
        if self.jewelry is not None and self.jewelry.equippable is not None:
            bonus += self.jewelry.equippable.defense_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus
        if self.chest is not None and self.chest.equippable is not None:
            bonus += self.chest.equippable.power_bonus
        if self.legs is not None and self.legs.equippable is not None:
            bonus += self.legs.equippable.power_bonus
        if self.jewelry is not None and self.jewelry.equippable is not None:
            bonus += self.jewelry.equippable.power_bonus

        return bonus

    @property
    def hitpoints_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.hitpoints_bonus
        if self.chest is not None and self.chest.equippable is not None:
            bonus += self.chest.equippable.hitpoints_bonus
        if self.legs is not None and self.legs.equippable is not None:
            bonus += self.legs.equippable.hitpoints_bonus
        if self.jewelry is not None and self.jewelry.equippable is not None:
            bonus += self.jewelry.equippable.hitpoints_bonus

        return bonus

    def item_is_equipped(self, item: Item) -> bool:
        return self.weapon == item or self.chest == item or self.legs == item or self.jewelry == item

    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)
        
        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if equippable_item.equippable:
            type = equippable_item.equippable.equipment_type
            if type == EquipmentType.WEAPON:
                slot = "weapon"
            elif type == EquipmentType.ARMOR_CHEST:
                slot = "chest"
            elif type == EquipmentType.ARMOR_LEGS:
                slot = "legs"
            else:
                slot = "jewelry"

            if getattr(self, slot) == equippable_item:
                self.unequip_from_slot(slot, add_message)
            else:
                self.equip_to_slot(slot, equippable_item, add_message)