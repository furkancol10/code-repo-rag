from src.scanner import scan_repo


def _mk(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8")


def test_exclusions(tmp_path):
    _mk(tmp_path, {
        "pkg/a.py": "x = 1\n", "README.md": "# Hi\n", "docs/guide.md": "# G\n",
        "tests/test_a.py": "", "pkg/test_b.py": "", "pkg/c_test.py": "",
        "poetry.lock": "x", "uv.lock": "x", "build/gen.py": "", "dist/d.py": "",
        ".venv/lib/v.py": "", "pkg/__pycache__/a.cpython.py": "",
        "node_modules/m/i.md": "# m", "src/data.json": "{}", "src/x.txt": "t",
        "src/bin.py": b"a\0b", "src/big.py": "x = 1\n" * 100_000,
    })
    assert scan_repo(tmp_path) == ["README.md", "docs/guide.md", "pkg/a.py"]


def test_git_repo_uses_ls_files(tmp_path):
    import subprocess
    _mk(tmp_path, {"a.py": "x=1\n", "ignored.py": "y=2\n", ".gitignore": "ignored.py\n",
                   "tests/t.py": ""})
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    assert scan_repo(tmp_path) == ["a.py"]


def test_symlink_escape_skipped(tmp_path):
    import os
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("S = 1\n")
    repo = tmp_path / "repo"
    _mk(repo, {"ok.py": "x = 1\n"})
    os.symlink(outside / "secret.py", repo / "leak.py")
    os.symlink(outside, repo / "linkdir")
    assert scan_repo(repo) == ["ok.py"]


def test_symlink_escape_skipped_git(tmp_path):
    import os
    import subprocess
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.py").write_text("S = 1\n")
    repo = tmp_path / "repo"
    _mk(repo, {"ok.py": "x = 1\n"})
    os.symlink(outside / "secret.py", repo / "leak.py")
    os.symlink(outside, repo / "linkdir")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    assert scan_repo(repo) == ["ok.py"]
