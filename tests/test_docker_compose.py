from pathlib import Path


def test_compose_defines_local_ai_stack_with_gpu_reservation():
    compose = Path("compose.yaml").read_text()

    assert "app:" in compose
    assert "ollama:" in compose
    assert "127.0.0.1:11434:11434" in compose
    assert "driver: nvidia" in compose
    assert "capabilities: [gpu]" in compose
    assert "OLLAMA_BASE_URL: http://ollama:11434" in compose


def test_compose_keeps_local_state_and_secrets_out_of_mounts():
    compose = Path("compose.yaml").read_text()
    env_example = Path(".env.example").read_text()
    dockerignore = Path(".dockerignore").read_text()

    assert ".omx" not in compose
    assert "MINIMAX_API_KEY: ${MINIMAX_API_KEY:-}" in compose
    assert "MINIMAX_API_KEY=" in env_example
    assert "sk-" not in env_example.lower()
    assert ".env" in dockerignore
    assert "models" in dockerignore
    assert ".omx" in dockerignore


def test_docker_docs_have_traditional_chinese_counterpart():
    assert Path("docs/docker-compose-ai-stack.md").exists()
    zh = Path("docs/docker-compose-ai-stack.zh-TW.md")

    assert zh.exists()
    assert "Docker Compose 本機 AI Stack" in zh.read_text()
