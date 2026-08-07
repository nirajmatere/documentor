import pytest
from typer.testing import CliRunner
from documentor.cli.main import app
import importlib.metadata

runner = CliRunner()

def test_version(monkeypatch):
    # Mock the version to be deterministic
    monkeypatch.setattr(importlib.metadata, "version", lambda x: "0.1.22")
    
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Documentor version: 0.1.22" in result.stdout

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Documentor: Enterprise-grade AI documentation suite" in result.stdout or "Documentor: A powerful AI documentation suite" in result.stdout
    assert "generate" in result.stdout
    assert "chat" in result.stdout
    assert "serve" in result.stdout
    assert "configure" in result.stdout

def test_configure(monkeypatch, tmp_path):
    # Point CONFIG_FILE to a temporary file
    monkeypatch.setattr("documentor.cli.main.CONFIG_FILE", tmp_path / "config.env")
    monkeypatch.setattr("documentor.cli.main.CONFIG_DIR", tmp_path)
    
    # Simulate pressing enter 4 times
    result = runner.invoke(app, ["configure"], input="\n\n\n\n")
    
    assert result.exit_code == 0
    assert "Configuration saved successfully" in result.stdout
    assert (tmp_path / "config.env").exists()

def test_generate_missing_dir():
    result = runner.invoke(app, ["generate", "/path/that/does/not/exist"])
    assert result.exit_code == 1
    assert "Error: Directory '/path/that/does/not/exist' does not exist" in result.stdout

def test_chat_no_vector_db(tmp_path):
    result = runner.invoke(app, ["chat", "How does this work?", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "Error: Vector store not found" in result.stdout
