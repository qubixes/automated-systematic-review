# Copyright 2019 The ASReview Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import warnings
import pkg_resources
import hashlib

import numpy as np
import pandas as pd

from asreview.exceptions import BadFileFormatError
from asreview.io.ris_reader import write_ris
from asreview.io.paper_record import PaperRecord
from asreview.config import LABEL_NA

with warnings.catch_warnings():
    warnings.filterwarnings("ignore")
    from fuzzywuzzy import fuzz


def format_to_str(obj):
    if obj is None:
        return ""
    res = ""
    if isinstance(obj, list):
        " ".join(obj)
    else:
        res = obj
    return res


def get_fuzzy_ranking(keywords, str_list):
    rank_list = np.zeros(len(str_list), dtype=np.float)
    for i, my_str in enumerate(str_list):
        rank_list[i] = fuzz.token_set_ratio(keywords, my_str)
    return rank_list


def is_iterable(i):
    try:
        iter(i)
        if isinstance(i, str):
            return False
        return True
    except TypeError:
        return False


class ASReviewData():
    """Data object to store csv/ris file.

    Extracts relevant properties of papers."""

    def __init__(self, df=None, data_name="empty", data_type="standard"):
        self.df = df
        self.data_name = data_name
        self.prior_idx = []
        if df is None:
            return

        if data_type == "included":
            self.labels = np.ones(len(self))
        if data_type == "excluded":
            self.labels = np.zeros(len(self))
        if data_type == "prior":
            self.prior_idx = df.index.values

        self.max_idx = max(df.index.values)

    def hash(self):
        if len(self.df.index) < 1000:
            texts = " ".join(self.bodies)
        else:
            texts = " ".join(self.texts)
        return hashlib.sha1(" ".join(texts).encode(
            encoding='UTF-8', errors='ignore')).hexdigest()

    def slice(self, idx):
        if self.df is None:
            raise ValueError("Cannot slice empty ASReviewData object.")

        return ASReviewData(self.df[idx], data_name="sliced")

    def append(self, as_data):
        """Append another ASReviewData object.

        It puts the training data at the end.

        Arguments
        ---------
        as_data: ASReviewData
            Dataset to append.
        """
        if as_data.df is None:
            return
        if len(self) == 0:
            self.df = as_data.df
            self.data_name = as_data.data_name
            self.prior_idx = as_data.prior_idx
            self.max_idx = as_data.max_idx
            return

        reindex_val = max(self.max_idx - min(as_data.df.index.values), 0)
        new_index = np.append(self.df.index.values,
                              as_data.df.index.values + reindex_val)
        new_priors = np.append(self.prior_idx, as_data.prior_idx + reindex_val)
        new_df = self.df.append(as_data.df)
        new_df.index = new_index

        self.max_idx = max(self.max_idx, as_data.max_idx, max(new_index))
        self.df = new_df
        self.prior_idx = new_priors
        self.data_name += "_" + as_data.data_name

    @classmethod
    def from_file(cls, fp, data_name=None, read_fn=None, data_type=None):
        "Create instance from csv/ris/excel file."
        if data_name is None:
            data_name = Path(fp).stem

        if read_fn is not None:
            return cls(read_fn(fp), data_name=data_name,
                       data_type=data_type)

        entry_points = {
            entry.name: entry
            for entry in pkg_resources.iter_entry_points('asreview.readers')
        }
        best_suffix = None
        for suffix, entry in entry_points.items():
            if str(Path(fp).resolve()).endswith(suffix):
                if best_suffix is None or len(suffix) > len(best_suffix):
                    best_suffix = suffix

        if best_suffix is None:
            raise ValueError(f"Error reading file {fp}, no capabilities for "
                             "reading such a file.")

        read_fn = entry_points[best_suffix].load()
        return cls(read_fn(fp), data_name=data_name,
                   data_type=data_type)

    def record(self, i, by_index=True):
        if not is_iterable(i):
            index_list = [i]
        else:
            index_list = i

        if not by_index:
            records = [PaperRecord(**self.df.loc[j, :], record_id=j)
                       for j in index_list]
        else:
            records = [PaperRecord(**self.df.iloc[j],
                                   record_id=self.df.index.values[j])
                       for j in index_list]

        if is_iterable(i):
            return records
        return records[0]

    def preview_record(self, i, by_index=True, *args, **kwargs):
        "Return a preview string for record i."
        return self.record(i, by_index=by_index).preview(*args, **kwargs)

    def format_record(self, i, by_index=True, *args, **kwargs):
        " Format one record for displaying in the CLI. "
        return self.record(i, by_index=by_index).format(*args, **kwargs)

    def print_record(self, *args, **kwargs):
        "Print a record to the CLI."
        print(self.format_record(*args, **kwargs))

    def fuzzy_find(self, keywords, threshold=50, max_return=10, exclude=None,
                   by_index=True):
        """Find a record using keywords.

        It looks for keywords in the title/authors/keywords
        (for as much is available). Using the fuzzywuzzy package it creates
        a ranking based on token set matching.

        Arguments
        ---------
        keywords: str
            A string of keywords together, can be a combination.
        threshold: float
            Don't return records below this threshold.
        max_return: int
            Maximum number of records to return.

        Returns
        -------
        list:
            Sorted list of indexes that match best the keywords.
        """
        match_str = np.full(len(self), "x", dtype=object)

        all_titles = self.title
        all_authors = self.df["authors"].values
        all_keywords = self.df["keywords"].values
        for i in range(len(self)):
            authors = format_to_str(all_authors[i])
            title = all_titles[i]
            rec_keywords = format_to_str(all_keywords[i])
            match_str[i, ] = " ".join([title, authors, rec_keywords])

        new_ranking = get_fuzzy_ranking(keywords, match_str)
        sorted_idx = np.argsort(-new_ranking)
        best_idx = []
        for idx in sorted_idx:
            if idx in exclude:
                continue
            if len(best_idx) >= max_return:
                break
            if len(best_idx) > 0 and new_ranking[idx] < threshold:
                break
            best_idx.append(idx)
        fuzz_idx = np.array(best_idx, dtype=np.int)
        if not by_index:
            fuzz_idx = self.df.index.values[fuzz_idx]
        return fuzz_idx.tolist()

    @property
    def record_ids(self):
        return self.df.index.values

    @property
    def texts(self):
        cur_texts = np.array([self.headings[i] + " " + self.bodies[i]
                              for i in range(len(self.headings))
                              ], dtype=object)
        return cur_texts

    @property
    def headings(self):
        return self.title

    @property
    def title(self):
        return self.df["title"].values

    @property
    def bodies(self):
        return self.abstract

    @property
    def abstract(self):
        return self.df["abstract"].values

    def get(self, name):
        return self.df[name].values

    @property
    def prior_data_idx(self):
        "Get prior_included, prior_excluded from dataset."
        convert_array = np.full(self.max_idx, 999999999)
        convert_array[self.df.index.values] = np.arange(len(self.df.index))
        return convert_array[self.prior_idx]

    @property
    def labels(self):
        if "label" in list(self.df):
            return self.df["label"].values
        return None

    def prior_labels(self, logger, by_index=True):
        _, _, query_src, _ = logger.review_state()
        if "initial" not in query_src:
            return np.array([], dtype=int)
        if by_index:
            return np.array(query_src["initial"], dtype=int)
        return self.df.index.values[query_src["initial"]]

    @labels.setter
    def labels(self, labels):
        self.df["label"] = labels

    def __len__(self):
        if self.df is None:
            return 0
        return len(self.df.index)

    @property
    def final_labels(self):
        return None

    def to_file(self, fp, labels=None, df_order=None):
        """
        Export data object to file.
        Both RIS and CSV are supported file formats at the moment.

        Arguments
        ---------
        fp: str
            Filepath to export to.
        labels: list, np.array
            Labels to be inserted into the dataframe before export.
        df_order: list, np.array
            Optionally, dataframe rows can be reordered.
        """
        if Path(fp).suffix in [".csv", ".CSV"]:
            self.to_csv(fp, labels=labels, df_order=df_order)
        elif Path(fp).suffix in [".ris", ".RIS"]:
            self.to_ris(fp, labels=labels, df_order=df_order)
        else:
            raise BadFileFormatError(
                f"Unknown file extension: {Path(fp).suffix}.\n"
                f"from file {fp}")

    def to_dataframe(self, labels=None, df_order=None):
        new_df = pd.DataFrame.copy(self.df)
        if labels is not None:
            new_df["label"] = labels
        if df_order is not None:
            return new_df.iloc[df_order]

        if "label" in list(new_df):
            new_df.loc[new_df["label"] == LABEL_NA, "label"] = np.nan
        return new_df

    def to_csv(self, fp, labels=None, df_order=None):
        self.to_dataframe(labels=labels, df_order=df_order).to_csv(
            fp, index=True)

    def to_ris(self, ris_fp, labels=None, df_order=None):
        df = self.to_dataframe(labels=labels, df_order=df_order)
        write_ris(df, ris_fp)
