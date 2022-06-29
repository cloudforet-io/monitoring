import jsonschema
from schematics import Model
from schematics.exceptions import ValidationError
from schematics.types import BaseType, ListType, DictType, StringType
from schematics.types.compound import ModelType

__all__ = ['MetricPluginMetadataModel', 'LogPluginMetadataModel']


class JSONSchemaType(BaseType):
    def validate_netloc(self, value):
        try:
            jsonschema.Draft7Validator.check_schema(value)
        except Exception as e:
            raise ValidationError(key=f'Plugin metadata is invalid. (filter_format = {str(value)}')


class DynamicField(Model):
    name = StringType(required=True)
    key = StringType(required=True)
    type = StringType()
    option = DictType(StringType)


class TemplateModel(Model):
    table = ListType(ModelType(DynamicField))


class MetricPluginMetadataModel(Model):
    supported_stat = ListType(StringType, required=True)
    required_keys = ListType(StringType)


class LogPluginMetadataModel(Model):
    required_keys = ListType(StringType)
    view = DictType(BaseType)
