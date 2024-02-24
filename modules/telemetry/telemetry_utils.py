from pathlib import Path


def mission_path(mission_name: str, missions_dir: Path, file_suffix: int = 0) -> Path:
    """Returns the path to the mission file with the matching mission name."""

    return missions_dir.joinpath(f"{mission_name}{'' if file_suffix == 0 else f'_{file_suffix}'}.{MISSION_EXTENSION}")
