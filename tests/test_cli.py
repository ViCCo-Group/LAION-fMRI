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
