# Displays terminal art for server launch
# Thomas Selwyn (Devil)
# Matteo Golin

# Imports
import datetime as dt
import os
from time import sleep

# Constants
ART_FILE: str = os.path.join(os.path.dirname(__file__), "launch.txt")
FIELDS: dict[str, str] = {
    "rocket name": "ROCKET_NAME",
    "version": "VERSION",
    "date": "DATE",
}


def load_art() -> str:
    """Returns the launch screen ASCII art as a string."""
    with open(ART_FILE, "r") as file:
        art = file.read()
    return art


def populate_fields(art: str, rocket_name: str, version: str) -> str:
    """Returns the launch screen ASCII art with its fields populated as a string."""

    art = art.replace(FIELDS["rocket name"], rocket_name)
    art = art.replace(FIELDS["version"], version)
    art = art.replace(FIELDS["date"], dt.date.today().strftime("%d %B, %Y"))
    return art


def print_cu_rocket(rocket_name: str, version: str) -> None:
    """Prints the CUInSpace rocket ASCII art with information about the rocket and software version."""

    art = load_art()
    art = populate_fields(art, rocket_name, version)
    print(art)
    sleep(0.1)
