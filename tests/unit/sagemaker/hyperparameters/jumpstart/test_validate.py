# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import


from mock.mock import patch
import pytest

from sagemaker import hyperparameters
from sagemaker.jumpstart.enums import HyperparameterValidationMode
from sagemaker.jumpstart.exceptions import JumpStartHyperparametersError
from sagemaker.jumpstart.types import JumpStartHyperparameter

from tests.unit.sagemaker.jumpstart.utils import get_spec_from_base_spec


@patch("sagemaker.jumpstart.accessors.JumpStartModelsAccessor.get_model_specs")
def test_jumpstart_validate_provided_hyperparameters(patched_get_model_specs):
    def add_options_to_hyperparameter(*largs, **kwargs):
        spec = get_spec_from_base_spec(*largs, **kwargs)
        spec.hyperparameters.extend(
            [
                JumpStartHyperparameter(
                    {
                        "name": "penalty",
                        "type": "text",
                        "default": "l2",
                        "options": ["l1", "l2", "elasticnet", "none"],
                        "scope": "algorithm",
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_bool_param",
                        "type": "bool",
                        "default": True,
                        "scope": "algorithm",
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_exclusive_min_param",
                        "type": "float",
                        "default": 4,
                        "scope": "algorithm",
                        "exclusive_min": 1,
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_exclusive_max_param",
                        "type": "int",
                        "default": -4,
                        "scope": "algorithm",
                        "exclusive_max": 4,
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_exclusive_min_param_text",
                        "type": "text",
                        "default": "hello",
                        "scope": "algorithm",
                        "exclusive_min": 1,
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_exclusive_max_param_text",
                        "type": "text",
                        "default": "hello",
                        "scope": "algorithm",
                        "exclusive_max": 6,
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_min_param_text",
                        "type": "text",
                        "default": "hello",
                        "scope": "algorithm",
                        "min": 1,
                    }
                ),
                JumpStartHyperparameter(
                    {
                        "name": "test_max_param_text",
                        "type": "text",
                        "default": "hello",
                        "scope": "algorithm",
                        "max": 6,
                    }
                ),
            ]
        )
        return spec

    patched_get_model_specs.side_effect = add_options_to_hyperparameter

    model_id, model_version = "pytorch-eqa-bert-base-cased", "*"
    region = "us-west-2"

    hyperparameter_to_test = {
        "adam-learning-rate": "0.05",
        "batch-size": "4",
        "epochs": "3",
        "penalty": "l2",
        "test_bool_param": False,
        "test_exclusive_min_param": 4,
        "test_exclusive_max_param": -4,
        "test_exclusive_min_param_text": "hello",
        "test_exclusive_max_param_text": "hello",
        "test_min_param_text": "hello",
        "test_max_param_text": "hello",
    }

    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
    )

    patched_get_model_specs.assert_called_once_with(
        region=region, model_id=model_id, version=model_version
    )

    patched_get_model_specs.reset_mock()

    del hyperparameter_to_test["adam-learning-rate"]

    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
    )

    hyperparameter_to_test["batch-size"] = "0"
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )

    hyperparameter_to_test["batch-size"] = "-1"
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )

    hyperparameter_to_test["batch-size"] = "-1.5"
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )

    hyperparameter_to_test["batch-size"] = "1.5"
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )

    hyperparameter_to_test["batch-size"] = "99999"
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )

    hyperparameter_to_test["batch-size"] = 5
    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
    )

    original_bool_val = hyperparameter_to_test["test_bool_param"]
    for val in ["False", "fAlSe", "false", "True", "TrUe", "true", True, False]:
        hyperparameter_to_test["test_bool_param"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in [None, "", 5, "Truesday", "Falsehood"]:
        hyperparameter_to_test["test_bool_param"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_bool_param"] = original_bool_val

    original_exclusive_min_val = hyperparameter_to_test["test_exclusive_min_param"]
    for val in [2, 1 + 1e-9]:
        hyperparameter_to_test["test_exclusive_min_param"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in [1, 1 - 1e-99, -99]:
        hyperparameter_to_test["test_exclusive_min_param"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_exclusive_min_param"] = original_exclusive_min_val

    original_exclusive_max_val = hyperparameter_to_test["test_exclusive_max_param"]
    for val in [-2, 2, 3]:
        hyperparameter_to_test["test_exclusive_max_param"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in [4, 5, 99]:
        hyperparameter_to_test["test_exclusive_max_param"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_exclusive_max_param"] = original_exclusive_max_val

    original_exclusive_max_text_val = hyperparameter_to_test["test_exclusive_max_param_text"]
    for val in ["", "sd", "12345"]:
        hyperparameter_to_test["test_exclusive_max_param_text"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in ["123456", "123456789"]:
        hyperparameter_to_test["test_exclusive_max_param_text"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_exclusive_max_param_text"] = original_exclusive_max_text_val

    original_max_text_val = hyperparameter_to_test["test_max_param_text"]
    for val in ["", "sd", "12345", "123456"]:
        hyperparameter_to_test["test_max_param_text"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in ["1234567", "123456789"]:
        hyperparameter_to_test["test_max_param_text"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_max_param_text"] = original_max_text_val

    original_exclusive_min_text_val = hyperparameter_to_test["test_exclusive_min_param_text"]
    for val in ["12", "sdfs", "12345dsfs"]:
        hyperparameter_to_test["test_exclusive_min_param_text"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in ["1", "d", ""]:
        hyperparameter_to_test["test_exclusive_min_param_text"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_exclusive_min_param_text"] = original_exclusive_min_text_val

    original_min_text_val = hyperparameter_to_test["test_min_param_text"]
    for val in ["1", "s", "12", "sdfs", "12345dsfs"]:
        hyperparameter_to_test["test_min_param_text"] = val
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )
    for val in [""]:
        hyperparameter_to_test["test_min_param_text"] = val
        with pytest.raises(JumpStartHyperparametersError):
            hyperparameters.validate(
                region=region,
                model_id=model_id,
                model_version=model_version,
                hyperparameters=hyperparameter_to_test,
            )
    hyperparameter_to_test["test_min_param_text"] = original_min_text_val

    del hyperparameter_to_test["batch-size"]
    hyperparameter_to_test["penalty"] = "blah"
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
        )

    hyperparameter_to_test["penalty"] = "elasticnet"
    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
    )


@patch("sagemaker.jumpstart.accessors.JumpStartModelsAccessor.get_model_specs")
def test_jumpstart_validate_algorithm_hyperparameters(patched_get_model_specs):
    def add_options_to_hyperparameter(*largs, **kwargs):
        spec = get_spec_from_base_spec(*largs, **kwargs)
        spec.hyperparameters.append(
            JumpStartHyperparameter(
                {
                    "name": "penalty",
                    "type": "text",
                    "default": "l2",
                    "options": ["l1", "l2", "elasticnet", "none"],
                    "scope": "algorithm",
                }
            )
        )
        return spec

    patched_get_model_specs.side_effect = add_options_to_hyperparameter

    model_id, model_version = "pytorch-eqa-bert-base-cased", "*"
    region = "us-west-2"

    hyperparameter_to_test = {
        "adam-learning-rate": "0.05",
        "batch-size": "4",
        "epochs": "3",
        "penalty": "l2",
    }

    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
        validation_mode=HyperparameterValidationMode.VALIDATE_ALGORITHM,
    )

    patched_get_model_specs.assert_called_once_with(
        region=region, model_id=model_id, version=model_version
    )

    patched_get_model_specs.reset_mock()

    hyperparameter_to_test["random-param"] = "random_val"
    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
        validation_mode=HyperparameterValidationMode.VALIDATE_ALGORITHM,
    )

    del hyperparameter_to_test["adam-learning-rate"]
    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
            validation_mode=HyperparameterValidationMode.VALIDATE_ALGORITHM,
        )


@patch("sagemaker.jumpstart.accessors.JumpStartModelsAccessor.get_model_specs")
def test_jumpstart_validate_all_hyperparameters(patched_get_model_specs):

    patched_get_model_specs.side_effect = get_spec_from_base_spec

    model_id, model_version = "pytorch-eqa-bert-base-cased", "*"
    region = "us-west-2"

    hyperparameter_to_test = {
        "adam-learning-rate": "0.05",
        "batch-size": "4",
        "epochs": "3",
        "sagemaker_container_log_level": "20",
        "sagemaker_program": "transfer_learning.py",
        "sagemaker_submit_directory": "/opt/ml/input/data/code/sourcedir.tar.gz",
    }

    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
        validation_mode=HyperparameterValidationMode.VALIDATE_ALL,
    )

    patched_get_model_specs.assert_called_once_with(
        region=region, model_id=model_id, version=model_version
    )

    patched_get_model_specs.reset_mock()

    del hyperparameter_to_test["sagemaker_submit_directory"]

    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
            validation_mode=HyperparameterValidationMode.VALIDATE_ALL,
        )

    hyperparameter_to_test[
        "sagemaker_submit_directory"
    ] = "/opt/ml/input/data/code/sourcedir.tar.gz"
    del hyperparameter_to_test["epochs"]

    with pytest.raises(JumpStartHyperparametersError):
        hyperparameters.validate(
            region=region,
            model_id=model_id,
            model_version=model_version,
            hyperparameters=hyperparameter_to_test,
            validation_mode=HyperparameterValidationMode.VALIDATE_ALL,
        )

    hyperparameter_to_test["epochs"] = "3"

    hyperparameter_to_test["other_hyperparam"] = "blah"
    hyperparameters.validate(
        region=region,
        model_id=model_id,
        model_version=model_version,
        hyperparameters=hyperparameter_to_test,
        validation_mode=HyperparameterValidationMode.VALIDATE_ALL,
    )
