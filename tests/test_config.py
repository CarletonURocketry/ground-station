# Tests config module for accurate loading, error checking and default values
__author__ = "Matteo Golin"

# Imports
import pytest

from modules.misc.config import CodingRates, Config, RadioParameters


# Fixtures
@pytest.fixture()
def default_radio_parameters():
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


# Test radio parameters
def test_radio_params_default(default_radio_parameters):
    """Tests that the RadioParameters object default constructor initializes all values to the correct defaults."""
    params = RadioParameters()
    defaults = default_radio_parameters()
    assert params.modulation.value == defaults.get("modulation")
    assert params.frequency == defaults.get("frequency")
    assert params.spread_factor == defaults.get("spread_factor")
    assert params.coding_rate.value == defaults.get("coding_rate")
    assert params.bandwidth == defaults.get("bandwidth")
    assert params.preamble_len == defaults.get("preamble_len")
    assert params.cyclic_redundancy == defaults.get("cyclic_redundancy")
    assert params.iqi == defaults.get("iqi")
    assert params.sync_word == defaults.get("sync_word")


def test_radio_params_partial_default():
    """
    Tests that the RadioParameters object default constructor initializes all non-specified values to the correct
    defaults, and specified values to the passed values.
    """
    params = RadioParameters(
        sync_word="0x13", power=12, coding_rate=CodingRates.FOUR_FIFTHS
    )
    assert params.sync_word == "0x13"
    assert params.power == 12
    assert params.coding_rate == CodingRates.FOUR_FIFTHS


def test_radio_params_default_json(default_radio_parameters):
    """
    Tests that the RadioParameters object's from_json method initializes all values to the correct defaults when given
    no radio_params JSON object.
    """
    params = RadioParameters.from_json(dict())
    defaults = default_radio_parameters()
    assert params.modulation.value == defaults.get("modulation")
    assert params.frequency == defaults.get("frequency")
    assert params.spread_factor == defaults.get("spread_factor")
    assert params.coding_rate.value == defaults.get("coding_rate")
    assert params.bandwidth == defaults.get("bandwidth")
    assert params.preamble_len == defaults.get("preamble_len")
    assert params.cyclic_redundancy == defaults.get("cyclic_redundancy")
    assert params.iqi == defaults.get("iqi")
    assert params.sync_word == defaults.get("sync_word")


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
    assert params.sync_word == "0x13"
    assert params.power == 12
    assert params.coding_rate == CodingRates.FOUR_FIFTHS


def test_radio_params_invalid_arguments():
    """
    Tests that initializing a RadioParameters object using invalid parameters will raise a value error.
    """

    with pytest.raises(ValueError):
        RadioParameters(frequency=42)

    with pytest.raises(ValueError):
        RadioParameters(power=18)

    with pytest.raises(ValueError):
        RadioParameters(spread_factor=6)

    with pytest.raises(ValueError):
        RadioParameters(preamble_len=65536)

    with pytest.raises(ValueError):
        RadioParameters(sync_word="0x101")

def test_radio_params_invalid_arguments_json():
    """
    Tests that initializing a RadioParameters object using invalid parameters from a JSON schema will raise a
    ValueError.
    """

    with pytest.raises(ValueError):
        RadioParameters.from_json({"frequency": 42})

    with pytest.raises(ValueError):
        RadioParameters.from_json({"power": 18})

    with pytest.raises(ValueError):
        RadioParameters.from_json({"spread_factor": 6})

    with pytest.raises(ValueError):
        RadioParameters.from_json({"preamble_len": 65536})
    
    with pytest.raises(ValueError):
        RadioParameters.from_json({"sync_word": "0x101"})


def test_radio_params_range_edges():
    """
    Tests that initializing a RadioParameters object with values right at the end of the accepted ranges
    does not raise any exceptions.
    """

    RadioParameters(power=-3)
    RadioParameters(power=16)

    RadioParameters(sync_word="0x0")
    RadioParameters(sync_word="0x100")

    RadioParameters(preamble_len=0)
    RadioParameters(preamble_len=65_535)

    RadioParameters(frequency=433_050_000)
    RadioParameters(frequency=434_790_000)
    RadioParameters(frequency=863_000_000)
    RadioParameters(frequency=870_000_000)

def test_radio_params_outside_range_edges():
    """
    Tests that initializing a RadioParameters object with values just outside the end of the accepted ranges
    raises a ValueError.
    """

    with pytest.raises(ValueError):
        RadioParameters(power=-4)

    with pytest.raises(ValueError):
        RadioParameters(power=17)

    with pytest.raises(ValueError):
        RadioParameters(sync_word="0x101")

    with pytest.raises(ValueError):
        RadioParameters(preamble_len=-1) 

