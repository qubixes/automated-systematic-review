from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

from asreview.feature_extraction.base import BaseFeatureExtraction


class Tfidf(BaseFeatureExtraction):
    """Class to apply SKLearn Tf-idf to texts."""
    name = "tf-idf"

    def __init__(self, ngram_max=1):
        """Initialize tfidf class.

        Arguments
        ---------
        ngram_max: int
            Can use up to ngrams up to ngram_max. For example in the case of
            ngram_max=2, monograms and bigrams could be used.
        """
        self.ngram_max = ngram_max

    def transform(self, texts):
        text_clf = Pipeline([
            ('vect', CountVectorizer(ngram_range=(1, self.ngram_max))),
            ('tfidf', TfidfTransformer())]
        )

        X = text_clf.fit_transform(texts)
        return X

    def full_hyper_space(self):
        from hyperopt import hp

        hyper_space = {
            "usp_ngram_max": 1 + hp.randint("usp_ngram_max", 2)
        }
        return hyper_space, {}
