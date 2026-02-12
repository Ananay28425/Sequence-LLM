import pytest
import tempfile
import os
from pathlib import Path
from seq_llm.config import Config, ModelConfig, ServerConfig


class TestModelConfig:
    """Test ModelConfig class"""

    def test_model_config_creation(self):
        """Test creating a ModelConfig instance"""
        config = ModelConfig(
            name="test-model", model_type="ollama", endpoint="http://localhost:11434", api_key=None
        )
        assert config.name == "test-model"
        assert config.model_type == "ollama"
        assert config.endpoint == "http://localhost:11434"
        assert config.api_key is None

    def test_model_config_with_api_key(self):
        """Test ModelConfig with API key"""
        config = ModelConfig(
            name="gpt-4",
            model_type="openai",
            endpoint="https://api.openai.com/v1",
            api_key="sk-test-key",
        )
        assert config.api_key == "sk-test-key"


class TestServerConfig:
    """Test ServerConfig class"""

    def test_server_config_creation(self):
        """Test creating a ServerConfig instance"""
        config = ServerConfig(host="127.0.0.1", port=8000, workers=4)
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.workers == 4

    def test_server_config_defaults(self):
        """Test ServerConfig default values"""
        config = ServerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.workers == 1


class TestConfig:
    """Test main Config class"""

    def test_config_from_dict(self):
        """Test creating Config from dictionary"""
        config_dict = {
            "server": {"host": "0.0.0.0", "port": 9000, "workers": 2},
            "models": [
                {
                    "name": "llama2",
                    "model_type": "ollama",
                    "endpoint": "http://localhost:11434",
                    "api_key": None,
                }
            ],
        }
        config = Config.from_dict(config_dict)
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 9000
        assert len(config.models) == 1
        assert config.models[0].name == "llama2"

    def test_config_from_yaml(self):
        """Test loading Config from YAML file"""
        yaml_content = """
server:
  host: 127.0.0.1
  port: 8000
  workers: 4

models:
  - name: ollama-model
    model_type: ollama
    endpoint: http://localhost:11434
    api_key: null
  - name: openai-model
    model_type: openai
    endpoint: https://api.openai.com/v1
    api_key: sk-test-key
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()

            try:
                config = Config.from_yaml(f.name)
                assert config.server.host == "127.0.0.1"
                assert config.server.port == 8000
                assert config.server.workers == 4
                assert len(config.models) == 2
                assert config.models[0].name == "ollama-model"
                assert config.models[1].name == "openai-model"
            finally:
                os.unlink(f.name)

    def test_config_get_model(self):
        """Test getting a model by name"""
        config = Config(
            server=ServerConfig(),
            models=[
                ModelConfig(name="model1", model_type="ollama", endpoint="http://localhost:11434"),
                ModelConfig(
                    name="model2", model_type="openai", endpoint="https://api.openai.com/v1"
                ),
            ],
        )

        model = config.get_model("model1")
        assert model is not None
        assert model.name == "model1"

        model = config.get_model("nonexistent")
        assert model is None

    def test_config_to_dict(self):
        """Test converting Config to dictionary"""
        config = Config(
            server=ServerConfig(host="0.0.0.0", port=9000),
            models=[
                ModelConfig(name="test", model_type="ollama", endpoint="http://localhost:11434")
            ],
        )

        config_dict = config.to_dict()
        assert config_dict["server"]["host"] == "0.0.0.0"
        assert config_dict["server"]["port"] == 9000
        assert len(config_dict["models"]) == 1
        assert config_dict["models"][0]["name"] == "test"


class TestConfigValidation:
    """Test Config validation"""

    def test_invalid_port(self):
        """Test that invalid port raises error"""
        with pytest.raises(ValueError):
            ServerConfig(port=-1)

    def test_invalid_workers(self):
        """Test that invalid worker count raises error"""
        with pytest.raises(ValueError):
            ServerConfig(workers=0)

    def test_empty_model_name(self):
        """Test that empty model name raises error"""
        with pytest.raises(ValueError):
            ModelConfig(name="", model_type="ollama", endpoint="http://localhost:11434")

    def test_empty_model_type(self):
        """Test that empty model type raises error"""
        with pytest.raises(ValueError):
            ModelConfig(name="test", model_type="", endpoint="http://localhost:11434")

    def test_empty_endpoint(self):
        """Test that empty endpoint raises error"""
        with pytest.raises(ValueError):
            ModelConfig(name="test", model_type="ollama", endpoint="")
