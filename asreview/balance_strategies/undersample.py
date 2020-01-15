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

from math import ceil

import numpy as np

from asreview.balance_strategies.base import BaseBalance


class UndersampleBalance(BaseBalance):
    """Balancing class that undersamples the data with a given ratio.
    """
    name = "undersampling"

    def __init__(self, ratio=1.0):
        """Initialize the undersampling balance strategy.

        Arguments
        ---------
        ratio: double
            Undersampling ratio of the zero's. If for example we set a ratio of
            0.25, we would sample only a quarter of the zeros and all the ones.
        """
        super(UndersampleBalance, self).__init__()
        self.ratio = ratio

    def sample(self, X, y, train_idx, shared):
        one_ind = train_idx[np.where(y[train_idx] == 1)]
        zero_ind = train_idx[np.where(y[train_idx] == 0)]

        n_one = len(one_ind)
        n_zero = len(zero_ind)

        # If we don't have an excess of 0's, give back all training_samples.
        if n_one/n_zero >= self.ratio:
            shuf_ind = np.append(one_ind, zero_ind)
        else:
            n_zero_epoch = ceil(n_one/self.ratio)
            zero_under = np.random.choice(np.arange(n_zero), n_zero_epoch,
                                          replace=False)
            shuf_ind = np.append(one_ind, zero_ind[zero_under])

        np.random.shuffle(shuf_ind)
        return X[shuf_ind], y[shuf_ind]

    def full_hyper_space(self):
        from hyperopt import hp
        parameter_space = {
            "bal_ratio": hp.lognormal('bal_ratio', 0, 1),
        }
        return parameter_space, {}
