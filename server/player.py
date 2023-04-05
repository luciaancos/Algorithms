from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packet import StreamSocket


@dataclass
class Player:
    """Contains extra information appart for a user, appart from the socket"""

    socket: StreamSocket
