import sys
import os.path
import numpy as np
from copy import deepcopy

import env
from utils import import_trace
from utils.read_write import save_model


class BaseEstimator(object):
    """Base class for all estimators."""

    def __init__(self, _y_required=True):
        self._y_required = _y_required
        self._X = None
        self._y = None
        self._n_samples = None
        self._n_features = None
        self._n_outputs = None
        self._called_fit = False

    def _check_X_y(self, X, y=None):
        """
        Ensure inputs are in the expected format:

        Convert `X` [and `y`] to `np.ndarray` if needed
        and ensure `X` [and `y`] are not empty.

        Parameters
        ----------
        X : (n_samples, n_features) array-like
            Data (feature vectors).
        y : (n_samples,) or (n_samples, n_outputs) array-like
            Labels vector. By default is required, but may be omitted
            if `_y_required` is False.
        """
        # validate `X`
        if not isinstance(X, np.ndarray):
            X = np.array(X)

        if X.size == 0:
            raise ValueError('number of features must be > 0')

        if X.ndim == 1:
            self._n_samples, self._n_features = 1, X.shape
        else:
            self._n_samples, self._n_features = X.shape[0], np.prod(X.shape[1:])

        # validate `y` if needed
        if self._y_required:
            if y is None:
                raise ValueError('missed required argument `y`')

            if not isinstance(y, np.ndarray):
                y = np.array(y)

            if y.size == 0:
                raise ValueError('number of outputs must be > 0')

            # TODO: decide whether to check len(y) == self._n_samples (semi-supervised learning)?
            if y.ndim == 1:
                self._n_outputs = 1
            else:
                self._n_outputs = np.prod(y.shape[1:])

        self._X = X
        self._y = y

    def _fit(self, X, y=None, **fit_params):
        """Class-specific `fit` routine."""
        raise NotImplementedError()

    def fit(self, X, y=None, **fit_params):
        """Fit the model according to the given training data (infrastructure)."""
        self._check_X_y(X, y)
        self._fit(X, y, **fit_params)
        self._called_fit = True

    def _predict(self, X=None, **predict_params):
        """Class-specific `predict` routine."""
        raise NotImplementedError()

    def predict(self, X=None, **predict_params):
        """Predict the target for the provided data (infrastructure)."""
        if not isinstance(X, np.ndarray):
            X = np.array(X)

        if self._called_fit:
            return self._predict(X, **predict_params)
        else:
            raise ValueError('`fit` must be called before calling `predict`')

    def get_params(self, deep=True, **params_mask):
        """Get parameters (attributes) of the model.

        # add model name (including import trace)

        Parameters
        ----------
        deep : bool, optional
            Whether to deepcopy all the attributes.
        params_mask : kwargs, optional
            Enables to control which attributes to include/exclude.
            If some attributes set to True, return only them.
            If some attributes set to False, return all excluding them.
            If there are mixed attributes, ValueError is raised.

        Returns
        -------
        params : dict
            Parameters of the model. Includes all attributes (members,
            not methods), that not start with underscore ("_") and also model
            name being class name stored in 'model' parameter.
        """
        if all(x in map(bool, params_mask.values()) for x in (False, True)):
            raise ValueError('`params_mask` cannot contain True and False values simultaneously')

        # collect all attributes
        params = vars(self)

        # omit "interesting" members
        params = {key: params[key] for key in params if not key.startswith('_')}

        # filter according to the mask provided
        if params_mask:
            if params_mask.values()[0]:
                params = {key: params[key] for key in params if key in params_mask}
            else:
                params = {key: params[key] for key in params if not key in params_mask}

        # path where the actual classifier is stored
        module_name = sys.modules[self.__class__.__module__].__name__
        module_path = os.path.abspath(module_name.replace('.', '/'))
        trace = import_trace(
            module_path=module_path,
            main_package_name='ml1_mnist',
            include_main_package=False
        )
        class_name = self.__class__.__name__
        params['model'] = '.'.join([trace, class_name])
        if deep:
            params = deepcopy(params)
        return params

    def set_params(self, **params):
        """Set parameters of the model.

        Parameters
        ----------
        params : kwargs
            New parameters and their values.

        Returns
        -------
        self
        """
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def _load(self):
        """Load (additional) class-specific parameters."""
        raise NotImplementedError()

    def _save(self):
        """Save (additional) class-specific parameters."""
        raise NotImplementedError()

    def save(self, filename=None, **json_params):
        save_model(self, filename, **json_params)