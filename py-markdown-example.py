import markdown
import pprint


def mdfile_to_toc(md_input_name):
    with open(md_input_name, "r", encoding="utf-8") as md_file:
        md_text = md_file.read()

    md = markdown.Markdown(extensions=["toc"])
    _ = md.convert(md_text)  # ここでmd.toc_tokensが更新される
    # toc = md.toc
    # pprint.pprint(md.toc_tokens)

    # TOC Object to {name: level} dict.
    result_hash = {}

    def _get_toc_tokens(toc_tokens):
        nonlocal result_hash
        for token in toc_tokens:
            if "level" in token and "name" in token:
                result_hash[token["name"]] = token["level"]

            if "children" in token:
                _get_toc_tokens(token["children"])

    _get_toc_tokens(md.toc_tokens)
    return result_hash


if __name__ == "__main__":
    md_input_name = r"README.md"

    toc_tokens = mdfile_to_toc(md_input_name)

    pprint.pprint(toc_tokens)
