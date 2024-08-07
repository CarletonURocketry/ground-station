# Test the websocket commands module
__author__ = "Matteo Golin"

# Imports
import pytest
from enum import Enum
import modules.telemetry.websocket_commands as cmd


# Helper functions
def command_parser(command: str) -> tuple[Enum, list[str]]:
    """Parses a command string and returns the parsed command and parameter list."""

    parameters = cmd.split_command_string(command)
    parsed_command = cmd.parse(parameters, cmd.WebsocketCommand)

    return parsed_command, parameters


# General parsing tests
def test_split_command_string() -> None:
    """Tests that the function to split command returns a list of subcommands and parameters, split on the space."""

    assert cmd.split_command_string("replay play") == ["replay", "play"]


def test_unknown_command_raises_error() -> None:
    """Test that an unknown command raises a command not found error."""

    command = "replay halt"
    parameters = cmd.split_command_string(command)

    with pytest.raises(cmd.WebsocketCommandNotFound):
        _ = cmd.parse(parameters, cmd.WebsocketCommand)


def test_wrong_enum_raises_error() -> None:
    """Test that passing the wrong enum type raises a command not found error."""

    command = "update"
    parameters = cmd.split_command_string(command)

    with pytest.raises(cmd.WebsocketCommandNotFound):
        _ = cmd.parse(parameters, cmd.WebsocketCommand.REPLAY.value)


def test_command_not_found_error_message() -> None:
    """Test that the error message is as expected."""

    command = "replay halt"
    parameters = cmd.split_command_string(command)

    try:
        _ = cmd.parse(parameters, cmd.WebsocketCommand)
    except cmd.WebsocketCommandNotFound as error:
        assert error.command == "halt"
        assert error.message == "The websocket command 'halt' does not exist."


def test_parse_default_enum() -> None:
    """Test that the default enum for the enum parameter of the parse function works with no error."""

    command = "replay speed 1.3"
    parameters = cmd.split_command_string(command)
    parsed_command = cmd.parse(parameters)

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.SPEED
    assert parameters == ["1.3"]


# Individual command tests
def test_update_command() -> None:
    """Test parsing the update websocket command."""

    parsed_command, parameters = command_parser("update")

    assert parameters == []
    assert parsed_command == cmd.WebsocketCommand.UPDATE


def test_start_recording_command() -> None:
    """Tests the start recording command."""

    parsed_command, parameters = command_parser("record start")

    assert parsed_command == cmd.WebsocketCommand.RECORD.value.START
    assert parameters == []


def test_stop_recording_command() -> None:
    """Tests the stop recording command."""

    parsed_command, parameters = command_parser("record stop")

    assert parsed_command == cmd.WebsocketCommand.RECORD.value.STOP
    assert parameters == []


def test_play_replay_command_no_mission_name() -> None:
    """Tests the play replay command without a mission name parameter."""

    parsed_command, parameters = command_parser("replay play")

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.PLAY
    assert parameters == []


def test_play_replay_command_with_one_word_mission_name() -> None:
    """Tests the play replay command with a one-word mission name parameter."""

    parsed_command, parameters = command_parser("replay play mission-name")

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.PLAY
    assert parameters == ["mission-name"]


def test_play_replay_command_with_multiple_word_mission_name() -> None:
    """Tests the play replay command with a multiple word mission name parameter."""

    parsed_command, parameters = command_parser("replay play mission name")

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.PLAY
    assert parameters == ["mission", "name"]


def test_pause_replay_command() -> None:
    """Tests the pause replay command."""

    parsed_command, parameters = command_parser("replay pause")

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.PAUSE
    assert parameters == []


def test_stop_replay_command() -> None:
    """Tests the stop replay command."""

    parsed_command, parameters = command_parser("replay stop")

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.STOP
    assert parameters == []


def test_replay_speed_command() -> None:
    """Tests the replay speed adjustment command."""

    parsed_command, parameters = command_parser("replay speed 2")

    assert parsed_command == cmd.WebsocketCommand.REPLAY.value.SPEED
    assert parameters == ["2"]
