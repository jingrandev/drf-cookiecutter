from rest_framework.exceptions import ValidationError


class StrictSerializerMixin:
    """Serializer mixin that rejects unknown fields in request data.

    By default DRF silently ignores fields that are not declared on the
    serializer.  This mixin changes that behaviour so that typos or
    outdated API clients are caught early with a 400 error.

    Usage::

        class MySerializer(StrictSerializerMixin, serializers.ModelSerializer):
            class Meta:
                model = MyModel
                fields = ["id", "name"]

    Now a request with ``{"name": "ok", "typo": 1}`` will return::

        400 {"name": ["Unknown field: typo"]}
    """

    def to_internal_value(self, data):
        self._raw_input_data = data
        return super().to_internal_value(data)

    def validate(self, attrs):
        raw = getattr(self, "_raw_input_data", None)
        if raw is not None and isinstance(raw, dict):
            known = set(self.fields.keys())
            # DRF adds a "type" field for polymorphic / custom-field registries
            type_field = getattr(self, "type_field_name", None)
            if type_field:
                known.discard(type_field)
            unknown = set(raw.keys()) - known
            if unknown:
                raise ValidationError(
                    {field: ["Unknown field."] for field in sorted(unknown)}
                )
        return super().validate(attrs)
