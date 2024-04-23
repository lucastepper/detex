import re
import sys
from pathlib import Path


def get_single_caption(text):
    idx_start = 0
    # find where caption starts
    caption_found = False
    while idx_start < len(text):
        if text[idx_start : idx_start + 9] == r"\caption{":
            idx_start += 9
            caption_found = True
            break
        idx_start += 1
    if not caption_found:
        raise ValueError("Could not find caption in text \n\n" + text)
    # find where caption ends by looking for the closing }
    num_open_curly = 1
    idx_end = idx_start
    while idx_end < len(text):
        char = text[idx_end]
        context = text[idx_end - 10 : idx_end + 10]
        context1 = text[idx_end : idx_end + 10]
        if text[idx_end] == "{":
            num_open_curly += 1
        elif text[idx_end] == "}":
            num_open_curly -= 1
        if num_open_curly == 0:
            break
        idx_end += 1
    return text[idx_start:idx_end]


def block_text(text_to_block, line_len: int = 100):
    """Convert text into blocked text with max line_len. This function does not really work, yet."""
    lines = [line for line in text_to_block.split("\n") if line]
    # split words and remove empty strings
    lines = [[w for w in line.split(" ") if w] for line in lines]
    # remember which lines are short, as we want to preserve the line breaks there
    len_lines = [len(" ".join(line)) for line in lines]

    # text_to_block = text_to_block.replace("\n", " ").replace("\t", " ")
    # words = [w for w in text_to_block.split(" ") if w]
    text_blocked = ""
    word_count = 0
    while len(lines) > 0:
        # check if line ends, if not, get next word
        if len(lines[0]) == 0:
            # short line ends, preserve line break
            if len_lines[0] < line_len - 10:
                text_blocked += "\n"
                word_count = 0
            lines = lines[1:]
            len_lines = len_lines[1:]
            continue
        words = lines.pop(0)
        while len(words) > 0:
            # check if word fits in line
            # check if we have word before, if not, always add word
            if word_count == 0:
                text_blocked += words[0]
                word_count += len(words[0])
                words = words[1:]
            # if we have word before, check if we have space, if so, add space and word
            elif word_count + len(words[0]) < line_len:
                text_blocked += " " + words[0]
                # add 1 for space
                word_count += len(words[0]) + 1
                words = words[1:]
            # if no space, add line break
            else:
                text_blocked += "\n"
                word_count = 0
    # if not text_blocked.endswith("\n"):
    #     text_blocked += "\n"
    return text_blocked


def get_text_enclosed(
    text: str, prefix: str, suffix: str, remove: bool = True, block: bool = False
):
    """Find the text between prefix and suffix and return it. If remove, replace
    prefix MATCH suffix with empty string. Throws an error if more than one hit found
    If block, blocks the hit.
    """
    hit = re.findall(prefix + r"(.*)" + suffix, text, flags=re.DOTALL)
    if not hit:
        return None
    if len(hit) > 1:
        raise ValueError(f"Found more than one hit for {prefix=} {suffix=}")
    if remove:
        text = re.sub(prefix + r".*" + suffix, "", text, flags=re.DOTALL)
    if block:
        hit = [block_text(hit[0])]
    return hit[0], text


def delete_tex_command(text: str, command: str):
    """Delete all occurences of a given latex command in text"""
    if not r"\\" in command:
        command = r"\\" + command
    return re.sub(command + r"(?:(?:\[.*\])?\n?\{[^}]+\})?", "", text)


def replace_tex_command_with_body(text: str, command: str):
    """Find all occurences of a given latex command in text and replace it with the body; {$BODY}"""
    if not r"\\" in command:
        command = r"\\" + command
    return re.sub(command + r"{([^}]*)}", r"\1", text)


def delte_comments(text: str):
    """Delete all comments, by removing everything after % in a line"""
    text = re.sub(r"%.*\n", "", text)
    return text


def delete_equations(text: str):
    """Delete all equations in equation, array or align environment"""
    equation_qualifiers = ["equation", "align", "array", "subequations"]
    for eqn_quali in equation_qualifiers:
        text = re.sub(
            r"\\begin{" + eqn_quali + r"\*?}(.*?)\\end{" + eqn_quali + r"\*?}\n?",
            "",
            text,
            flags=re.DOTALL,
        )
    return text


def get_title(text) -> str:
    """Search for title in document"""
    hit = re.search(r"\\title(?:\[.*\])?\n?\{([^{]+)\}", text)
    if len(hit.groups()) >= 1:
        return hit.group(1)
    return ""


def get_document_body(text) -> str:
    r"""Search for the body inside \begin{document} \end{document}"""
    hit = re.search(r"\\begin{document}(.*)\\end{document}", text, flags=re.DOTALL)
    if len(hit.groups()) >= 1:
        return hit.group(1)
    raise ValueError(r"Counld not find body of \begin{document} BODY \end{document}")


def remove_extra_newlines(doc_body: str):
    """Remove extra newlines, i.e. more than 1 newlines in a row"""
    return re.sub(r"\n\n+", r"\n\n", doc_body)


def get_abstract(text: str):
    """Remove abstract enclosing if found"""
    abstract, text = get_text_enclosed(text, r"\\begin{abstract}", r"\\end{abstract}", block=True)
    return abstract, text


def get_all_captions(text: str) -> list[str]:
    """For all tables and figures, get the caption text and remove the table/figure env."""
    fig_tab_bodies = re.findall(
        r"\\begin{(?:figure|table)\*?}(.*?)\\end{(?:figure|table)\*?}", text, flags=re.DOTALL
    )
    text = re.sub(
        r"\\begin{(?:figure|table)\*?}(?:.*?)\\end{(?:figure|table)\*?}", "", text, flags=re.DOTALL
    )
    captions = [get_single_caption(body) for body in fig_tab_bodies]
    return text, captions


def replace_subtitles(text: str):
    """Replace the title, section or subsection titles with regular titles. Allowed are
    any number of subs before section and a \label{LABEL} in the section body.
    The LABEL is removed.
    """
    # I don't join this function with get_title as this function operator on the body, only
    # and the title is outside the body
    to_find = r"\\(?:sub)*section{(?:\\label{[^}]*})([^}]*)}"
    text = re.sub(to_find, r"\1\n\n", text, flags=re.DOTALL)
    return text


def replace_refs(text):
    """Replace all references by the number 1"""
    return re.sub(r"\\ref{[^}]*}", "1", text)


def replace_bib_with_caption(text: str, captions: list[str]):
    """We use the line including the bibliography to replace it with the captions
    of all figures and tables.
    """
    # pylint: disable=anomalous-backslash-in-string
    captions_text = "\section{Captions}\n"
    for i, caption in enumerate(captions):
        # pylint: disable=anomalous-backslash-in-string
        captions_text += "\subsection{Caption " f"{i}" "}" f" \n{caption}\n "
    # print(captions_text)
    text = re.sub(r"\\bibliography{[^}]*}", "PUTTHECAPTIONTEXTHEREREADFASDF", text)
    text = text.replace("PUTTHECAPTIONTEXTHEREREADFASDF", captions_text)
    return text


def main():
    text_out = ""
    mode = sys.argv[1]
    if mode == "detex":
        file = Path(sys.argv[2])
        print(f"Detexing {file}")
        with open(file, "r", encoding="UTF-8") as fh:
            text = fh.read()
        # run through the text editing functionse
        text = replace_refs(text)
        text, captions = get_all_captions(text)
        text = delete_equations(text)
        text = delete_tex_command(text, r"~\\cite")
        text = replace_bib_with_caption(text, captions)
        # store output in /tmp
        with open("/tmp/temp.tex", "w", encoding="UTF-8") as fh:
            fh.write(text)


if __name__ == "__main__":
    main()
