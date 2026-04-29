import json

from laion_fmri._cli import main


def test_cli_config_sets_data_dir(tmp_path, monkeypatch):
    data_dir = tmp_path / "cli_data"
    data_dir.mkdir()

    config_home = tmp_path / "cli_config"
    config_home.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    main(["config", "--data-dir", str(data_dir)])

    config_file = config_home / "laion_fmri" / "config.json"
    assert config_file.exists()
    config = json.loads(config_file.read_text())
    assert config["data_dir"] == str(data_dir)


def test_cli_no_args_shows_help(capsys):
    main([])
    captured = capsys.readouterr()
    out = captured.out.lower()
    assert "usage" in out or "laion-fmri" in out


def test_cli_help_shows_usage(capsys):
    import pytest
    with pytest.raises(SystemExit, match="0"):
        main(["--help"])


# ── download subcommand: BIDS-entity filter forwarding ──────────


def _capture_download(monkeypatch):
    """Replace download() with a recorder; return the captured-kwargs dict."""
    captured = {}

    def fake_download(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        "laion_fmri.download.download", fake_download,
    )
    return captured


def test_cli_download_passes_subject_only(monkeypatch):
    captured = _capture_download(monkeypatch)
    main(["download", "--subject", "sub-03"])
    assert captured["subject"] == "sub-03"
    assert captured.get("ses") is None
    assert captured.get("task") is None
    assert captured.get("space") is None
    assert captured.get("desc") is None
    assert captured.get("stat") is None
    assert captured.get("suffix") is None
    assert captured.get("extension") is None
    assert captured["include_stimuli"] is False
    assert captured["n_jobs"] == 1


def test_cli_download_passes_ses_single_value(monkeypatch):
    captured = _capture_download(monkeypatch)
    main(["download", "--subject", "sub-03", "--ses", "ses-01"])
    assert captured["ses"] == ["ses-01"]


def test_cli_download_passes_ses_multiple_values(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--ses", "ses-01", "ses-02",
    ])
    assert captured["ses"] == ["ses-01", "ses-02"]


def test_cli_download_passes_ses_averages(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--ses", "averages",
    ])
    assert captured["ses"] == ["averages"]


def test_cli_download_passes_task(monkeypatch):
    captured = _capture_download(monkeypatch)
    main(["download", "--subject", "sub-03", "--task", "images"])
    assert captured["task"] == ["images"]


def test_cli_download_passes_space(monkeypatch):
    captured = _capture_download(monkeypatch)
    main(["download", "--subject", "sub-03", "--space", "T1w"])
    assert captured["space"] == ["T1w"]


def test_cli_download_passes_desc(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--desc", "singletrial",
    ])
    assert captured["desc"] == ["singletrial"]


def test_cli_download_passes_stat(monkeypatch):
    captured = _capture_download(monkeypatch)
    main(["download", "--subject", "sub-03", "--stat", "effect"])
    assert captured["stat"] == ["effect"]


def test_cli_download_passes_suffix(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--suffix", "statmap",
    ])
    assert captured["suffix"] == ["statmap"]


def test_cli_download_passes_extension(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--extension", "nii.gz",
    ])
    assert captured["extension"] == ["nii.gz"]


def test_cli_download_passes_n_jobs(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--n-jobs", "4",
    ])
    assert captured["n_jobs"] == 4


def test_cli_download_passes_include_stimuli(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--include-stimuli",
    ])
    assert captured["include_stimuli"] is True


def test_cli_download_passes_all_filters_combined(monkeypatch):
    captured = _capture_download(monkeypatch)
    main([
        "download", "--subject", "sub-03",
        "--ses", "ses-01", "ses-02",
        "--task", "images",
        "--space", "T1w",
        "--desc", "singletrial",
        "--stat", "effect",
        "--suffix", "statmap",
        "--extension", "nii.gz",
        "--n-jobs", "2",
        "--include-stimuli",
    ])
    assert captured["subject"] == "sub-03"
    assert captured["ses"] == ["ses-01", "ses-02"]
    assert captured["task"] == ["images"]
    assert captured["space"] == ["T1w"]
    assert captured["desc"] == ["singletrial"]
    assert captured["stat"] == ["effect"]
    assert captured["suffix"] == ["statmap"]
    assert captured["extension"] == ["nii.gz"]
    assert captured["n_jobs"] == 2
    assert captured["include_stimuli"] is True
