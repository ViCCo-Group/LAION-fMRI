import pytest

from laion_fmri._errors import (
    DataDirNotSetError,
    DataNotDownloadedError,
    LicenseNotAcceptedError,
    StimuliNotDownloadedError,
    SubjectNotFoundError,
)


def test_data_dir_not_set_error_is_exception():
    assert issubclass(DataDirNotSetError, Exception)


def test_data_not_downloaded_error_is_file_not_found():
    assert issubclass(DataNotDownloadedError, FileNotFoundError)


def test_subject_not_found_error_is_value_error():
    assert issubclass(SubjectNotFoundError, ValueError)


def test_stimuli_not_downloaded_error_is_file_not_found():
    assert issubclass(StimuliNotDownloadedError, FileNotFoundError)


def test_data_dir_not_set_error_can_be_raised():
    with pytest.raises(DataDirNotSetError):
        raise DataDirNotSetError("Data directory not configured.")


def test_data_not_downloaded_error_can_be_raised():
    with pytest.raises(DataNotDownloadedError):
        raise DataNotDownloadedError("sub-01")


def test_subject_not_found_error_can_be_raised():
    with pytest.raises(SubjectNotFoundError):
        raise SubjectNotFoundError("invalid-subject")


def test_stimuli_not_downloaded_error_can_be_raised():
    with pytest.raises(StimuliNotDownloadedError):
        raise StimuliNotDownloadedError("Stimuli not found.")


def test_license_not_accepted_error_is_runtime_error():
    assert issubclass(LicenseNotAcceptedError, RuntimeError)


def test_license_not_accepted_error_can_be_raised():
    with pytest.raises(LicenseNotAcceptedError):
        raise LicenseNotAcceptedError("License not accepted.")
