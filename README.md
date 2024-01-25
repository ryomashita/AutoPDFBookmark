# AutoPDFBookmark
## Background
[Markdown PDF](https://github.com/yzane/vscode-markdown-pdf) is great but it doesn't provide bookmarks
so here's a python script to Generate bookmark(outline) according to the CSS file given

This forked version implements the heading matching by the original markdown file's content.
The discussion on the difficulty of adding bookmarks to PDFs converted from HTML is followed [here](https://stackoverflow.com/questions/30049649/how-to-convert-html-to-pdf-with-bookmark).

TODO: Provide the user with the option to filter using either Markdown and/or CSS.

## how to use (forked version)

1. run `Markdown PDF: Export (pdf)` or `Markdown PDF: Export (settings.json)` in vscode, to generate the pdf file.
2. run this script.
```bash
poetry run python .\AutoPDFBookmark.py -f <input-pdf> [-c <input-css>] -m <input-md> [-o <output-pdf>]
```

## how to use
* specify the CSS for `Markdown PDF` like this:
```
"markdown-pdf.styles": [
    "markdownhere.css"
],
```
`markdownhere.css` is something like

```css
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

h3 {
  font-family:"Microsoft Yahei";
  font-size: 16pt;
}
```

* run `Markdown PDF: Export(pdf)` in vscode, to generate the pdf file `example.pdf`
* run `AutoPDFBookmark.py -f example.pdf -c markdownhere.css` to generate a new pdf file with Bookmarks named 'example_new.pdf'

## Special thanks
* [vscode-markdown-pdf](https://github.com/yzane/vscode-markdown-pdf)
* [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
* [cssutils](https://pypi.org/project/cssutils/)

