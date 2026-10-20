"""Testes OFFLINE do `make bonde` e do `make gabarito-aula`.

Garantem que o atalho funciona nos dois tipos de fork da turma:

* fork completo, com o branch `solucoes` (o gabarito vem do próprio fork);
* fork criado com "Copy the main branch only", sem `solucoes` (o gabarito vem
  do repositório do curso, pelo endereço em ``GABARITO_URL``).

Tudo roda em repositórios git temporários, sem internet e sem chave.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or shutil.which("make") is None,
    reason="precisa de git e make instalados",
)

# Arquivos que o `bonde` traz para AULA=2 (os da Aula 1, ver ARQ_AULA1 no Makefile).
ARQUIVOS_AULA1 = [
    "opspilot/tools.py",
    "opspilot/prompts.py",
    "opspilot/agente_react.py",
    "aulas/aula1/a1_01_llm_vs_agente.py",
]


def _git(*args: str, cwd: Path) -> str:
    comando = ["git", "-c", "user.name=teste", "-c", "user.email=teste@exemplo.com", *args]
    return subprocess.run(comando, cwd=cwd, check=True, capture_output=True, text=True).stdout


def _make(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["make", "-s", *args], cwd=cwd, capture_output=True, text=True)


def _escrever(raiz: Path, conteudo: str) -> None:
    for caminho in ARQUIVOS_AULA1:
        arquivo = raiz / caminho
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(conteudo, encoding="utf-8")


@pytest.fixture()
def oficial(tmp_path: Path) -> Path:
    """Repositório "do curso": main com lacunas e solucoes com o gabarito."""
    repo = tmp_path / "oficial"
    repo.mkdir()
    _git("init", "-q", "-b", "main", cwd=repo)
    shutil.copy(RAIZ / "Makefile", repo / "Makefile")
    _escrever(repo, "valor = ___\n")
    _git("add", "-A", cwd=repo)
    _git("commit", "-q", "-m", "lacunas", cwd=repo)
    _git("checkout", "-q", "-b", "solucoes", cwd=repo)
    _escrever(repo, "valor = 'gabarito'\n")
    _git("commit", "-q", "-am", "gabarito", cwd=repo)
    _git("checkout", "-q", "main", cwd=repo)
    return repo


def _aluno(tmp_path: Path, oficial: Path, *, so_main: bool) -> Path:
    """Simula o fork no GitHub e o clone do aluno no Codespace."""
    fork = tmp_path / ("fork_so_main.git" if so_main else "fork_completo.git")
    extra = ["--single-branch", "--branch", "main"] if so_main else []
    _git("clone", "-q", "--bare", *extra, str(oficial), str(fork), cwd=tmp_path)
    aluno = tmp_path / ("aluno_so_main" if so_main else "aluno_completo")
    _git("clone", "-q", str(fork), str(aluno), cwd=tmp_path)
    return aluno


def test_bonde_em_fork_sem_solucoes_busca_no_repositorio_do_curso(tmp_path, oficial):
    aluno = _aluno(tmp_path, oficial, so_main=True)
    assert "solucoes" not in _git("ls-remote", "--heads", "origin", cwd=aluno)

    resultado = _make("bonde", "AULA=2", f"GABARITO_URL={oficial}", cwd=aluno)

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "repositório do curso" in resultado.stdout
    assert (aluno / "opspilot/tools.py").read_text(encoding="utf-8") == "valor = 'gabarito'\n"


def test_bonde_em_fork_completo_usa_o_proprio_fork(tmp_path, oficial):
    aluno = _aluno(tmp_path, oficial, so_main=False)

    # Endereço inválido de propósito: se o bonde usasse o repositório do curso, falharia.
    resultado = _make("bonde", "AULA=2", f"GABARITO_URL={tmp_path / 'nao-existe.git'}", cwd=aluno)

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert (aluno / "opspilot/tools.py").read_text(encoding="utf-8") == "valor = 'gabarito'\n"


def test_bonde_sem_acesso_ao_gabarito_avisa_e_falha(tmp_path, oficial):
    aluno = _aluno(tmp_path, oficial, so_main=True)

    resultado = _make("bonde", "AULA=2", f"GABARITO_URL={tmp_path / 'nao-existe.git'}", cwd=aluno)

    assert resultado.returncode != 0
    assert "Não consegui baixar o gabarito" in resultado.stdout
    assert "___" in (aluno / "opspilot/tools.py").read_text(encoding="utf-8")  # nada foi sobrescrito


def test_gabarito_aula_funciona_em_fork_sem_solucoes(tmp_path, oficial):
    aluno = _aluno(tmp_path, oficial, so_main=True)

    resultado = _make("gabarito-aula", "AULA=1", f"GABARITO_URL={oficial}", cwd=aluno)

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "valor = 'gabarito'" in resultado.stdout
