#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import getopt
import fitz  # pymupdf
import cssutils  # cssutils
import markdown  # Python-Markdown

from pprint import pprint  # NOQA

"""
AutoPDFBookmark Project
Generate bookmark(outline) according to the CSS file given

the CSS file should contain selector like:

body{
  font-family:"Microsoft Yahei";
  font-size: 14pt;
  line-height: 1.4em;
 }

h1 {
  font-family:"Microsoft Yahei";
  font-size: 28pt;
}

h2 {
  font-family:"Microsoft Yahei";
  font-size: 20pt;
}
...

and the PDF file should be generated by this CSS file
here we use Markdown PDF on vscode running 'Export(pdf)'

!!! only support pt for font-size.
!!! the 'font-size' in body CANNOT equal to the h1,h2,h3... styles, else will encount error.
"""

__version__ = "0.5.1"
__author__ = "Castle"
__email__ = "castleodinland@gmail.com"
__license__ = "GPL"

css_list = []  # [selector, {xxx1:yyy1, xxx2:yyy2, ...}]context["size"]

re_font_size = r"(\d+)pt"  # -> 14pt
re_head_title = r"h(\d+)"  # -> h1, h2, h3, h4, h5, h6
re_chapter_code = r"(\d+\.\d+\.\d+)|(\d+\.\d+)|(\d+\.)"  # -> 1.2.3 or 1.2 or 1.

pdf_input_name = "mypdf.pdf"  # default input pdf name
css_input_name = "markdownhere.css"  # default input css name
pdf_output_name = None  # default output pdf name (input name + _new)
md_input_name = None  # default input md name (input name + .md)

# the acceptable margin between CSS font-size (`selector_font_size`) and
# actual font size (`context["size"]`)
fontsize_threshold = 0.2


def usage():
    print("AutoPDFBookmark version : %s" % (__version__))
    print("\nThis is the usage function")
    print("Usage:")
    print(
        "python AutoPDFBookmark.py -f <pdf_input_file> -c <css_input_file> [-o <pdf_output_file>]"
    )
    print("-f, --pdf : specify the input .pdf file name, mypdf.pdf as default")
    print("-c, --css : specify the input .css file name, markdownhere.css as default")
    print("-o, --output : specify the output .pdf file name, mypdf_new.pdf as default")
    print("-m, --md : specify the input .md file name, None as default")


def load_css_file(css_file):
    with open(css_file, "rb") as fd:
        css_string = fd.read()

    sheet = cssutils.parseString(css_string)
    css_list = {
        rule.selectorText: {property.name: property.value for property in rule.style}
        for rule in sheet
        if hasattr(rule, "selectorText")
    }
    return css_list


def get_header_level_from_selector(key, values):
    # get selector named h* and return header level
    # if not h*, return None
    pattern = re.compile(re_head_title)
    match_obj = pattern.match(key)
    if match_obj:
        bmk_level = int(match_obj.group(1))
    else:
        bmk_level = None

    return bmk_level


def get_font_size_from_selector(key, values):
    if "font-size" not in values:
        return None

    pattern = re.compile(re_font_size)
    match_obj = pattern.match(values["font-size"])
    return int(match_obj.group(1))


def mdfile_to_toc(md_input_name):
    with open(md_input_name, "r", encoding="utf-8") as md_file:
        md_text = md_file.read()

    md = markdown.Markdown(extensions=["toc"])
    _ = md.convert(md_text)  # ここでmd.toc_tokensが更新される
    # toc = md.toc
    # pprint.pprint(md.toc_tokens)

    # TOC Object to {name: level} dict.
    result_hash = {}

    def get_toc_tokens(toc_tokens):
        nonlocal result_hash
        for token in toc_tokens:
            if "level" in token and "name" in token:
                result_hash[token["name"]] = token["level"]

            if "children" in token:
                get_toc_tokens(token["children"])

    get_toc_tokens(md.toc_tokens)
    return result_hash


def gen_document_toc_item(lvl, title, page, position):
    return [lvl, title, page, {"kind": fitz.LINK_GOTO, "to": position, "collapse": 1}]


def convert_Kangxi_to_CJK(str):
    # https://imabari.hateblo.jp/entry/2020/08/03/220407
    tbl = str.maketrans(
        "⺃⺅⺉⺋⺎⺏⺐⺒⺓⺔⺖⺘⺙⺛⺟⺠⺡⺢⺣⺦⺨⺫⺬⺭⺱⺲⺹⺾⻁⻂⻃⻄⻍⻏⻑⻒⻖⻘⻟⻤⻨⻩⻫⻭⻯⻲⼀⼁⼂⼃⼄⼅⼆⼇⼈⼉⼊⼋⼌⼍⼎⼏⼐⼑⼒⼓⼔⼕⼖⼗⼘⼙⼚⼛⼜⼝⼞⼟⼠⼡⼢⼣⼤⼥⼦⼧⼨⼩⼪⼫⼬⼭⼮⼯⼰⼱⼲⼳⼴⼵⼶⼷⼸⼹⼺⼻⼼⼽⼾⼿⽀⽁⽂⽃⽄⽅⽆⽇⽈⽉⽊⽋⽌⽍⽎⽏⽐⽑⽒⽓⽔⽕⽖⽗⽘⽙⽚⽛⽜⽝⽞⽟⽠⽡⽢⽣⽤⽥⽦⽧⽨⽩⽪⽫⽬⽭⽮⽯⽰⽱⽲⽳⽴⽵⽶⽷⽸⽹⽺⽻⽼⽽⽾⽿⾀⾁⾂⾃⾄⾅⾆⾇⾈⾉⾊⾋⾌⾍⾎⾏⾐⾑⾒⾓⾔⾕⾖⾗⾘⾙⾚⾛⾜⾝⾞⾟⾠⾡⾢⾣⾤⾥⾦⾧⾨⾩⾪⾫⾬⾭⾮⾯⾰⾱⾲⾳⾴⾵⾶⾷⾸⾹⾺⾻⾼⾽⾾⾿⿀⿁⿂⿃⿄⿅⿆⿇⿈⿉⿊⿋⿌⿍⿎⿏⿐⿑⿒⿓⿔⿕戶黑",
        "乚亻刂㔾兀尣尢巳幺彑忄扌攵旡母民氵氺灬丬犭罒示礻罓罒耂艹虎衤覀西辶阝長镸阝青飠鬼麦黄斉歯竜亀一丨丶丿乙亅二亠人儿入八冂冖冫几凵刀力勹匕匚匸十卜卩厂厶又口囗土士夂夊夕大女子宀寸小尢尸屮山巛工己巾干幺广廴廾弋弓彐彡彳心戈戸手支攴文斗斤方无日曰月木欠止歹殳毋比毛氏气水火爪父爻爿片牙牛犬玄玉瓜瓦甘生用田疋疒癶白皮皿目矛矢石示禸禾穴立竹米糸缶网羊羽老而耒耳聿肉臣自至臼舌舛舟艮色艸虍虫血行衣襾見角言谷豆豕豸貝赤走足身車辛辰辵邑酉釆里金長門阜隶隹雨靑非面革韋韭音頁風飛食首香馬骨高髟鬥鬯鬲鬼魚鳥鹵鹿麥麻黃黍黒黹黽鼎鼓鼠鼻齊齒龍龜龠戸黒",
    )

    return str.translate(tbl)


if __name__ == "__main__":
    print(fitz.__doc__)

    try:
        options, args = getopt.getopt(
            sys.argv[1:], "hf:c:o:m:", ["help", "pdf=", "css=", "output=", "md="]
        )
    except getopt.GetoptError:
        usage()
        sys.exit(0)

    for name, value in options:
        if name in ("-h", "--help"):
            usage()
            sys.exit(0)
        if name in ("-f", "--pdf"):
            pdf_input_name = value
            if pdf_output_name is None:
                pdf_input_basename = os.path.splitext(pdf_input_name)[0]
                pdf_output_name = pdf_input_basename + "_new" + ".pdf"

            if md_input_name is None:
                md_input_name = pdf_input_basename + ".md"
        if name in ("-c", "--css"):
            css_input_name = value
        if name in ("-o", "--output"):
            pdf_output_name = value
            print("output file name: %s" % (pdf_output_name))
        if name in ("-m", "--md"):
            md_input_name = value

    css_list = load_css_file(css_input_name)
    # pprint(css_list)
    if md_input_name is not None:
        heading_dict = mdfile_to_toc(md_input_name)
        # pprint(heading_dict)
    else:
        heading_dict = None

    doc = fitz.open(pdf_input_name)
    toc = doc.get_toc(simple=False)
    if toc:
        assert "the file has toc."

    # the bmk_level should start from 1, if not, assert error
    has_main_title = False

    # for pages in doc:
    for page_num, page in enumerate(doc, 1):
        text_blocks = page.get_text("blocks", flags=11)

        for text_block in text_blocks:
            text = text_block[4]
            text = convert_Kangxi_to_CJK(text)
            text = text.strip()
            text = text.replace("\n", " ")
            point = fitz.Point(0, float(text_block[1]))
            if text in heading_dict:
                bmk_level = heading_dict[text]
                print(f"match: {text} [level:{bmk_level}]")
                # add bookmark
                toc.append(
                    gen_document_toc_item(
                        bmk_level,
                        text,
                        page_num,
                        point,
                    )
                )
                continue

        continue

        blocks = page.get_text("dict", flags=11)["blocks"]

        for one_block in blocks:
            context = one_block["lines"][0]["spans"][0]
            block_text = context["text"]
            block_text = convert_Kangxi_to_CJK(block_text)
            line_local = context["bbox"][1]
            point = fitz.Point(0, float(line_local))
            # print(context["text"])
            # print("-------------------")

            # if not context["flags"] == 0:
            # continue

            if heading_dict is not None:
                if block_text in heading_dict:
                    bmk_level = heading_dict[block_text]
                    print(f"match: {block_text} [level:{bmk_level}]")
                    if not has_main_title and bmk_level != 1:
                        assert "document starts from level %d" % (bmk_level)
                    elif not has_main_title:
                        has_main_title = True

                    # add bookmark
                    toc.append(
                        gen_document_toc_item(
                            bmk_level,
                            block_text,
                            page_num,
                            point,
                        )
                    )
                    continue

            for key, values in css_list.items():
                bmk_level = get_header_level_from_selector(key, values)
                if not bmk_level:
                    continue

                # get font-size & font-family
                selector_font_size = get_font_size_from_selector(key, values)
                if not selector_font_size:
                    continue

                if abs(selector_font_size - context["size"]) <= fontsize_threshold:
                    # chapter text filter
                    # pt1 = re.compile(re_chapter_code)
                    # mo = pt1.match(context["text"])
                    # if mo is None:
                    # continue
                    print(f"match: {block_text} [level:{bmk_level}]")
                    if not has_main_title and bmk_level != 1:
                        assert "document starts from level %d" % (bmk_level)
                    elif not has_main_title:
                        has_main_title = True

                    # add bookmark
                    toc.append(
                        gen_document_toc_item(
                            bmk_level,
                            block_text,
                            page_num,
                            point,
                        )
                    )

    # pprint(toc)
    doc.set_toc(toc)
    doc.save(pdf_output_name)
    doc.close()
