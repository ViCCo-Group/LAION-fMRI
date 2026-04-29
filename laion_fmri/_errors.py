"""Custom exception classes for the laion_fmri package."""


class DataDirNotSetError(Exception):
    """Raised when data directory has not been configured."""


class DataNotDownloadedError(FileNotFoundError):
    """Raised when requested data has not been downloaded."""


class SubjectNotFoundError(ValueError):
    """Raised when an invalid subject ID is provided."""


class StimuliNotDownloadedError(FileNotFoundError):
    """Raised when stimulus data is requested but not downloaded."""


class LicenseNotAcceptedError(RuntimeError):
    """Raised when the dataset license has not been accepted."""
