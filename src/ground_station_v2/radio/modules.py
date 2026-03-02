"""
Registry of supported radio modules.

To add support for a new radio module, add an entry to SUPPORTED_MODULES with:
- baud_rate: The baud rate used for serial communication.
- identify_command: The command sent to identify the device.
- identify_response_prefix: The expected prefix of the identification response.

Example for a hypothetical RN2903 module:
    "RN2903": ModuleDefinition(
        baud_rate=57600,
        identify_command="sys get ver",
        identify_response_prefix="RN2903",
    ),
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleDefinition:
    """Definition of a supported radio module."""

    baud_rate: int
    identify_command: str
    identify_response_prefix: str


SUPPORTED_MODULES: dict[str, ModuleDefinition] = {
    "RN2483": ModuleDefinition(
        baud_rate=57600,
        identify_command="sys get ver",
        identify_response_prefix="RN2483",
    ),
}
