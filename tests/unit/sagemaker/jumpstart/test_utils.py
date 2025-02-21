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
from mock.mock import Mock, patch
import pytest
import random
from sagemaker.jumpstart import utils
from sagemaker.jumpstart.constants import (
    JUMPSTART_BUCKET_NAME_SET,
    JUMPSTART_REGION_NAME_SET,
    JumpStartScriptScope,
)
from sagemaker.jumpstart.enums import JumpStartTag
from sagemaker.jumpstart.exceptions import (
    DeprecatedJumpStartModelError,
    VulnerableJumpStartModelError,
)
from sagemaker.jumpstart.types import JumpStartModelHeader, JumpStartVersionedModelId
from tests.unit.sagemaker.jumpstart.utils import get_spec_from_base_spec


def random_jumpstart_s3_uri(key):
    return f"s3://{random.choice(list(JUMPSTART_BUCKET_NAME_SET))}/{key}"


def test_get_jumpstart_content_bucket():
    bad_region = "bad_region"
    assert bad_region not in JUMPSTART_REGION_NAME_SET
    with pytest.raises(ValueError):
        utils.get_jumpstart_content_bucket(bad_region)


def test_get_jumpstart_launched_regions_message():

    with patch("sagemaker.jumpstart.constants.JUMPSTART_REGION_NAME_SET", {}):
        assert (
            utils.get_jumpstart_launched_regions_message()
            == "JumpStart is not available in any region."
        )

    with patch("sagemaker.jumpstart.constants.JUMPSTART_REGION_NAME_SET", {"some_region"}):
        assert (
            utils.get_jumpstart_launched_regions_message()
            == "JumpStart is available in some_region region."
        )

    with patch(
        "sagemaker.jumpstart.constants.JUMPSTART_REGION_NAME_SET", {"some_region1", "some_region2"}
    ):
        assert (
            utils.get_jumpstart_launched_regions_message()
            == "JumpStart is available in some_region1 and some_region2 regions."
        )

    with patch("sagemaker.jumpstart.constants.JUMPSTART_REGION_NAME_SET", {"a", "b", "c"}):
        assert (
            utils.get_jumpstart_launched_regions_message()
            == "JumpStart is available in a, b, and c regions."
        )


def test_get_formatted_manifest():
    mock_manifest = [
        {
            "model_id": "tensorflow-ic-imagenet-inception-v3-classification-4",
            "version": "1.0.0",
            "min_version": "2.49.0",
            "spec_key": "community_models_specs/tensorflow-ic-imagenet-inception-v3-classification-4/specs_v1.0.0.json",
        },
    ]

    assert utils.get_formatted_manifest(mock_manifest) == {
        JumpStartVersionedModelId(
            "tensorflow-ic-imagenet-inception-v3-classification-4", "1.0.0"
        ): JumpStartModelHeader(mock_manifest[0])
    }

    assert utils.get_formatted_manifest([]) == {}


def test_parse_sagemaker_version():

    with patch("sagemaker.__version__", "1.2.3"):
        assert utils.parse_sagemaker_version() == "1.2.3"

    with patch("sagemaker.__version__", "1.2.3.3332j"):
        assert utils.parse_sagemaker_version() == "1.2.3"

    with patch("sagemaker.__version__", "1.2.3."):
        assert utils.parse_sagemaker_version() == "1.2.3"

    with pytest.raises(ValueError):
        with patch("sagemaker.__version__", "1.2.3dfsdfs"):
            utils.parse_sagemaker_version()

    with pytest.raises(RuntimeError):
        with patch("sagemaker.__version__", "1.2"):
            utils.parse_sagemaker_version()

    with pytest.raises(RuntimeError):
        with patch("sagemaker.__version__", "1"):
            utils.parse_sagemaker_version()

    with pytest.raises(RuntimeError):
        with patch("sagemaker.__version__", ""):
            utils.parse_sagemaker_version()

    with pytest.raises(RuntimeError):
        with patch("sagemaker.__version__", "1.2.3.4.5"):
            utils.parse_sagemaker_version()


@patch("sagemaker.jumpstart.utils.parse_sagemaker_version")
@patch("sagemaker.jumpstart.accessors.SageMakerSettings._parsed_sagemaker_version", "")
def test_get_sagemaker_version(patched_parse_sm_version: Mock):
    utils.get_sagemaker_version()
    utils.get_sagemaker_version()
    utils.get_sagemaker_version()
    assert patched_parse_sm_version.called_only_once()


def test_is_jumpstart_model_uri():

    assert not utils.is_jumpstart_model_uri("fdsfdsf")
    assert not utils.is_jumpstart_model_uri("s3://not-jumpstart-bucket/sdfsdfds")
    assert not utils.is_jumpstart_model_uri("some/actual/localfile")

    assert utils.is_jumpstart_model_uri(
        random_jumpstart_s3_uri("source_directory_tarballs/sourcedir.tar.gz")
    )
    assert utils.is_jumpstart_model_uri(random_jumpstart_s3_uri("random_key"))


def test_add_jumpstart_tags_inference():
    tags = None
    inference_model_uri = "dfsdfsd"
    inference_script_uri = "dfsdfs"
    assert (
        utils.add_jumpstart_tags(
            tags=tags,
            inference_model_uri=inference_model_uri,
            inference_script_uri=inference_script_uri,
        )
        is None
    )

    tags = []
    inference_model_uri = "dfsdfsd"
    inference_script_uri = "dfsdfs"
    assert (
        utils.add_jumpstart_tags(
            tags=tags,
            inference_model_uri=inference_model_uri,
            inference_script_uri=inference_script_uri,
        )
        == []
    )

    tags = [{"Key": "some", "Value": "tag"}]
    inference_model_uri = "dfsdfsd"
    inference_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [{"Key": "some", "Value": "tag"}]

    tags = None
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    inference_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [{"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": inference_model_uri}]

    tags = []
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    inference_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [{"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": inference_model_uri}]

    tags = [{"Key": "some", "Value": "tag"}]
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    inference_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {"Key": "some", "Value": "tag"},
        {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": inference_model_uri},
    ]

    tags = None
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [{"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri}]

    tags = []
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [{"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri}]

    tags = [{"Key": "some", "Value": "tag"}]
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {"Key": "some", "Value": "tag"},
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri},
    ]

    tags = None
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {
            "Key": JumpStartTag.INFERENCE_MODEL_URI.value,
            "Value": inference_model_uri,
        },
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri},
    ]

    tags = []
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {
            "Key": JumpStartTag.INFERENCE_MODEL_URI.value,
            "Value": inference_model_uri,
        },
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri},
    ]

    tags = [{"Key": "some", "Value": "tag"}]
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {"Key": "some", "Value": "tag"},
        {
            "Key": JumpStartTag.INFERENCE_MODEL_URI.value,
            "Value": inference_model_uri,
        },
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri},
    ]

    tags = [{"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": "garbage-value"}]
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": inference_script_uri},
    ]

    tags = [{"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": "garbage-value"}]
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": inference_model_uri},
    ]

    tags = [
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": "garbage-value-2"},
    ]
    inference_script_uri = random_jumpstart_s3_uri("random_key")
    inference_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        inference_model_uri=inference_model_uri,
        inference_script_uri=inference_script_uri,
    ) == [
        {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": "garbage-value-2"},
    ]


def test_add_jumpstart_tags_training():
    tags = None
    training_model_uri = "dfsdfsd"
    training_script_uri = "dfsdfs"
    assert (
        utils.add_jumpstart_tags(
            tags=tags,
            training_model_uri=training_model_uri,
            training_script_uri=training_script_uri,
        )
        is None
    )

    tags = []
    training_model_uri = "dfsdfsd"
    training_script_uri = "dfsdfs"
    assert (
        utils.add_jumpstart_tags(
            tags=tags,
            training_model_uri=training_model_uri,
            training_script_uri=training_script_uri,
        )
        == []
    )

    tags = [{"Key": "some", "Value": "tag"}]
    training_model_uri = "dfsdfsd"
    training_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [{"Key": "some", "Value": "tag"}]

    tags = None
    training_model_uri = random_jumpstart_s3_uri("random_key")
    training_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [{"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": training_model_uri}]

    tags = []
    training_model_uri = random_jumpstart_s3_uri("random_key")
    training_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [{"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": training_model_uri}]

    tags = [{"Key": "some", "Value": "tag"}]
    training_model_uri = random_jumpstart_s3_uri("random_key")
    training_script_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {"Key": "some", "Value": "tag"},
        {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": training_model_uri},
    ]

    tags = None
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [{"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri}]

    tags = []
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [{"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri}]

    tags = [{"Key": "some", "Value": "tag"}]
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = "dfsdfs"
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {"Key": "some", "Value": "tag"},
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri},
    ]

    tags = None
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {
            "Key": JumpStartTag.TRAINING_MODEL_URI.value,
            "Value": training_model_uri,
        },
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri},
    ]

    tags = []
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {
            "Key": JumpStartTag.TRAINING_MODEL_URI.value,
            "Value": training_model_uri,
        },
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri},
    ]

    tags = [{"Key": "some", "Value": "tag"}]
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {"Key": "some", "Value": "tag"},
        {
            "Key": JumpStartTag.TRAINING_MODEL_URI.value,
            "Value": training_model_uri,
        },
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri},
    ]

    tags = [{"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": "garbage-value"}]
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": training_script_uri},
    ]

    tags = [{"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": "garbage-value"}]
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": training_model_uri},
    ]

    tags = [
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": "garbage-value-2"},
    ]
    training_script_uri = random_jumpstart_s3_uri("random_key")
    training_model_uri = random_jumpstart_s3_uri("random_key")
    assert utils.add_jumpstart_tags(
        tags=tags,
        training_model_uri=training_model_uri,
        training_script_uri=training_script_uri,
    ) == [
        {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": "garbage-value"},
        {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": "garbage-value-2"},
    ]


def test_update_inference_tags_with_jumpstart_training_script_tags():

    random_tag_1 = {"Key": "tag-key-1", "Value": "tag-val-1"}
    random_tag_2 = {"Key": "tag-key-2", "Value": "tag-val-2"}

    js_tag = {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": "garbage-value"}
    js_tag_2 = {"Key": JumpStartTag.TRAINING_SCRIPT_URI.value, "Value": "garbage-value-2"}

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=None
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[]
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1]
    )

    assert [random_tag_2, js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [random_tag_2, js_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2, js_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=None
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1, js_tag]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=None
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1, js_tag]
    )


def test_update_inference_tags_with_jumpstart_training_model_tags():

    random_tag_1 = {"Key": "tag-key-1", "Value": "tag-val-1"}
    random_tag_2 = {"Key": "tag-key-2", "Value": "tag-val-2"}

    js_tag = {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": "garbage-value"}
    js_tag_2 = {"Key": JumpStartTag.TRAINING_MODEL_URI.value, "Value": "garbage-value-2"}

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=None
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[]
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1]
    )

    assert [random_tag_2, js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [random_tag_2, js_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2, js_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=None
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1, js_tag]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=None
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1, js_tag]
    )


def test_update_inference_tags_with_jumpstart_training_script_tags_inference():

    random_tag_1 = {"Key": "tag-key-1", "Value": "tag-val-1"}
    random_tag_2 = {"Key": "tag-key-2", "Value": "tag-val-2"}

    js_tag = {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": "garbage-value"}
    js_tag_2 = {"Key": JumpStartTag.INFERENCE_SCRIPT_URI.value, "Value": "garbage-value-2"}

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=None
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[]
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1]
    )

    assert [random_tag_2, js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [random_tag_2, js_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2, js_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=None
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1, js_tag]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=None
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1, js_tag]
    )


def test_update_inference_tags_with_jumpstart_training_model_tags_inference():

    random_tag_1 = {"Key": "tag-key-1", "Value": "tag-val-1"}
    random_tag_2 = {"Key": "tag-key-2", "Value": "tag-val-2"}

    js_tag = {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": "garbage-value"}
    js_tag_2 = {"Key": JumpStartTag.INFERENCE_MODEL_URI.value, "Value": "garbage-value-2"}

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=None
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[]
    )

    assert [random_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1]
    )

    assert [random_tag_2, js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [random_tag_2, js_tag_2] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[random_tag_2, js_tag_2], training_tags=[random_tag_1, js_tag]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=None
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[]
    )

    assert [] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=[], training_tags=[random_tag_1, js_tag]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=None
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[]
    )

    assert None is utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1]
    )

    assert [js_tag] == utils.update_inference_tags_with_jumpstart_training_tags(
        inference_tags=None, training_tags=[random_tag_1, js_tag]
    )


@patch("sagemaker.jumpstart.accessors.JumpStartModelsAccessor.get_model_specs")
def test_jumpstart_vulnerable_model(patched_get_model_specs):
    def make_vulnerable_inference_spec(*largs, **kwargs):
        spec = get_spec_from_base_spec(*largs, **kwargs)
        spec.inference_vulnerable = True
        spec.inference_vulnerabilities = ["some", "vulnerability"]
        return spec

    patched_get_model_specs.side_effect = make_vulnerable_inference_spec

    with pytest.raises(VulnerableJumpStartModelError) as e:
        utils.verify_model_region_and_return_specs(
            model_id="pytorch-eqa-bert-base-cased",
            version="*",
            scope=JumpStartScriptScope.INFERENCE.value,
            region="us-west-2",
        )
    assert (
        "Version '*' of JumpStart model 'pytorch-eqa-bert-base-cased' has at least 1 "
        "vulnerable dependency in the inference script. "
        "Please try targetting a higher version of the model. "
        "List of vulnerabilities: some, vulnerability"
    ) == str(e.value.message)

    with patch("logging.Logger.warning") as mocked_warning_log:
        assert (
            utils.verify_model_region_and_return_specs(
                model_id="pytorch-eqa-bert-base-cased",
                version="*",
                scope=JumpStartScriptScope.INFERENCE.value,
                region="us-west-2",
                tolerate_vulnerable_model=True,
            )
            is not None
        )
        mocked_warning_log.assert_called_once_with(
            "Using vulnerable JumpStart model '%s' and version '%s' (inference).",
            "pytorch-eqa-bert-base-cased",
            "*",
        )

    def make_vulnerable_training_spec(*largs, **kwargs):
        spec = get_spec_from_base_spec(*largs, **kwargs)
        spec.training_vulnerable = True
        spec.training_vulnerabilities = ["some", "vulnerability"]
        return spec

    patched_get_model_specs.side_effect = make_vulnerable_training_spec

    with pytest.raises(VulnerableJumpStartModelError) as e:
        utils.verify_model_region_and_return_specs(
            model_id="pytorch-eqa-bert-base-cased",
            version="*",
            scope=JumpStartScriptScope.TRAINING.value,
            region="us-west-2",
        )
    assert (
        "Version '*' of JumpStart model 'pytorch-eqa-bert-base-cased' has at least 1 "
        "vulnerable dependency in the training script. "
        "Please try targetting a higher version of the model. "
        "List of vulnerabilities: some, vulnerability"
    ) == str(e.value.message)

    with patch("logging.Logger.warning") as mocked_warning_log:
        assert (
            utils.verify_model_region_and_return_specs(
                model_id="pytorch-eqa-bert-base-cased",
                version="*",
                scope=JumpStartScriptScope.TRAINING.value,
                region="us-west-2",
                tolerate_vulnerable_model=True,
            )
            is not None
        )
        mocked_warning_log.assert_called_once_with(
            "Using vulnerable JumpStart model '%s' and version '%s' (training).",
            "pytorch-eqa-bert-base-cased",
            "*",
        )


@patch("sagemaker.jumpstart.accessors.JumpStartModelsAccessor.get_model_specs")
def test_jumpstart_deprecated_model(patched_get_model_specs):
    def make_deprecated_spec(*largs, **kwargs):
        spec = get_spec_from_base_spec(*largs, **kwargs)
        spec.deprecated = True
        return spec

    patched_get_model_specs.side_effect = make_deprecated_spec

    with pytest.raises(DeprecatedJumpStartModelError) as e:
        utils.verify_model_region_and_return_specs(
            model_id="pytorch-eqa-bert-base-cased",
            version="*",
            scope=JumpStartScriptScope.INFERENCE.value,
            region="us-west-2",
        )
    assert "Version '*' of JumpStart model 'pytorch-eqa-bert-base-cased' is deprecated. "
    "Please try targetting a higher version of the model." == str(e.value.message)

    with patch("logging.Logger.warning") as mocked_warning_log:
        assert (
            utils.verify_model_region_and_return_specs(
                model_id="pytorch-eqa-bert-base-cased",
                version="*",
                scope=JumpStartScriptScope.INFERENCE.value,
                region="us-west-2",
                tolerate_deprecated_model=True,
            )
            is not None
        )
        mocked_warning_log.assert_called_once_with(
            "Using deprecated JumpStart model '%s' and version '%s'.",
            "pytorch-eqa-bert-base-cased",
            "*",
        )
