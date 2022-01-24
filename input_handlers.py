from __future__ import annotations

import os

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod

import actions
from actions import Action, BumpAction, WaitAction, PickupAction
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item


MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value that either triggers an action or switches to another handler.

If a handler is returned, it becomes the active handler for current events.
If an action is returned, its attempted. If it was valid, MainGameEventHandler becomes the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state,Action), f"{self!r} can't handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class PopUpMessage(BaseEventHandler):
    """Display a pop up window in the center of the screen."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # We've performed an action successfully
            if not self.engine.player.is_alive:
                # The player died during the current action
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine) # Go back to the main game
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        # Handles actions returned from event methods. If the action advances a turn, return true.
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False # Skip enemy turns on exceptions. This prevents us from giving enemies free turns when a mistake is made.
        
        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

class AskUserEventHandler(EventHandler):
    """Handles a user input for any action that requires special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Any key press will exit this input handler by default."""
        if event.sym in {
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Any mouse click will exit this input handler by default."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called upon a user's attempt to exit/cancel the action.
        
        By default, this returns to the main event handler.
        """
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        pl = self.engine.player.level # player level class
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title=self.TITLE,
            clear=True,
            fg=(255,255,255),
            bg=(0,0,0),
        )

        console.print(
            x=x+1, y=y+1, string=f"Level: {pl.current_level}"
        )
        console.print(
            x=x+1, y=y+2, string=f"XP: {pl.current_xp}"
        )
        console.print(
            x=x+1, y=y+3 , string=f"XP to next level: {pl.xp_to_next_level}"
        )
        console.print(
            x=x+1, y=y+4, string=f"Attack: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x+1, y=y+5, string=f"Devense: {self.engine.player.fighter.defense}"
        )

class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up!"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else: 
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255,255,255),
            bg=(0,0,0),
        )

        console.print(x=x +1, y=1, string="Congratulations! You've levelled up!")
        console.print(x=x+1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x+1,
            y=4,
            string=f"a) Hitpoints ({self.engine.player.fighter.max_hp} -> {self.engine.player.fighter.max_hp+20}"
        )
        console.print(
            x=x+1,
            y=5,
            string=f"a) Strength ({self.engine.player.fighter.power} -> {self.engine.player.fighter.power+1}"
        )
        console.print(
            x=x+1,
            y=6,
            string=f"a) Agility ({self.engine.player.fighter.defense} -> {self.engine.player.fighter.defense+1}"
        )

    def ev_keydown(self, event=tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)
            return None
        
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Do nothing."""
        return None


class InventoryEventHandler(AskUserEventHandler):
    """Handler for selecting an item from the inventory.
    
    The subclass of the given item determines what happens next.
    """

    TITLE = 'INVENTORY'

    def on_render(self, console: tcod.Console) -> None:
        """Renders the inventory menu that displays all items in the inventory, and a
        letter attached to the item for using/examining/whatever they want to do with it.
        
        The menu moves based on where the player is located so that the player is never 
        hidden behind the menu.
        """

        super().on_render(console)
        num_inv_items = len(self.engine.player.inventory.items)
        height = num_inv_items + 2

        if height <= 3:
            height = 3
        
        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0
        y = 0
        width = len(self.TITLE) + 4
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255,255,255),
            bg=(0,0,0),
        )

        if num_inv_items > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a")+i)
                is_equipped = self.engine.player.equipment.item_is_equipped(item)
                item_string = f"({item_key}) {item.name}"

                if is_equipped:
                    item_string = f"{item_string} (E)"
                console.print(x + 1, y + i + 1, item_string)
        else:
            console.print(x+1, y+1, "(Nothing)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()

class InventoryActivateHandler(InventoryEventHandler):
    """Handle the use of an inventory item."""

    TITLE = "Use which item?"

    def on_item_selected(self, item:Item) -> Optional[ActionOrHandler]:
        """Returns the action for the selected item."""
        if item.consumable:
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None

class InventoryDropHandler(InventoryEventHandler):
    """Handles dropping an inventory item."""

    TITLE = "Drop which item?"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop the item."""
        return actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user to select a location on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1 # Relative speed of movement. Holding certain keys increases the speed.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20
        
            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Prevent the cursor from leaving the map.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown()

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Call when an index is selected."""
        return NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Allows the player to look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to the main handler."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the selected enemy will be affected."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)
        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int,int]], Optional(Action)],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.console) -> None:
        """Highlight the title under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        # Draw a polygon around the targeted area. Allows the player to see the area of effect.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg = color.red,
            clear = False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

class MainGameEventHandler(EventHandler):

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (
            tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)

        

        # No valid key was pressed
        return action


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

class HistoryViewer(EventHandler):
    #Prints the history of the chatbox in a larger window that can be navigated.

    def __init__(self, engine:Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length-1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console) # Draw the main state as the background

        log_console = tcod.Console(console.width - 6, console.height - 6)

        #draw a banner with a custom title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment = tcod.CENTER
        )

        #Render the message using the cursor parameter
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Conditional movement wizardry
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                #Move from top to bottom only when on the edge
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                #The inverse for bottom to top
                self.cursor = 0
            else:
                #Otherwise move by staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0 #Go to the top message upon pressing home.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1 #Go to the bottom message upon pressing end.
        else: #Pressing any other key moves us back to the main game.
            return MainGameEventHandler(self.engine)
        return None