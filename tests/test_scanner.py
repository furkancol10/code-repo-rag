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


def test_symlinked_parent_dir_inside_repo_skipped(tmp_path):
    import os
    import subprocess
    repo = tmp_path / "repo"
    _mk(repo, {"ok.py": "x = 1\n", "real/a.py": "y = 1\n", "sub/a.py": "z = 1\n"})
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    # sub/ dizini indekste izli kalır, sonra repo içindeki real/'e symlink'e dönüşür
    (repo / "sub" / "a.py").unlink()
    (repo / "sub").rmdir()
    os.symlink(repo / "real", repo / "sub")
    # sub/a.py git'te izlenir, sub repo içine symlink: bileşen kontrolü atlar
    assert scan_repo(repo) == ["ok.py", "real/a.py"]


def test_inside_root_resolved_escape_without_symlink(tmp_path):
    from src.scanner import _inside_root
    repo = tmp_path / "repo"
    _mk(repo, {"ok.py": "x = 1\n"})
    _mk(tmp_path, {"outside/s.py": "S = 1\n"})
    root_real = repo.resolve()
    # symlink yok, ama '..' çözümlenince kök dışına çıkar: yalnız relative_to yakalar
    assert not _inside_root(root_real, repo / ".." / "outside" / "s.py")
    assert _inside_root(root_real, repo / "ok.py")
