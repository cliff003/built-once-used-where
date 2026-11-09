#!/usr/bin/env python3
"""Build a PDF from a paper Markdown file with python-markdown and headless Chrome (COLLAB-006, 2026-11-05).

The earlier drafts were printed with headless Chrome too, but their build script was not kept in the project.

Usage: python3 -I build_pdf.py PAPER_FINAL.md PAPER_FINAL.pdf [--repo URL]
  --repo   public repository URL put in place of the {{REPO}} token. Without it the text says
           "the repository linked from the Writeup".

Needs: python3 with the `markdown` package, Google Chrome. Writes <pdf>.html next to the PDF only with --keep-html.
Images are embedded as data URIs, so the result does not depend on where the Markdown lives.
"""
import argparse
import base64
import mimetypes
import os
import re
import subprocess
import sys
import tempfile

import markdown

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = r"""
@page { size: Letter; margin: 2.1cm 2.3cm 2.2cm;
  @bottom-center { content: counter(page); font: 9pt "Charter", Georgia, serif; color: #444; } }
html { font-size: 10.5pt; }
body { font-family: "Charter", "Georgia", "Times New Roman", serif; line-height: 1.38; color: #111; margin: 0;
  overflow-wrap: break-word; hyphens: manual; }
a { overflow-wrap: anywhere; }
h1 { font-size: 20pt; line-height: 1.2; margin: 0 0 0.35em; font-weight: 700; }
h2 { font-size: 13pt; margin: 1.3em 0 0.45em; break-after: avoid; }
p { margin: 0.5em 0; }
ul, ol { margin: 0.35em 0 0.55em; padding-left: 1.35em; }
li { margin: 0.18em 0; }
li > ul, li > ol { margin: 0.2em 0 0.25em; }
p:has(+ ul), p:has(+ ol), p:has(+ table), p:has(+ p > img), p.runin-head { break-after: avoid; }
p:has(> img) { break-after: avoid; }  /* a figure stays with its caption (2026-11-09) */
li:has(> ol) { break-inside: avoid; }  /* a lead-in item ("We add two things:") stays with its numbered list (2026-11-09) */
code { font-family: "Menlo", monospace; font-size: 0.83em; overflow-wrap: anywhere; }
a { color: #0b3d91; text-decoration: none; }
table { border-collapse: collapse; width: 100%; margin: 0.55em 0 0.9em; font-size: 8.8pt; line-height: 1.28; }
th { text-align: left; border-top: 1.2px solid #111; border-bottom: 0.7px solid #111; padding: 3px 5px; font-weight: 600; vertical-align: bottom; }
td { border-bottom: 0.3px solid #bbb; padding: 2.6px 5px; vertical-align: top; }
tbody tr:last-child td { border-bottom: 1.2px solid #111; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
img { max-width: 100%; height: auto; display: block; margin: 0.45em auto; break-inside: avoid; }
img[src^="data:image/png"] { image-rendering: pixelated; }
.authors { font-size: 11.5pt; margin: 0 0 0.15em; }
.keynote { border-top: 0.7px solid #111; border-bottom: 0.7px solid #111; padding: 0.35em 0; margin: 0.7em 0 0.2em; font-size: 9.6pt; }
.keynote p { margin: 0.35em 0; }
blockquote { margin: 0.8em 0; padding: 0.35em 0.9em 0.3em; border: 0.8px solid #8a8984; border-radius: 4px; background: #f6f5f2; break-inside: avoid; }  /* the takeaways box (2026-11-09) */
blockquote p { margin: 0.3em 0; } blockquote ul { margin: 0.2em 0 0.3em; }
.refs { font-size: 0.93em; line-height: 1.32; } .refs li { margin: 0.1em 0; } .refs p { margin: 0.4em 0; }  /* the reference list, set a little smaller (2026-11-09) */
math { font-family: "STIX Two Math", math; font-size: 1.06em; }
math[display="block"] { margin: 0.3em 0 0.45em; break-before: avoid; break-after: avoid; }
"""


# Math (2026-11-09): $...$ inline and $$...$$ display in the Markdown hold a small TeX subset, written out here as
# MathML, which Chrome renders natively. Anything outside the subset stops the build. Code spans are left alone.
TEX_CMD = {r"\lambda": "<mi>λ</mi>", r"\ell": "<mi>ℓ</mi>", r"\Delta": '<mi mathvariant="normal">Δ</mi>',
           r"\min": "<mi>min</mi>", r"\,": '<mspace width="0.1667em"></mspace>'}
TEX_OP = {"=": "<mo>=</mo>", "+": "<mo>+</mo>", "-": "<mo>−</mo>", ",": "<mo>,</mo>", ".": "<mo>.</mo>",
          "/": '<mo lspace="0" rspace="0">/</mo>',  # a tight solidus, as in TeX
          **{d: f'<mo stretchy="false">{d}</mo>' for d in "()[]"}}  # plain brackets keep their size; \bigl/\bigr set it


def tex_to_mathml(tex, display):
    toks = re.findall(r"\\[A-Za-z]+|\\,|[{}^_]|[0-9]+(?:\.[0-9]+)?|[A-Za-z]|[=+\-,/()\[\].]|\s+", tex)
    assert "".join(toks) == tex, f"unsupported TeX: {tex!r}"
    toks = [t for t in toks if not t.isspace()]
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        pos[0] += 1
        return toks[pos[0] - 1]

    def group():
        if peek() == "{":
            take()
            items = seq("}")
            take()
            return items[0] if len(items) == 1 else "<mrow>" + "".join(items) + "</mrow>"
        return atom()

    def atom():
        t = take()
        if t == "{":
            items = seq("}")
            take()
            return "<mrow>" + "".join(items) + "</mrow>"
        if t == r"\frac":
            return f"<mfrac>{group()}{group()}</mfrac>"
        if t == r"\mathbb":
            assert [take(), take(), take()] == ["{", "E", "}"], tex
            return "<mi>𝔼</mi>"
        if t in (r"\bigl", r"\bigr"):
            d = take()
            assert d in "()[]", tex
            return f'<mo stretchy="true" symmetric="true" minsize="1.2em" maxsize="1.2em">{d}</mo>'
        if t in TEX_CMD:
            return TEX_CMD[t]
        if t[0].isdigit():
            return f"<mn>{t}</mn>"
        if len(t) == 1 and t.isalpha():
            return f"<mi>{t}</mi>"
        if t in TEX_OP:
            return TEX_OP[t]
        raise ValueError(f"unsupported TeX token {t!r} in {tex!r}")

    def seq(end=None):
        items = []
        while peek() is not None and peek() != end:
            base, sub, sup = atom(), None, None
            while peek() in ("^", "_"):
                if take() == "^":
                    sup = group()
                else:
                    sub = group()
            if sub and sup:
                base = f"<msubsup>{base}{sub}{sup}</msubsup>"
            elif sub:
                base = f"<msub>{base}{sub}</msub>"
            elif sup:
                base = f"<msup>{base}{sup}</msup>"
            items.append(base)
        return items

    body = "".join(seq())
    assert pos[0] == len(toks), f"unparsed TeX: {tex!r}"
    return f'<math{" display=\"block\"" if display else ""}><mrow>{body}</mrow></math>'


def convert_math(md):
    """Swap each formula for a placeholder that python-markdown leaves alone; returns the text and the MathML."""
    stash, out, fence = [], [], False

    def put(html):
        stash.append(html)
        return f"MATHSTASH{len(stash) - 1}X"
    for line in md.split("\n"):
        if line.startswith("```"):
            fence = not fence
        elif not fence and "$" in line:
            parts = re.split(r"(`[^`]*`)", line)
            for i in range(0, len(parts), 2):
                parts[i] = re.sub(r"\$\$(.+?)\$\$", lambda m: put(tex_to_mathml(m.group(1), True)), parts[i])
                parts[i] = re.sub(r"\$([^$]+?)\$", lambda m: put(tex_to_mathml(m.group(1), False)), parts[i])
            line = "".join(parts)
        out.append(line)
    return "\n".join(out), stash


def fix_lists(md):
    """python-markdown wants a blank line before a list and 4-space nesting; the paper uses neither."""
    out = []
    in_fence = False
    item = re.compile(r"^( *)([-*]|\d+\.) ")
    for line in md.split("\n"):
        if line.startswith("```"):
            in_fence = not in_fence
        if in_fence:
            out.append(line)
            continue
        m = item.match(line)
        if m:
            line = " " * (len(m.group(1)) * 2) + line[len(m.group(1)):]
            if out and out[-1].strip() and not item.match(out[-1]) and not out[-1].startswith(" "):
                out.append("")
        out.append(line)
    return "\n".join(out)


def embed_images(html, base):
    def repl(m):
        path = os.path.normpath(os.path.join(base, m.group(1)))
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        data = base64.b64encode(open(path, "rb").read()).decode()
        return f'src="data:{mime};base64,{data}"'
    return re.sub(r'src="(?!data:|https?:)([^"]+)"', repl, html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("pdf")
    ap.add_argument("--repo", default="")
    ap.add_argument("--keep-html", action="store_true")
    a = ap.parse_args()
    src = open(a.md, encoding="utf-8").read()
    repo = f"<{a.repo}>" if a.repo else "the repository linked from the Writeup"
    src = src.replace("{{REPO}}", repo)
    src, math = convert_math(src)
    assert "{{" not in src, "unfilled token"
    title = src.split("\n", 1)[0].lstrip("# ").strip()
    body = markdown.markdown(fix_lists(src), extensions=["tables", "fenced_code", "sane_lists"], output_format="html5")
    # Lead-in block: the author line and the two notes above the abstract.
    body = re.sub(r"(<h1>.*?</h1>\s*)<p>(.*?)</p>", r'\1<p class="authors">\2</p>', body, count=1, flags=re.S)
    m = re.search(r"(<p>ARC Prize 2026 Paper Track.*?)(<h2>Abstract</h2>)", body, flags=re.S)
    assert m, "lead-in block not found"
    body = body[:m.start()] + '<div class="keynote">' + m.group(1) + "</div>" + m.group(2) + body[m.end():]
    # A paragraph that is only a bold heading ("**E. Decode headroom …**") stays with what follows (2026-11-08).
    body = re.sub(r"<p>(<strong>[^<]*</strong>)</p>", r'<p class="runin-head">\1</p>', body)
    body = re.sub(r"([λwhs])_ℓ", r"\1<sub>ℓ</sub>", body)
    body = re.sub(r"MATHSTASH(\d+)X", lambda m: math[int(m.group(1))], body)
    assert "MATHSTASH" not in body, "math placeholder left"
    assert body.count("<h2>References</h2>") == 1
    body = body.replace("<h2>References</h2>", '<h2>References</h2><div class="refs">') + "</div>"
    body = re.sub(r"<td>(ARC-AGI-[23])</td>", r'<td style="white-space:nowrap">\1</td>', body)
    body = embed_images(body, os.path.dirname(os.path.abspath(a.md)))
    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><meta name="author" content="Kaggle team 42"><style>{CSS}</style></head><body>{body}</body></html>'
    with tempfile.TemporaryDirectory() as tmp:
        hp = os.path.join(tmp, "paper.html")
        open(hp, "w", encoding="utf-8").write(html)
        if a.keep_html:
            open(a.pdf + ".html", "w", encoding="utf-8").write(html)
        if os.path.exists(a.pdf):
            os.remove(a.pdf)
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={os.path.join(tmp, 'prof')}", "--no-pdf-header-footer",
               "--generate-pdf-document-outline", f"--print-to-pdf={os.path.abspath(a.pdf)}", "file://" + hp]
        # On this Mac Chrome writes the PDF and then often exits 2 ("Teardown watchdog expired"), so the exit code
        # says nothing: judge by the file.
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        except subprocess.TimeoutExpired:
            pass
    pdf = open(a.pdf, "rb").read()
    assert pdf.startswith(b"%PDF") and pdf.rstrip().endswith(b"%%EOF"), "incomplete PDF"
    print(a.pdf, f"{len(pdf) / 1024:.0f} KiB; pages:", re.findall(rb"/Count (\d+)", pdf)[:1], "title:", re.findall(rb"/Title ?\((.*?)\)", pdf)[:1])


if __name__ == "__main__":
    sys.exit(main())
