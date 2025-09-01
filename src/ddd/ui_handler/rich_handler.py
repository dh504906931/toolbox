import os
from typing import Union, Optional, Any, List, Dict

from ddd.ui_handler.handler_base import UIHandlerBase, Theme
from ddd.ui_handler.utils import (
    Console, Panel, Table, Text, box, check_rich_available
)

from .handler_base import _import_rich, Theme


# Rich UI constants
DEFAULT_BOX_TYPE = "rounded"
DEFAULT_PANEL_PADDING = (0, 1)
DEFAULT_TITLE_ALIGN = "left"


class RichHandler(UIHandlerBase):
    """Rich-enhanced TUI implementation with colorful styling using Rich library"""

    def __init__(self):
        check_rich_available()
        self.console = Console()

    def clear_screen(self):
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_text(self, text: Union[str, Any] = "", style: Optional[str] = None, end: str = "\n"):
        """Print text with optional styling"""
        if isinstance(text, str) and style:
            text = Text(text, style=style)
        self.console.print(text, end=end)

    def print_panel(self, content: Union[str, Any], title: Optional[str] = None,
                   style: Optional[str] = None, border_style: Optional[str] = None,
                   box_type: Optional[str] = None, padding: tuple = (0, 1),
                   title_align: str = "left") -> None:
        """Print content in a styled panel"""
        panel_kwargs = {
            "title": title,
            "title_align": title_align,
            "style": style,
            "box": self._get_box_type(box_type),
            "padding": padding
        }

        # Only add border_style if it's not None
        if border_style is not None:
            panel_kwargs["border_style"] = border_style

        panel = Panel(content, **panel_kwargs)
        self.console.print(panel)

    def print_table(self, title: Optional[str] = None, title_style: Optional[str] = None,
                   columns: Optional[List[Dict[str, Any]]] = None,
                   rows: Optional[List[List[str]]] = None,
                   box_type: Optional[str] = None,
                   border_style: Optional[str] = None,
                   show_header: bool = True, **kwargs) -> None:
        """Create and print a styled table"""
        table = Table(
            title=title,
            title_style=title_style,
            box=self._get_box_type(box_type),
            border_style=border_style,
            show_header=show_header,
            **kwargs
        )

        if columns:
            for col in columns:
                table.add_column(**col)

        if rows:
            for row in rows:
                table.add_row(*row)

        self.console.print(table)

    def get_input(self, prompt: Union[str, Any] = "", default: str = "") -> Optional[str]:
        """Get user input with styled prompt"""
        if isinstance(prompt, str):
            prompt_text = Text()
            prompt_text.append("❯ ", style=f"bold {Theme.PRIMARY}")
            prompt_text.append(prompt, style=Theme.TEXT_PRIMARY)

            if default:
                prompt_text.append(f" [{default}]", style=Theme.TEXT_SECONDARY)

            prompt_text.append(": ", style=Theme.TEXT_PRIMARY)
            prompt = prompt_text

        if prompt:
            self.console.print(prompt, end="")

        try:
            user_input = input().strip()
            return user_input if user_input else default
        except KeyboardInterrupt:
            self.console.print("")
            return None

    def _get_box_type(self, box_type: Optional[str]):
        """Convert box_type string to Rich box object"""
        if box_type == "double":
            return box.DOUBLE
        elif box_type == "single":
            return box.SQUARE
        elif box_type == "heavy":
            return box.HEAVY
        else:
            return box.ROUNDED  # default

