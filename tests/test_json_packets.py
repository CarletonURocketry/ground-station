# Test cases for the JSON packets module
__author__ = "Matteo Golin"

# Imports
import modules.telemetry.status as status


# Default parameter tests
def test_serial_data_defaults() -> None:
    """Test that the default field values for the serial data are correct."""
    serial_data = status.SerialData()

    assert serial_data.available_ports == []


def test_rn2483_radio_data_defaults() -> None:
    """Test that the default field values for the RN2483 radio data are correct."""
    radio_data = status.RN2483RadioData()

    assert radio_data.connected is False
    assert radio_data.connected_port == ""


def test_mission_data_defaults() -> None:
    """Test that the default field values for the mission data are correct."""
    mission_data = status.MissionData()

    assert mission_data.name == ""
    assert mission_data.epoch == -1
    assert mission_data.state == status.MissionState.DNE
    assert mission_data.recording is False
    assert mission_data.last_mission_time == -1


def test_replay_data_defaults() -> None:
    """Test that the default field values for the replay data are correct."""
    replay_data = status.ReplayData()

    assert replay_data.state == status.ReplayState.DNE
    assert replay_data.speed == 1.0


# JSON serialization tests
def test_serial_data_serialization() -> None:
    """Test that the serialization of serial data is correct."""
    serial_data = status.SerialData(available_ports=["20", "16"])

    assert dict(serial_data) == {"available_ports": ["20", "16"]}


def test_rn2483_radio_data_serialization() -> None:
    """Test that the serialization of RN2483 radio data is correct."""

    rn2483_radio_data = status.RN2483RadioData(connected=True, connected_port="20")

    assert dict(rn2483_radio_data) == {
        "connected_port": "20",
        "connected": True,
        "snr": 0,
    }


def test_mission_data_serialization() -> None:
    """Test that the serialization of mission data is correct."""

    mission_data = status.MissionData(
        name="rocket mission",
        epoch=12,
        state=status.MissionState.RECORDED,
        recording=True,
        last_mission_time=50,
    )

    assert dict(mission_data) == {
        "name": "rocket mission",
        "epoch": 12,
        "state": status.MissionState.RECORDED.value,
        "recording": True,
    }


def test_status_data_serialization() -> None:
    """Test that the serialization of status data is correct."""

    mission_data = status.MissionData(
        name="rocket mission",
        epoch=12,
        state=status.MissionState.RECORDED,
        recording=True,
        last_mission_time=3921,
    )

    serial_data = status.SerialData(available_ports=["20", "16"])

    rn2483_radio_data = status.RN2483RadioData(
        connected=True,
        connected_port="20",
        snr=5,
    )

    replay_data = status.ReplayData(
        state=status.ReplayState.PAUSED,
        speed=2.5,
    )

    # Mission list must be reset so that it can be tested without knowing what is
    # in the missions directory
    replay_data.mission_list = [status.MissionEntry(name="TestData", length=3598549)]

    status_data = status.TelemetryStatus(
        mission=mission_data,
        serial=serial_data,
        rn2483_radio=rn2483_radio_data,
        replay=replay_data,
    )

    assert dict(status_data) == {
        "mission": {
            "name": "rocket mission",
            "epoch": 12,
            "state": status.MissionState.RECORDED.value,
            "recording": True,
        },
        "serial": {"available_ports": ["20", "16"]},
        "rn2483_radio": {
            "connected": True,
            "connected_port": "20",
            "snr": 5,
        },
        "replay": {
            "state": status.ReplayState.PAUSED.value,
            "speed": 2.5,
            "mission_list": [{"name": "TestData", "length": 3598549, "version": 1}],
        },
    }
