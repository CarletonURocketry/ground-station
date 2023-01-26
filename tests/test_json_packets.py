# Test cases for the JSON packets module
__author__ = "Matteo Golin"

# Imports
import modules.telemetry.json_packets as jsp
from modules.telemetry.data_block import DeploymentState

# Constants


# Default parameter tests
def test_serial_data_defaults() -> None:
    """Test that the default field values for the serial data are correct."""
    serial_data = jsp.SerialData()

    assert serial_data.available_ports == []


def test_rn2483_radio_data_defaults() -> None:
    """Test that the default field values for the RN2483 radio data are correct."""
    radio_data = jsp.RN2483RadioData()

    assert radio_data.connected is False
    assert radio_data.connected_port == ""


def test_mission_data_defaults() -> None:
    """Test that the default field values for the mission data are correct."""
    mission_data = jsp.MissionData()

    assert mission_data.name == ""
    assert mission_data.epoch == -1
    assert mission_data.state == jsp.MissionState.DNE
    assert mission_data.recording is False


def test_rocket_data_defaults() -> None:
    """Test that the default field values for the rocket data are correct."""
    rocket_data = jsp.RocketData()

    assert rocket_data.kx134_state == -1
    assert rocket_data.altimeter_state == -1
    assert rocket_data.imu_state == -1
    assert rocket_data.sd_driver_state == -1
    assert rocket_data.deployment_state == DeploymentState.DEPLOYMENT_STATE_DNE.value
    assert rocket_data.blocks_recorded == -1
    assert rocket_data.checkouts_missed == -1
    assert rocket_data.mission_time == -1
    assert rocket_data.last_mission_time == -1


def test_replay_data_defaults() -> None:
    """Test that the default field values for the replay data are correct."""
    replay_data = jsp.ReplayData()

    assert replay_data.status == jsp.ReplayState.DNE
    assert replay_data.speed == 1.0
    assert replay_data.mission_list == []


# JSON serialization tests
def test_serial_data_serialization() -> None:
    """Test that the serialization of serial data is correct."""
    serial_data = jsp.SerialData(available_ports=["20", "16"])

    assert dict(serial_data) == {"available_ports": ["20", "16"]}


def test_rn2483_radio_data_serialization() -> None:
    """Test that the serialization of RN2483 radio data is correct."""

    rn2483_radio_data = jsp.RN2483RadioData(
        connected=True,
        connected_port="20"
    )

    assert dict(rn2483_radio_data) == {
        "connected_port": "20",
        "connected": True,
    }


def test_mission_data_serialization() -> None:
    """Test that the serialization of mission data is correct."""

    mission_data = jsp.MissionData(
        name="rocket mission",
        epoch=12,
        state=jsp.MissionState.RECORDED,
        recording=True
    )

    assert dict(mission_data) == {
        "name": "rocket mission",
        "epoch": 12,
        "state": jsp.MissionState.RECORDED.value,
        "recording": True,
    }


def test_rocket_data_serialization() -> None:
    """Test that the serialization of rocket data is correct."""

    rocket_data = jsp.RocketData(
        kx134_state=2,
        altimeter_state=1,
        imu_state=3,
        sd_driver_state=1,
        deployment_state=DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT,
        blocks_recorded=12,
        checkouts_missed=3,
        mission_time=1983,
        last_mission_time=1981,
    )

    assert dict(rocket_data) == {
        "kx134_state": 2,
        "altimeter_state": 1,
        "imu_state": 3,
        "sd_driver_state": 1,
        "deployment_state": DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT.value,
        "deployment_state_text": str(DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT),
        "blocks_recorded": 12,
        "checkouts_missed": 3,
        "mission_time": 1983,
        "last_mission_time": 1981,
    }


def test_status_data_serialization() -> None:
    """Test that the serialization of status data is correct."""

    rocket_data = jsp.RocketData(
        kx134_state=2,
        altimeter_state=1,
        imu_state=3,
        sd_driver_state=1,
        deployment_state=DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT,
        blocks_recorded=12,
        checkouts_missed=3,
        mission_time=1983,
        last_mission_time=1981,
    )

    mission_data = jsp.MissionData(
        name="rocket mission",
        epoch=12,
        state=jsp.MissionState.RECORDED,
        recording=True
    )

    rn2483_radio_data = jsp.RN2483RadioData(
        connected=True,
        connected_port="20"
    )

    serial_data = jsp.SerialData(available_ports=["20", "16"])

    status_data = jsp.StatusData(
        mission=mission_data,
        serial=serial_data,
        rn2483_radio=rn2483_radio_data,
        rocket=rocket_data
    )

    assert dict(status_data) == {
        "mission": dict(mission_data),
        "serial": dict(serial_data),
        "rn2483_radio": dict(rn2483_radio_data),
        "rocket": dict(rocket_data)
    }


def test_replay_data_serialization() -> None:
    """Test that the serialization of replay data is correct."""

    replay_data = jsp.ReplayData(
        status=jsp.ReplayState.PAUSED,
        speed=2.5,
    )

    # Mission list must be reset so that it can be tested without knowing what is
    # in the missions directory
    replay_data.mission_list = ["test mission", "another mission"]

    assert dict(replay_data) == {
        "status": jsp.ReplayState.PAUSED.value,
        "speed": 2.5,
        "mission_list": ["test mission", "another mission"]
    }

# TODO test RocketData.from_data_block()
# TODO test mission list logic on ReplayData
