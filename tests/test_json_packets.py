# Test cases for the JSON packets module
__author__ = "Matteo Golin"

# Imports
import modules.telemetry.json_packets as jsp
from modules.telemetry.data_block import (
    DeploymentState,
    SDCardStatus,
    SensorStatus,
    StatusDataBlock,
)


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
    assert mission_data.last_mission_time == -1


def test_rocket_data_defaults() -> None:
    """Test that the default field values for the rocket data are correct."""
    rocket_data = jsp.RocketData()

    assert rocket_data.mission_time == -1
    assert rocket_data.deployment_state == DeploymentState.DEPLOYMENT_STATE_DNE.value
    assert rocket_data.blocks_recorded == -1
    assert rocket_data.checkouts_missed == -1


def test_replay_data_defaults() -> None:
    """Test that the default field values for the replay data are correct."""
    replay_data = jsp.ReplayData()

    assert replay_data.state == jsp.ReplayState.DNE
    assert replay_data.speed == 1.0


# JSON serialization tests
def test_serial_data_serialization() -> None:
    """Test that the serialization of serial data is correct."""
    serial_data = jsp.SerialData(available_ports=["20", "16"])

    assert dict(serial_data) == {"available_ports": ["20", "16"]}


def test_rn2483_radio_data_serialization() -> None:
    """Test that the serialization of RN2483 radio data is correct."""

    rn2483_radio_data = jsp.RN2483RadioData(connected=True, connected_port="20")

    assert dict(rn2483_radio_data) == {
        "connected_port": "20",
        "connected": True,
        "snr": 0,
    }


def test_mission_data_serialization() -> None:
    """Test that the serialization of mission data is correct."""

    mission_data = jsp.MissionData(
        name="rocket mission",
        epoch=12,
        state=jsp.MissionState.RECORDED,
        recording=True,
        last_mission_time=50,
    )

    assert dict(mission_data) == {
        "name": "rocket mission",
        "epoch": 12,
        "state": jsp.MissionState.RECORDED.value,
        "recording": True,
        "last_mission_time": 50,
    }


def test_rocket_data_serialization() -> None:
    """Test that the serialization of rocket data is correct."""

    rocket_data = jsp.RocketData(
        mission_time=1983,
        deployment_state=DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT,
        blocks_recorded=12,
        checkouts_missed=3,
    )

    assert dict(rocket_data) == {
        "mission_time": 1983,
        "deployment_state": DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT.value,
        "blocks_recorded": 12,
        "checkouts_missed": 3,
    }


def test_status_data_serialization() -> None:
    """Test that the serialization of status data is correct."""

    mission_data = jsp.MissionData(
        name="rocket mission",
        epoch=12,
        state=jsp.MissionState.RECORDED,
        recording=True,
        last_mission_time=3921,
    )

    serial_data = jsp.SerialData(available_ports=["20", "16"])

    rn2483_radio_data = jsp.RN2483RadioData(
        connected=True,
        connected_port="20",
        snr=5,
    )

    rocket_data = jsp.RocketData(
        mission_time=1983,
        deployment_state=DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT,
        blocks_recorded=12,
        checkouts_missed=3,
    )

    replay_data = jsp.ReplayData(
        state=jsp.ReplayState.PAUSED,
        speed=2.5,
    )

    # Mission list must be reset so that it can be tested without knowing what is
    # in the missions directory
    replay_data.mission_list = [jsp.MissionEntry(name="TestData", length=3598549)]

    status_data = jsp.StatusData(
        mission=mission_data,
        serial=serial_data,
        rn2483_radio=rn2483_radio_data,
        rocket=rocket_data,
        replay=replay_data,
    )

    assert dict(status_data) == {
        "mission": {
            "name": "rocket mission",
            "epoch": 12,
            "state": jsp.MissionState.RECORDED.value,
            "recording": True,
            "last_mission_time": 3921,
        },
        "serial": {"available_ports": ["20", "16"]},
        "rn2483_radio": {
            "connected": True,
            "connected_port": "20",
            "snr": 5,
        },
        "rocket": {
            "mission_time": 1983,
            "deployment_state": DeploymentState.DEPLOYMENT_STATE_COASTING_ASCENT.value,
            "blocks_recorded": 12,
            "checkouts_missed": 3,
        },
        "replay": {
            "state": jsp.ReplayState.PAUSED.value,
            "speed": 2.5,
            "mission_list": [{"name": "TestData", "length": 3598549, "version": 1}],
        },
    }


# Logic testing
def test_rocket_data_from_data_block() -> None:
    """Tests that properties of rocket data are correctly assigned from a data block."""

    data_block = StatusDataBlock(
        mission_time=145,
        kx134_state=SensorStatus(3),
        alt_state=SensorStatus(4),
        imu_state=SensorStatus(2),
        sd_state=SDCardStatus(1),
        sd_blocks_recorded=18,
        deployment_state=DeploymentState.DEPLOYMENT_STATE_POWERED_ASCENT,
        sd_checkouts_missed=90,
    )

    rocket_data = jsp.RocketData.from_data_block(data_block)

    assert rocket_data.mission_time == 145
    assert rocket_data.blocks_recorded == 18
    assert rocket_data.deployment_state == DeploymentState.DEPLOYMENT_STATE_POWERED_ASCENT
    assert rocket_data.checkouts_missed == 90
