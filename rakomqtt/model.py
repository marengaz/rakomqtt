from marshmallow import Schema, fields, post_load, validate


class MqttPayloadSchema(Schema):
    state = fields.Str(validate=validate.OneOf(choices=('ON', 'OFF')))
    brightness = fields.Int(validate=validate.Range(min=0, max=255))

    @post_load
    def post_load(self, item, many, **kwargs):
        if item.get('brightness') is None and item['state'] == 'ON':
            item['brightness'] = 255
        if item.get('brightness') is None and item['state'] == 'OFF':
            item['brightness'] = 0
        return item


mqtt_payload_schema = MqttPayloadSchema()
