# Tests config module for accurate loading, error checking and default values
__author__ = "Matteo Golin"

# Imports
import pytest
import json
import os
from modules.misc.config import CodingRates, Config, RadioParameters, load_config


# Fixtures
@pytest.fixture()
def def_radio_params() -> dict[str, str | int | bool]:
    return {
        "modulation": "lora",
        "frequency": 433_050_000,
        "power": 15,
        "spread_factor": 9,
        "coding_rate": "4/7",
        "bandwidth": 500,
        "preamble_len": 6,
        "cyclic_redundancy": True,
        "iqi": False,
        "sync_word": "0x43",
    }


@pytest.fixture()
def callsigns() -> dict[str, str]:
    return {"VA3TEST": "Some Body", "VA3INI": "linguini1"}


@pytest.fixture()
def config(def_radio_params: dict[str, str | int | bool], callsigns: dict[str, str]):
    return {"radio_parameters": def_radio_params, "approved_callsigns": callsigns}


# Test radio parameters
def test_radio_params_default(def_radio_params: dict[str, str | int | bool]):
    """Tests that the RadioParameters object default constructor initializes all values to the correct defaults."""
    params = RadioParameters()
    assert params.modulation.value == def_radio_params.get("modulation")
    assert params.frequency == def_radio_params.get("frequency")
    assert params.spread_factor == def_radio_params.get("spread_factor")
    assert params.coding_rate.value == def_radio_params.get("coding_rate")
    assert params.bandwidth == def_radio_params.get("bandwidth")
    assert params.preamble_len == def_radio_params.get("preamble_len")
    assert params.cyclic_redundancy == def_radio_params.get("cyclic_redundancy")
    assert params.iqi == def_radio_params.get("iqi")
    assert params.sync_word == def_radio_params.get("sync_word")[2:]  # type: ignore


def test_radio_params_partial_default():
    """
    Tests that the RadioParameters object default constructor initializes all non-specified values to the correct
    defaults, and specified values to the passed values.
    """
    params = RadioParameters(sync_word="0x13", power=12, coding_rate=CodingRates.FOUR_FIFTHS)
    assert params.sync_word == "13"
    assert params.power == 12
    assert params.coding_rate == CodingRates.FOUR_FIFTHS


def test_radio_params_default_json(def_radio_params: dict[str, str | int | bool]):
    """
    Tests that the RadioParameters object's from_json method initializes all values to the correct defaults when given
    no radio_params JSON object.
    """
    params = RadioParameters.from_json(dict())
    assert params.modulation.value == def_radio_params.get("modulation")
    assert params.frequency == def_radio_params.get("frequency")
    assert params.spread_factor == def_radio_params.get("spread_factor")
    assert params.coding_rate.value == def_radio_params.get("coding_rate")
    assert params.bandwidth == def_radio_params.get("bandwidth")
    assert params.preamble_len == def_radio_params.get("preamble_len")
    assert params.cyclic_redundancy == def_radio_params.get("cyclic_redundancy")
    assert params.iqi == def_radio_params.get("iqi")
    assert params.sync_word == def_radio_params.get("sync_word")[2:]  # type: ignore


def test_radio_params_partial_defaults_json():
    """
    Tests that the RadioParameters object's from_json method initializes all values to defaults except those
    that are specified in the radio_params JSON object already.
    """
    params = RadioParameters.from_json(
        {
            "sync_word": "0x13",
            "power": 12,
            "coding_rate": CodingRates.FOUR_FIFTHS,
        }
    )
    assert params.sync_word == "13"
    assert params.power == 12
    assert params.coding_rate == CodingRates.FOUR_FIFTHS


def test_radio_params_invalid_arguments():
    """
    Tests that initializing a RadioParameters object using invalid parameters will raise a value error.
    """

    with pytest.raises(ValueError):
        _ = RadioParameters(frequency=42)

    with pytest.raises(ValueError):
        _ = RadioParameters(power=18)

    with pytest.raises(ValueError):
        _ = RadioParameters(spread_factor=6)

    with pytest.raises(ValueError):
        _ = RadioParameters(preamble_len=65536)

    with pytest.raises(ValueError):
        _ = RadioParameters(sync_word="0x101")


def test_radio_params_invalid_arguments_json():
    """
    Tests that initializing a RadioParameters object using invalid parameters from a JSON schema will raise a
    ValueError.
    """

    with pytest.raises(ValueError):
        _ = RadioParameters.from_json({"frequency": 42})

    with pytest.raises(ValueError):
        _ = RadioParameters.from_json({"power": 18})

    with pytest.raises(ValueError):
        _ = RadioParameters.from_json({"spread_factor": 6})

    with pytest.raises(ValueError):
        _ = RadioParameters.from_json({"preamble_len": 65536})

    with pytest.raises(ValueError):
        _ = RadioParameters.from_json({"sync_word": "0x101"})


def test_radio_params_range_edges():
    """
    Tests that initializing a RadioParameters object with values right at the end of the accepted ranges
    does not raise any exceptions.
    """

    _ = RadioParameters(power=-3)
    _ = RadioParameters(power=16)

    _ = RadioParameters(sync_word="0x0")
    _ = RadioParameters(sync_word="0x100")

    _ = RadioParameters(preamble_len=0)
    _ = RadioParameters(preamble_len=65_535)

    _ = RadioParameters(frequency=433_050_000)
    _ = RadioParameters(frequency=434_790_000)
    _ = RadioParameters(frequency=863_000_000)
    _ = RadioParameters(frequency=870_000_000)


def test_radio_params_outside_range_edges():
    """
    Tests that initializing a RadioParameters object with values just outside the end of the accepted ranges
    raises a ValueError.
    """

    with pytest.raises(ValueError):
        _ = RadioParameters(power=-4)
    assert RadioParameters(power=-3).power == -3

    with pytest.raises(ValueError):
        _ = RadioParameters(power=17)
    assert RadioParameters(power=16).power == 16

    with pytest.raises(ValueError):
        _ = RadioParameters(sync_word="0x101")
    assert RadioParameters(sync_word="0x100").sync_word == "100"

    with pytest.raises(ValueError):
        _ = RadioParameters(preamble_len=-1)
    assert RadioParameters(preamble_len=0).preamble_len == 0

    with pytest.raises(ValueError):
        _ = RadioParameters(preamble_len=65_536)
    assert RadioParameters(preamble_len=65_535).preamble_len == 65_535

    with pytest.raises(ValueError):
        _ = RadioParameters(frequency=433_049_999)
    assert RadioParameters(frequency=433_050_000).frequency == 433_050_000

    with pytest.raises(ValueError):
        _ = RadioParameters(frequency=434_790_001)
    assert RadioParameters(frequency=434_790_000).frequency == 434_790_000

    with pytest.raises(ValueError):
        _ = RadioParameters(frequency=862_999_999)
    assert RadioParameters(frequency=863_000_000).frequency == 863_000_000

    with pytest.raises(ValueError):
        _ = RadioParameters(frequency=870_000_001)
    assert RadioParameters(frequency=870_000_000).frequency == 870_000_000


def test_config_defaults(def_radio_params: dict[str, str | int | bool], callsigns: dict[str, str]):
    """Tests that initializing an empty Config object results in the correct default values."""

    config = Config(approved_callsigns=callsigns)

    assert config.radio_parameters.modulation.value == def_radio_params.get("modulation")
    assert config.radio_parameters.frequency == def_radio_params.get("frequency")
    assert config.radio_parameters.spread_factor == def_radio_params.get("spread_factor")
    assert config.radio_parameters.coding_rate.value == def_radio_params.get("coding_rate")
    assert config.radio_parameters.bandwidth == def_radio_params.get("bandwidth")
    assert config.radio_parameters.preamble_len == def_radio_params.get("preamble_len")
    assert config.radio_parameters.cyclic_redundancy == def_radio_params.get("cyclic_redundancy")
    assert config.radio_parameters.iqi == def_radio_params.get("iqi")
    assert config.radio_parameters.sync_word == def_radio_params.get("sync_word")[2:]  # type: ignore
    assert config.approved_callsigns == callsigns


def test_config_defaults_json(def_radio_params: dict[str, str | int | bool], callsigns: dict[str, str]):
    """Tests that initializing a Config object from an empty JSON object results in the correct default values."""

    config = Config.from_json({"approved_callsigns": callsigns})

    assert config.radio_parameters.modulation.value == def_radio_params.get("modulation")
    assert config.radio_parameters.frequency == def_radio_params.get("frequency")
    assert config.radio_parameters.spread_factor == def_radio_params.get("spread_factor")
    assert config.radio_parameters.coding_rate.value == def_radio_params.get("coding_rate")
    assert config.radio_parameters.bandwidth == def_radio_params.get("bandwidth")
    assert config.radio_parameters.preamble_len == def_radio_params.get("preamble_len")
    assert config.radio_parameters.cyclic_redundancy == def_radio_params.get("cyclic_redundancy")
    assert config.radio_parameters.iqi == def_radio_params.get("iqi")
    assert config.radio_parameters.sync_word == def_radio_params.get("sync_word")[2:]  # type: ignore
    assert config.approved_callsigns == callsigns


def test_no_callsigns():
    """Tests that a Config object initialized with no callsigns raises a ValueError."""

    with pytest.raises(ValueError):
        _ = Config()


def test_no_callsigns_json():
    """Tests that Config object initialized with a JSON object containing no approved callsigns raises a ValueError."""

    with pytest.raises(ValueError):
        _ = Config.from_json(dict())


def test_config_from_json(config: dict[str, dict[str, str | int | bool]]):
    """Test that initializing a Config object from a valid JSON config results in the correct values being set."""

    cfg = Config.from_json(config)

    rparams = config["radio_parameters"]
    assert cfg.radio_parameters.modulation.value == rparams.get("modulation")
    assert cfg.radio_parameters.frequency == rparams.get("frequency")
    assert cfg.radio_parameters.spread_factor == rparams.get("spread_factor")
    assert cfg.radio_parameters.coding_rate.value == rparams.get("coding_rate")
    assert cfg.radio_parameters.bandwidth == rparams.get("bandwidth")
    assert cfg.radio_parameters.preamble_len == rparams.get("preamble_len")
    assert cfg.radio_parameters.cyclic_redundancy == rparams.get("cyclic_redundancy")
    assert cfg.radio_parameters.iqi == rparams.get("iqi")
    assert cfg.radio_parameters.sync_word == rparams.get("sync_word")[2:]  # type: ignore
    assert cfg.approved_callsigns == config["approved_callsigns"]


def test_load_config(config: dict[str, dict[str, str | int | bool]]):
    """Test that loading a Config object from a valid JSON config file results in the correct values being set."""

    # Setup
    with open("./test_config.json", "w") as file:
        json.dump(config, file)

    cfg = load_config("./test_config.json")
    rparams = config["radio_parameters"]
    assert cfg.radio_parameters.modulation.value == rparams.get("modulation")
    assert cfg.radio_parameters.frequency == rparams.get("frequency")
    assert cfg.radio_parameters.spread_factor == rparams.get("spread_factor")
    assert cfg.radio_parameters.coding_rate.value == rparams.get("coding_rate")
    assert cfg.radio_parameters.bandwidth == rparams.get("bandwidth")
    assert cfg.radio_parameters.preamble_len == rparams.get("preamble_len")
    assert cfg.radio_parameters.cyclic_redundancy == rparams.get("cyclic_redundancy")
    assert cfg.radio_parameters.iqi == rparams.get("iqi")
    assert cfg.radio_parameters.sync_word == rparams.get("sync_word")[2:]  # type: ignore
    assert cfg.approved_callsigns == config["approved_callsigns"]

    # Teardown
    os.remove("./test_config.json")
