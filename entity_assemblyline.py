from components.ai import HostileEnemy
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Actor, Item


#THE PLAYER
player = Actor(
    char="@",
    color=(255,255,255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=2, base_power=5),
    inventory=Inventory(capacity=26),
    level=Level(level_up_base=200),
)
#ENEMIES
orc=Actor(
    char="o", 
    color=(63,127,63), 
    name="Orc", 
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=30),
)
troll=Actor(
    char="T", 
    color=(0,127,0), 
    name="Troll", 
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    inventory=Inventory(capacity=0),
    level=Level(xp_given=48),
)
#CONSUMABLES
health_potion=Item(
    char="!",
    color=(127,0,255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=10),
)
lightning_scroll = Item(
    char="~",
    color = (255,255,0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)
fireball_scroll = Item(
    char="~",
    color = (255, 0, 0),
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3),
)
confusion_scroll = Item(
    char="~",
    color = (207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(turns_left=10),
)
#EQUIPPABLES
dagger = Item(char="/", color=(0, 191, 255), name="Dagger", equippable=equippable.Dagger())
sword = Item(char="/", color=(0, 191, 255), name="Sword", equippable=equippable.Sword())
leather_chest=Item(char="[", color=(139, 69, 19), name="Leather Chestplate", equippable=equippable.LeatherChest())
leather_legs=Item(char="+", color=(139, 69, 19), name="Leather Legs", equippable=equippable.LeatherLegs())
chain_chest=Item(char="[", color=(139, 69, 19), name="Chainmail Chestplate", equippable=equippable.ChainChest())
chain_legs=Item(char="[", color=(139, 69, 19), name="Chainmail Skirt", equippable=equippable.ChainLegs())
power_amulet=Item(char="*", color=(255, 255, 255), name="Amulet", equippable=equippable.PowerAmulet())
health_ring=Item(char=".", color=(255, 0, 0), name="Ring", equippable=equippable.HealthRing())