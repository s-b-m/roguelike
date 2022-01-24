from typing import Tuple
import numpy as np #type: ignore

#tile graphics constructor that plays nice with Console.tiles_rgb

graphic_dt = np.dtype(
    [
        ("ch", np.int32), #unicode codepoint
        ("fg", "3B"), #3 unsigned bytes, for rgb colors
        ("bg", "3B"), #same for background
    ]
)

tile_dt = np.dtype(
    [
        ("walkable", bool), #bool for walkable tile. walls, enemies, etc.
        ("transparent", bool), #for FOV calculations, based on logical conclusion from the tile.
        ("unseen", graphic_dt), #alternate appearance of tiles that are out of FOV
        ("seen", graphic_dt), # Appearance for when tile is in FOV
    ]
)

#FOW (Fog of War) represents any tiles we've never seen
FOW = np.array((ord(" "), (255, 255, 255), (0,0,0)), dtype=graphic_dt)

def new_tile(
    *, #keyword enforcer. this allows us to create a new tile object without needing to worry about the order of the variables.
    walkable: int,
    transparent: int,
    unseen: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    seen: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    #helper function for creation of new tile types
    return np.array((walkable, transparent, unseen, seen), dtype=tile_dt)

"""TYPES OF TILES"""
floor = new_tile(
    walkable=True, 
    transparent=True, 
    unseen=(ord("."), (100, 100, 100), (0, 0, 0)),
    seen=(ord("."), (200, 200, 200), (0, 0, 0)),
)
wall = new_tile(
    walkable=False, 
    transparent=False, 
    unseen=(ord("#"), (100, 100, 100), (0, 0, 0)),
    seen=(ord("#"), (200, 200, 200), (0, 0, 0)),
)
stairs_down = new_tile(
    walkable=True,
    transparent=True,
    unseen=(ord(">"), (100, 100, 100), (0, 0, 0)),
    seen=(ord(">"), (200, 200, 200), (0, 0, 0)),
)