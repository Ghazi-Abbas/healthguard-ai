from typing import Any

from app.security.classification import (
    DataClassification,
    classify_field,
)


CLASSIFICATION_PRIORITY = {
    DataClassification.PUBLIC: 1,
    DataClassification.INTERNAL: 2,
    DataClassification.PII: 3,
    DataClassification.PHI: 4,
    DataClassification.SECRET: 5,
}


def get_highest_classification(data: Any) -> DataClassification:
    """
    Inspect nested dictionaries and lists.

    Return the highest classification found.

    Reject unknown fields instead of assigning INTERNAL.
    """

    classifications = []

    def inspect(value: Any):

        if isinstance(value, dict):

            for key, nested_value in value.items():

                if not isinstance(key, str):
                    raise ValueError(
                        "Classification field names must be strings."
                    )

                field_classification = classify_field(key)

                classifications.append(field_classification)

                inspect(nested_value)

        elif isinstance(value, list):

            for item in value:
                inspect(item)

    if not isinstance(data, dict) or not data:
        raise ValueError(
            "Input must be a non-empty dictionary."
        )

    inspect(data)

    if not classifications:
        raise ValueError(
            "No classifiable fields were found."
        )

    return max(
        classifications,
        key=lambda item: CLASSIFICATION_PRIORITY[item],
    )
