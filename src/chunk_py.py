"""Python: ast ile module/class/method/function parçaları (satırlar 1-tabanlı, dahil)."""
import ast

from . import config
from .chunk import CodeChunk

MODULE = "<module>"

# (kind, symbol, signature, start, end) — bölmeden önceki ham aralık
_Span = tuple[str, str, str, int, int]


def _start(node: ast.AST) -> int:
    decs = getattr(node, "decorator_list", None) or []
    return min([node.lineno] + [d.lineno for d in decs])


def _signature(node: ast.AST) -> str:
    try:
        if isinstance(node, ast.ClassDef):
            args = [ast.unparse(b) for b in node.bases]
            args += [ast.unparse(k) for k in node.keywords]
            return f"class {node.name}" + (f"({', '.join(args)})" if args else "")
        pre = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        return f"{pre} {node.name}({ast.unparse(node.args)}){ret}"
    except Exception:  # unparse beklenmedik düğümde patlarsa
        return f"def {node.name}" if not isinstance(node, ast.ClassDef) else f"class {node.name}"


def _is_def(node: ast.AST) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))


def _runs(lo: int, hi: int, covered: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """[lo,hi] içinde covered aralıklarına girmeyen ardışık satır blokları."""
    out, cur = [], lo
    for s, e in sorted(covered):
        if s > cur:
            out.append((cur, s - 1))
        cur = max(cur, e + 1)
    if cur <= hi:
        out.append((cur, hi))
    return out


def _has_code(lines: list[str], s: int, e: int) -> bool:
    """Boş ya da yalnız yorum olan blokları elemek için."""
    return any(ln.strip() and not ln.lstrip().startswith("#") for ln in lines[s - 1:e])


def _spans_for_class(node: ast.ClassDef, prefix: str, lines: list[str]) -> list[_Span]:
    sym = prefix + node.name
    sig = _signature(node)
    s, e = _start(node), node.end_lineno
    if e - s + 1 <= config.MAX_CHUNK_LINES:
        return [("class", sym, sig, s, e)]
    # Uzun sınıf: metotlar (ve iç sınıflar) ayrı, kalan satırlar sınıf başı
    spans, covered = [], []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.append(("method", f"{sym}.{child.name}", _signature(child),
                          _start(child), child.end_lineno))
            covered.append((_start(child), child.end_lineno))
        elif isinstance(child, ast.ClassDef):
            spans += _spans_for_class(child, sym + ".", lines)
            covered.append((_start(child), child.end_lineno))
    for rs, re_ in _runs(s, e, covered):
        if rs == s or _has_code(lines, rs, re_):
            spans.append(("class", sym, sig, rs, re_))
    return spans


def _split(s: int, e: int, breaks: set[int], has_header: bool) -> list[tuple[int, int]]:
    """[s,e]'yi MAX_CHUNK_LINES'lık parçalara böler; mümkünse breaks satırlarından."""
    mx = config.MAX_CHUNK_LINES
    parts, cur = [], s
    while cur <= e:
        win = mx if not parts or not has_header else mx - 1  # başlık satırına yer
        limit = cur + win - 1
        if e <= limit:
            parts.append((cur, e))
            break
        cands = [b for b in breaks if cur + win // 2 < b <= limit + 1]
        nxt = max(cands) if cands else limit + 1
        parts.append((cur, nxt - 1))
        cur = nxt
    return parts


def _trim(lines: list[str], s: int, e: int) -> tuple[int, int]:
    while s <= e and not lines[s - 1].strip():
        s += 1
    while e >= s and not lines[e - 1].strip():
        e -= 1
    return s, e


def _fallback_spans(lines: list[str]) -> tuple[list[_Span], set[int]]:
    breaks = {i + 2 for i, ln in enumerate(lines) if not ln.strip()}  # boş satırdan sonra
    return [("module", MODULE, "", 1, len(lines))], breaks


def chunk_python(rel: str, text: str) -> list[CodeChunk]:
    lines = text.splitlines()
    if not lines:
        return []
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        spans, breaks = _fallback_spans(lines)
    else:
        spans, covered = [], []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                spans += _spans_for_class(node, "", lines)
            elif _is_def(node):
                spans.append(("function", node.name, _signature(node),
                              _start(node), node.end_lineno))
            else:
                continue
            covered.append((_start(node), node.end_lineno))
        for rs, re_ in _runs(1, len(lines), covered):
            if _has_code(lines, rs, re_):
                spans.append(("module", MODULE, "", rs, re_))
        # Bölme noktaları: deyim başları (decorator'lı tanımlarda ilk decorator)
        breaks = {_start(n) for n in ast.walk(tree) if isinstance(n, ast.stmt)}

    raw = []  # (start, end, kind, symbol, sig, part_no, text)
    for kind, sym, sig, s, e in spans:
        s, e = _trim(lines, s, e)
        if s > e:
            continue
        header = bool(sig)
        for part, (ps, pe) in enumerate(_split(s, e, breaks, header)):
            ps, pe = _trim(lines, ps, pe)
            if ps > pe:
                continue
            body = "\n".join(lines[ps - 1:pe])
            txt = f"{sig}\n{body}" if part and header else body
            raw.append((ps, pe, kind, sym, sig, part, txt))

    raw.sort(key=lambda r: (r[0], r[1]))
    chunks, seen = [], {}
    for ps, pe, kind, sym, sig, part, txt in raw:
        base = f"{rel}::{sym}" + (f"#{part + 1}" if part else "")
        seen[base] = seen.get(base, 0) + 1
        cid = base if seen[base] == 1 else f"{base}~{seen[base]}"
        chunks.append(CodeChunk(cid, rel, "python", kind, sym, sig, ps, pe, txt))
    return chunks
