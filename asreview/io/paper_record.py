from asreview.config import LABEL_NA


class PaperRecord():
    def __init__(self, title, abstract, record_id, authors=None, keywords=None,
                 label=LABEL_NA, **kwargs):
        self.title = title
        self.abstract = abstract
        self.authors = authors
        self.keywords = keywords
        self.record_id = record_id
        self.label = label
        if label is None:
            self.label = LABEL_NA
        self.extra_fields = kwargs

    def preview(self, w_title=80, w_authors=40):
        "Return a preview string for record i."
        title_str = ""
        author_str = ""
        if self.title is not None:
            if len(self.title) > w_title:
                title_str = self.title[:w_title - 2] + ".."
            else:
                title_str = self.title
        if self.authors is not None:
            cur_authors = format_to_str(self.authors)
            if len(cur_authors) > w_authors:
                author_str = cur_authors[:w_authors - 2] + ".."
            else:
                author_str = cur_authors
        format_str = "{0: <" + str(w_title) + "}   " + "{1: <" + str(w_authors)
        format_str += "}"
        prev_str = format_str.format(title_str, author_str)
        return prev_str

    def format(self, use_cli_colors=True):
        " Format one record for displaying in the CLI. "
        if self.title is not None:
            title = self.title
            if use_cli_colors:
                title = "\033[95m" + title + "\033[0m"
            title += "\n"
        else:
            title = ""

        if self.authors is not None and len(self.authors) > 0:
            authors = format_to_str(self.authors) + "\n"
        else:
            authors = ""

        if self.abstract is not None and len(self.abstract) > 0:
            abstract = self.abstract
            abstract = "\n" + abstract + "\n"
        else:
            abstract = ""

        return ("\n\n----------------------------------"
                f"\n{title}{authors}{abstract}"
                "----------------------------------\n\n")

    def print(self, *args, **kwargs):
        "Print a record to the CLI."
        print(self.format_record(*args, **kwargs))

    @property
    def text(self):
        title = self.title
        abstract = self.abstract
        if title is None:
            title = ""
        if abstract is None:
            abstract = ""
        return title + " " + abstract

    @property
    def heading(self):
        if self.title is None:
            return ""
        return self.title

    @property
    def body(self):
        if self.abstract is None:
            return ""
        return self.abstract

    def todict(self):
        label = self.label
        if self.label is LABEL_NA:
            label = None
        paper_dict = {
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "keywords": self.keywords,
            "record_id": self.record_id,
            "label": label,
        }
        paper_dict.update(self.extra_fields)
        return paper_dict


def format_to_str(obj):
    res = ""
    if isinstance(obj, list):
        for sub in obj:
            res += str(sub) + " "
    else:
        res = obj
    return res
