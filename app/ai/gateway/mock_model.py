
from typing import Any


class MockClinicalModel:

    def __init__(self, response: Any):
        self.response = response

    def with_structured_output(self, schema, **kwargs):

        response = self.response

        class StructuredMock:

            def invoke(self, inputs, config=None, **kw):
                if isinstance(response, dict):
                    return schema.model_validate(response)

                return response

        return StructuredMock()
