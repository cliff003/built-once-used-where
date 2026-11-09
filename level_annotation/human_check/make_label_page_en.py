"""Make blind_label.en.html, an English rendering of the blind-labelling page (2026-11-09).

blind_label.html is the page the two human annotators used. build_label_page.py --offline built it, and its interface,
including the S/V/N definitions, is in Chinese; both files stay unchanged. This script copies the page, replaces each
Chinese interface string with English (PAIRS below: the Chinese is written with \\u escapes, and the comment gives the
line of blind_label.html where it occurs) and sets lang="en". The S/V/N definitions are rendered as in Section 4 of the
paper. Nothing else changes: the frames, the sample and the code are byte-identical, which the checks at the end assert.
One behaviour follows the language: ticking "unsure" writes "unsure" into the note (then "; " before any note text),
where the original wrote the Chinese word for it (then a full-width semicolon). Reading a note back accepts the same
separators as the original, written as \uFF1B and \uFF0C escapes in the regular expression.

Run from level_annotation/human_check/:  python3 -I make_label_page_en.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile("[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")

PAIRS = [  # (Chinese, English, occurrences), applied in this order
    ('\u53ea\u770b\u6bcf\u5173\u7684\u7b2c\u4e00\u5e27\uff0c\u548c\u540c\u4e00\u5c40\u524d\u9762\u6240\u6709\u5173\u6bd4\uff0c\u4e0d\u7528\u73a9\u3002\u5171 7 \u5c40 44 \u5173\u3002',  # line 85
     'Look only at the first frame of each level and compare it with all earlier levels of the same game; there is no need to play. 7 games, 44 levels in all.', 1),
    ('\u6807\u6ce8\u4eba\uff08\u5199\u4e0a\u540d\u5b57\u518d\u5f00\u59cb\uff09',  # line 87
     'Annotator (write your name before you start)', 1),
    ('placeholder="\u4f60\u7684\u540d\u5b57"',  # line 88
     'placeholder="Your name"', 1),
    ('aria-label="\u5173\u5361\u8fdb\u5ea6"',  # line 95
     'aria-label="Level progress"', 1),
    ('\u540c\u4e00\u5c40\u524d\u9762\u7684\u5173\uff0c\u70b9\u4e00\u5f20\u653e\u5230\u5de6\u8fb9\u5bf9\u7167\uff1a',  # line 102
     'Earlier levels of the same game; click one to put it on the left for comparison:', 1),
    ('aria-label="\u9009\u4e00\u4e2a\u6807\u7b7e"',  # line 106
     'aria-label="Choose a label"', 1),
    ('\u6ca1\u6709\u524d\u9762\u6ca1\u51fa\u73b0\u8fc7\u7684\u5143\u7d20\u7c7b\u578b\uff0c\u53ea\u662f\u5e03\u5c40\u3001\u6570\u91cf\u3001\u5927\u5c0f\u6216\u53c2\u6570\uff08\u989c\u8272\u3001\u94a5\u5319\u5f62\u72b6\u7b49\uff09\u53d8\u4e86',  # line 107
     'No element type that earlier levels lacked; only the layout, counts, sizes or parameters change (colours, key shapes and the like)', 1),
    ('\u5df2\u77e5\u5143\u7d20\u4ee5\u65b0\u7684\u914d\u7f6e\u51fa\u73b0\uff0c\u53ef\u80fd\u6539\u53d8\u7528\u6cd5\uff0c\u4f8b\u5982\u955c\u50cf\u8f74\u4ece\u7ad6\u76f4\u53d8\u6210\u6c34\u5e73\u3001\u4e24\u6761\u94fe\u4ea4\u53c9\u3001\u8c03\u8272\u677f\u591a\u4e86\u989c\u8272',  # line 108
     'Known elements in a new configuration that may change how they are used, for example a mirror axis turning from vertical to horizontal, two chains crossing or a palette gaining colours', 1),
    ('\u51fa\u73b0\u4e86\u65b0\u7684\u5143\u7d20\u7c7b\u578b\u6216\u65b0\u7684\u5168\u5c40\u6761\u4ef6\uff0c\u4f8b\u5982\u65b0\u7269\u4f53\u3001\u65b0\u7684\u754c\u9762\u5143\u7d20\u3001\u8ff7\u96fe',  # line 109
     'A new element type or a new global condition, such as a new object, a new interface element or fog', 1),
    ('\u5907\u6ce8\uff0c\u53ef\u4ee5\u4e0d\u5199\u3002\u5148\u5199\u5907\u6ce8\u518d\u70b9\u6807\u7b7e\uff0c\u70b9\u5b8c\u4f1a\u8df3\u5230\u4e0b\u4e00\u5173\u3002',  # line 112
     'Note (optional). Write the note before clicking a label; clicking a label moves on to the next level.', 1),
    ('placeholder="\u534a\u53e5\u7406\u7531"',  # line 114
     'placeholder="Half a sentence of reason"', 1),
    ('<input type="checkbox" id="unsure">\u4e0d\u786e\u5b9a</label>',  # line 115
     '<input type="checkbox" id="unsure">unsure</label>', 1),
    ('\u2190 \u4e0a\u4e00\u5173',  # line 119
     '← Previous level', 1),
    ('\u4e0b\u4e00\u5173 \u2192',  # line 120
     'Next level →', 1),
    ('44 \u5173\u90fd\u6807\u5b8c\u4e86\u3002\u56de\u7b54\u4e0b\u9762\u4e00\u9898\uff0c\u70b9\u201c\u4e0b\u8f7d CSV\u201d\uff0c\u628a\u6587\u4ef6\u4ea4\u7ed9\u7ec4\u7ec7\u8fd9\u6b21\u6807\u6ce8\u7684\u4eba\u3002\u4e24\u4efd\u90fd\u4ea4\u9f50\u4e4b\u524d\uff0c\u4e0d\u8981\u6253\u5f00\u5bf9\u65b9\u7684\u6587\u4ef6\u3002',  # line 122
     "All 44 levels are labelled. Answer the question below, click “Download CSV” and give the file to the person organising this labelling. Until both files are in, do not open the other annotator's file.", 1),
    ('\u6807\u5b8c\u4e4b\u524d\uff0c\u4f60\u6709\u6ca1\u6709\u770b\u8fc7 AI \u7684\u6807\u7b7e\u3001\u6807\u7b7e\u7edf\u8ba1\u6216\u8bba\u6587\u7a3f\uff1f\u7167\u5b9e\u9009\uff0c\u8bba\u6587\u4f1a\u5982\u5b9e\u5199\u3002',  # line 123
     'Before you finished, had you seen the AI labels, label statistics or the paper draft? Answer truthfully; the paper will report your answer as it is.', 1),
    ('<option value="">\u8bf7\u9009\u62e9</option><option value="none">\u6ca1\u770b\u8fc7</option><option value="partial">\u770b\u8fc7\u4e00\u90e8\u5206</option>',  # line 124
     '<option value="">Please choose</option><option value="none">No, none of them</option><option value="partial">Some of them</option>', 1),
    ('placeholder="\u770b\u8fc7\u4ec0\u4e48\uff0c\u5927\u6982\u4ec0\u4e48\u65f6\u5019"',  # line 126
     'placeholder="What you saw, and roughly when"', 1),
    ('\u8fd9\u4e2a\u6587\u4ef6\u4e0d\u8054\u7f51\uff0c\u4e5f\u4e0d\u4e0a\u4f20\u3002\u4f60\u7684\u7b54\u6848\u53ea\u5b58\u5728\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc\uff0c\u6807\u5b8c\u4e0b\u8f7d CSV \u4ea4\u51fa\u6765\u3002',  # line 128
     'This file does not go online and uploads nothing. Your answers are kept only in this browser; when you finish, download the CSV and hand it in.', 1),
    ('\u952e\u76d8\u4e5f\u884c\uff1aS\u3001V\u3001N \u9009\u6807\u7b7e\uff0c\u5de6\u53f3\u65b9\u5411\u952e\u7ffb\u5173\u3002\u5199\u5b8c\u5907\u6ce8\u6309\u56de\u8f66\uff0c\u5c31\u80fd\u63a5\u7740\u7528\u952e\u76d8\u3002',  # line 129
     'The keyboard works too: S, V and N choose a label, and the left and right arrow keys move between levels. After writing a note, press Enter to go on with the keyboard.', 1),
    ('\u62ff\u4e0d\u51c6\u5c31\u9009\u6700\u63a5\u8fd1\u7684\u4e00\u4e2a\uff0c\u518d\u52fe\u201c\u4e0d\u786e\u5b9a\u201d\u3002',  # line 130
     'If you are not sure, choose the closest label and tick “unsure”.', 1),
    ('\u5173\u6389\u518d\u5f00\uff0c\u5199\u540c\u4e00\u4e2a\u540d\u5b57\u5c31\u80fd\u63a5\u7740\u6807\u3002\u6362\u6d4f\u89c8\u5668\u6216\u6362\u7535\u8111\u63a5\u4e0d\u4e0a\uff1b\u4e0d\u8981\u7528\u65e0\u75d5\u7a97\u53e3\uff0c\u4e5f\u4e0d\u8981\u5728\u804a\u5929\u8f6f\u4ef6\u7684\u9884\u89c8\u91cc\u6807\u3002',  # line 131
     "If you close the page and open it again, write the same name to carry on. Another browser or another computer cannot carry on; do not use a private window, and do not label inside a chat app's preview.", 1),
    ('\u4e24\u4eba\u5404\u6807\u5404\u7684\u3002\u4e24\u4efd\u90fd\u4ea4\u9f50\u4e4b\u524d\uff0c\u4e0d\u8981\u8ba8\u8bba\u5177\u4f53\u5173\u5361\uff0c\u4e5f\u4e0d\u8981\u5148\u5bf9\u6807\u51c6\u3002',  # line 132
     'The two of you label separately. Until both files are in, do not discuss particular levels, and do not agree on criteria beforehand.', 1),
    ('\u6807\u5b8c\u4e4b\u524d\u4e0d\u8981\u770b\u8bba\u6587\u7a3f\u3001Writeup\u3001\u5c01\u9762\u3001\u7ed3\u679c\u6587\u4ef6\u548c\u79c1\u6709\u4ed3\u5e93\u91cc\u7684\u5176\u4ed6\u5185\u5bb9\uff0c\u4e0d\u8981\u67e5\u8fd9\u4e9b\u6e38\u620f\u7684\u673a\u5236\u8d44\u6599\uff0c\u4e5f\u4e0d\u8981\u53bb\u73a9\u8fd9\u51e0\u5c40\u3002',  # line 133
     'Until you finish, do not look at the paper draft, the Writeup, the cover, result files or anything else in the private repository; do not look up how these games work, and do not play these games.', 1),
    ("'\u8fd9\u4e2a\u6d4f\u89c8\u5668\u4e0d\u8ba9\u5b58\u3002\u5173\u9875\u9762\u4e4b\u524d\u4e00\u5b9a\u8981\u70b9\u201c\u4e0b\u8f7d CSV\u201d\u3002'",  # line 158
     "'This browser does not allow saving. Be sure to click “Download CSV” before closing the page.'", 1),
    ("'\u6709 ' + failed.size + ' \u5173\u6ca1\u5b58\u4e0a\u3002\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc\u8fd8\u7559\u7740\uff0c\u53ef\u4ee5\u7528\u201c\u590d\u5236\u7ed3\u679c CSV\u201d\u53d1\u7ed9 Claude\u3002'",  # line 285
     "failed.size + ' level(s) not saved. They are still in this browser; you can send them to Claude with “Copy results CSV”.'", 1),
    ("'\u5b58\u50a8\u8fde\u4e0d\u4e0a\uff0c\u5148\u5b58\u5728\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc\u3002\u6807\u5b8c\u7528\u201c\u590d\u5236\u7ed3\u679c CSV\u201d\u53d1\u7ed9 Claude\u3002'",  # line 295
     "'Cannot reach storage; saved in this browser for now. When you finish, send it to Claude with “Copy results CSV”.'", 1),
    ('>\u4e0b\u8f7d CSV</button>',  # line 136
     '>Download CSV</button>', 1),
    ('>\u590d\u5236\u7ed3\u679c CSV</button>',  # line 137
     '>Copy results CSV</button>', 1),
    ('aria-label="\u7ed3\u679c CSV"',  # line 139
     'aria-label="Results CSV"', 1),
    ('\u5173\u5361\u76f2\u6807',  # line 6, 84
     'Blind level labelling', 2),
    ("g + ' \u7b2c ' + it.level + ' \u5173'",  # line 213
     "g + ' level ' + it.level", 1),
    ("(v ? '\uff0c\u5df2\u6807 ' + v.label : '\uff0c\u672a\u6807')",  # line 214
     "(v ? ', labelled ' + v.label : ', not labelled')", 1),
    ("' \u8981\u6807\u7684\u8fd9\u4e00\u5173'",  # line 227
     "' the level to label'", 1),
    ("it.game + ' \u7b2c ' + it.level + ' \u5173\u7684\u7b2c\u4e00\u5e27'",  # line 229
     "it.game + ' level ' + it.level + ', first frame'", 1),
    ("' \u7528\u6765\u5bf9\u7167'",  # line 234
     "' for comparison'", 1),
    ("it.game + ' \u7b2c ' + ref + ' \u5173\u7684\u7b2c\u4e00\u5e27'",  # line 236
     "it.game + ' level ' + ref + ', first frame'", 1),
    ("'\u5bf9\u7167\u7b2c ' + l + ' \u5173'",  # line 243
     "'Compare with level ' + l", 1),
    ("it.game + ' \u7b2c ' + l + ' \u5173'",  # line 246
     "it.game + ' level ' + l", 1),
    ("note.indexOf('\u4e0d\u786e\u5b9a')",  # line 256
     "note.indexOf('unsure')", 1),
    ("note.replace(/^\u4e0d\u786e\u5b9a[\uff1b;\uff0c, ]*/, '')",  # line 257
     "note.replace(/^unsure[\\uFF1B;\\uFF0C, ]*/, '')", 1),
    ("('\u4e0d\u786e\u5b9a' + (t ? '\uff1b' + t : ''))",  # line 276
     "('unsure' + (t ? '; ' + t : ''))", 1),
    ("setStatus('\u5df2\u4fdd\u5b58')",  # line 284
     "setStatus('Saved')", 1),
    ("'\u5148\u5728\u53f3\u4e0a\u89d2\u5199\u4e0a\u540d\u5b57\u3002'",  # line 288, 375
     "'First write your name at the top right.'", 2),
    ("'\u5df2\u5b58\u5728\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc'",  # line 294
     "'Saved in this browser'", 1),
    ("'\u5b58\u50a8\u6682\u65f6\u8fde\u4e0d\u4e0a\uff0c\u6807\u6ce8\u5148\u5b58\u5728\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc\u3002'",  # line 313
     "'Storage cannot be reached for now; labels are kept in this browser meanwhile.'", 1),
    ("'\u5b58\u50a8\u65ad\u5f00\u4e86\uff0c\u6807\u6ce8\u5148\u5b58\u5728\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc\u3002'",  # line 324
     "'Storage disconnected; labels are kept in this browser meanwhile.'", 1),
    ("'\u5148\u56de\u7b54\u6700\u540e\u4e00\u9898\u3002'",  # line 362, 377
     "'Answer the last question first.'", 2),
    ("'\u5df2\u590d\u5236\u3002'",  # line 368
     "'Copied.'", 1),
    ("'\u5df2\u590d\u5236\uff0c\u7c98\u8d34\u5230\u5bf9\u8bdd\u91cc\u5c31\u884c\u3002'",  # line 368
     "'Copied; just paste it into the chat.'", 1),
    ("'\u6d4f\u89c8\u5668\u6ca1\u8ba9\u590d\u5236\uff0c\u6587\u5b57\u5df2\u9009\u4e2d\uff0c\u624b\u52a8\u590d\u5236\u5373\u53ef\u3002'",  # line 369
     "'The browser did not allow copying; the text is selected, so copy it by hand.'", 1),
    ("'\u5df2\u4e0b\u8f7d '",  # line 388
     "'Downloaded '", 1),
    ("'\u8fd8\u5dee ' + (ITEMS.length - n) + ' \u5173\u3002\u8fd9\u4efd\u53ea\u662f\u5907\u4efd\uff0c\u4e0d\u662f\u6700\u7ec8\u6587\u4ef6\u3002'",  # line 388
     "(ITEMS.length - n) + ' levels still to go. This file is only a backup, not the final file.'", 1),
    ("'\u5b58\u50a8\u8fde\u4e0d\u4e0a\uff0c\u6807\u6ce8\u4f1a\u5b58\u5728\u8fd9\u4e2a\u6d4f\u89c8\u5668\u91cc\u3002'",  # line 402
     "'Cannot reach storage; labels will be kept in this browser.'", 2),
]


def main():
    src = open(os.path.join(HERE, "blind_label.html"), encoding="utf-8").read()
    assert src.count('<html lang="zh-CN">') == 1
    text = src.replace('<html lang="zh-CN">', '<html lang="en">')
    for old, new, n in PAIRS:
        assert text.count(old) == n, (old, text.count(old))
        text = text.replace(old, new)
    assert not CJK.search(text), CJK.findall(text)
    a, b = src.split("\n"), text.split("\n")
    assert len(a) == len(b)
    changed = [i + 1 for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert all(CJK.search(a[i - 1]) or a[i - 1].startswith("<html") for i in changed)  # only lines that held Chinese
    with open(os.path.join(HERE, "blind_label.en.html"), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"blind_label.en.html: {len(changed)} of {len(a)} lines changed")


if __name__ == "__main__":
    main()
