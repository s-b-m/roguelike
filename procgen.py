from __future__ import annotations
import random
from typing import Dict, Iterator, Tuple, List, TYPE_CHECKING
import numpy as np
from numpy.lib.shape_base import tile
from game_map import GameMap
import tile_types
import tcod
import entity_assemblyline

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[int, int]]] = {
    0: [(entity_assemblyline.health_potion, 35), (entity_assemblyline.dagger, 15), (entity_assemblyline.leather_legs, 10), (entity_assemblyline.health_ring, 2), (entity_assemblyline.power_amulet, 2)],
    2: [(entity_assemblyline.confusion_scroll, 10), (entity_assemblyline.sword, 15), (entity_assemblyline.leather_chest, 15), (entity_assemblyline.leather_legs, 10), (entity_assemblyline.health_ring, 4), (entity_assemblyline.power_amulet, 4)],
    4: [(entity_assemblyline.lightning_scroll, 25), (entity_assemblyline.health_ring, 6), (entity_assemblyline.power_amulet, 6), (entity_assemblyline.sword, 20), (entity_assemblyline.chain_chest, 15), (entity_assemblyline.chain_legs, 10)],
    8: [(entity_assemblyline.fireball_scroll, 25), (entity_assemblyline.health_ring, 15), (entity_assemblyline.power_amulet, 15)],
}

enemy_chances: Dict[int, List[Tuple[int, int]]] = {
    0: [(entity_assemblyline.orc, 80)],
    3: [(entity_assemblyline.troll, 15)],
    5: [(entity_assemblyline.troll, 30)],
    7: [(entity_assemblyline.troll, 60)],
}


def get_max_value_for_floor(
    weighted_chances_by_floor: List[Tuple[int,int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in weighted_chances_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value
    
    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[int,int]]], 
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property #a read-only getter function
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2)/2)
        center_y = int((self.y1 + self.y2)/2)

        return center_x, center_y

    @property #a read-only getter function
    def inner(self)-> Tuple[slice, slice]:
        #Return an array that holds the inner area of the given room
        return slice(self.x1 + 1, self.x2), slice(self.y1+1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        #Return true if the room overlaps with another RectangularRoom
        return (
            self.x1 <= other.x2
            and self. x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


# TEST OF CELLULAR AUTOMATA FLOOR GENERATION
class CellFloor:
    def __init__(self, width: int, height: int, probability: float):
        self.width = width
        self.height = height
        self.probability = probability
    
    def generate(self, dungeon: GameMap) -> GameMap:
        # Initial carving of tiles
        for i in range(self.width):
            for j in range(self.height):
                choice = random.uniform(0, 1)
                if choice < self.probability:
                    dungeon.tiles[i][j] = tile_types.wall
                else: dungeon.tiles[i][j] = tile_types.floor

        # Reruns to create realistic cave structure using Cellular Automata rules
        generations = 5
        for generation in range(generations):
            for i in range(self.width):
                for j in range(self.height):
                    # Get number of walls within range of 1 from current tile
                    sub = dungeon.tiles[max(i-1, 0):min(i+2, self.width), max(j-1, 0):min(j+2, self.height)]
                    mat = np.array(sub)
                    walls_one_away = len(np.where(mat.flatten() == tile_types.wall)[0])
                    # Get number of walls within range of 2 from current tile
                    sub = dungeon.tiles[max(i-2, 0):min(i+3, self.width), max(j-2, 0):min(j+3, self.height)]
                    mat = np.array(sub)
                    walls_two_away = len(np.where(mat.flatten() == tile_types.wall)[0])
                    # For the first five generations, build a scaffolding of walls
                    if generation < 5:
                        if walls_one_away >= 5 or walls_two_away <= 7:
                            dungeon.tiles[i][j] = tile_types.wall
                        else:
                            dungeon.tiles[i][j] = tile_types.floor
                    else:
                        if walls_one_away >= 5:
                            dungeon.tiles[i][j] = tile_types.wall
                        else:
                            dungeon.tiles[i][j] = tile_types.floor
        return dungeon



def place_entities(
    room: RectangularRoom, dungeon:GameMap, floor_number: int,
) -> None:
    number_of_monsters=random.randint(0, get_max_value_for_floor(max_monsters_by_floor, floor_number))
    number_of_items=random.randint(0, get_max_value_for_floor(max_items_by_floor, floor_number))

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )

    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

#Takes two location tuples and creates a tunnel between them.
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
)-> Iterator[Tuple[int,int]]:
    #Return an L-shaped tunnel between two points.
    x1,y1 = start
    x2,y2 = end
    if random.random() < 0.5: #50% chance of happening
        corner_x, corner_y = x2,y1
    else: corner_x, corner_y = x1,y2
    #generate coordinates in the tunnel
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y
    
def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size:int, 
    map_width:int,
    map_height:int,
    engine: Engine,
) -> GameMap:
    # Create the dungeon map
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])
    # Our "rooms" list holds, you guessed it, a list of the rooms on the current dungeon
    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # create a Rectangular Room object to manipulate the dungeon
        new_room = RectangularRoom(x, y, room_width, room_height)
        # check for room overlap
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue # upon overlap, regenerate
        # no intersections? continue

        # "dig out" floor tiles
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # starting room
            player.place(*new_room.center, dungeon)
        else:
            # tunnel to the next room (i cant stop looking at the word room. why does it look so weird)
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor
            
            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        dungeon.tiles[center_of_last_room] = tile_types.stairs_down
        dungeon.stairs_down_location = center_of_last_room
        
        # we're done generating. add the room to the list of rooms
        rooms.append(new_room)
    return dungeon
    
