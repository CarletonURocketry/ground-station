class MissionNotFoundError(FileNotFoundError):
    """Raised when the desired mission is not found."""

    def __init__(self, mission_name: str):
        self.mission_name = mission_name
        self.message = f"The mission recording '{mission_name}' does not exist."
        super().__init__(self.message)


class AlreadyRecordingError(Exception):
    """Raised if the telemetry process is already recording when instructed to record."""

    def __init__(self, message: str = "Recording is already in progress."):
        self.message: str = message
        super().__init__(self.message)


class ReplayPlaybackError(Exception):
    """Raised if the telemetry process replay system is active when instructed to record or recording."""

    def __init__(self, message: str = "Not recording when replay system is active."):
        self.message: str = message
        super().__init__(self.message)
