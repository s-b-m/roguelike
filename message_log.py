from types import MethodDescriptorType
from typing import Iterable, List, Reversible, Tuple
import textwrap

import tcod

import color


class Message:
    def __init__(self, text: str, fg: Tuple[int,int,int]):
        self.plain_text = text
        self.fg = fg
        self.count = 1
    
    @property
    def full_text(self) -> str:
        #Get full text + count if greater than 1.
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text

class MessageLog:
    def __init__(self) -> None:
        self.messages: List[Message] = []

    def add_message(
        self, text: str, fg: Tuple[int, int, int] = color.white, *, stack: bool = True,
    ) -> None:
        #push message into the log. if stack is true, stack with previous identical messages
        if stack and self.messages and text == self.messages[-1].plain_text:
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text, fg))

    def render(
        self, console: tcod.Console, x: int, y: int, width: int, height:int,
    ) -> None:
        #Render the log over a given area
        self.render_messages(console, x, y, width, height, self.messages)
    
    @classmethod
    def render_messages(
        cls,
        console: tcod.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        messages: Reversible[Message],
    ) -> None:
        #Render all messages. Reversible is used to start at the most recent message and work backwards.
        y_offset = height - 1
        for message in reversed(messages):
            for line in reversed(list(cls.wrap(message.full_text, width))):
                console.print(x=x, y=y + y_offset, string=line, fg = message.fg)
                y_offset -= 1
                if y_offset < 0:
                    return #We've reached the top of our printable area. Stop printing
    
    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        #Return a wrapped text message.
        for line in string.splitlines(): # handle newlines in messages
            yield from textwrap.wrap(
                line, width, expand_tabs=True,
            )
    
    
