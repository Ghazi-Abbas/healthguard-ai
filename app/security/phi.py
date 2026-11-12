from app.security.classification import (
    DataClassification,
    classify_field,
)


def is_phi_field(field_name: str) -> bool:
    """
    Check whether a field is classified as PHI.
    """

    return (
        classify_field(field_name)
        == DataClassification.PHI
    )
