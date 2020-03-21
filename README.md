# rako mqtt

A component to attach rako lights (via the rako bridge) to an mqtt broker for use with home assistant.
[Rako bridge interaction guide](accessing-the-rako-bridge.pdf).

Only tested with [mosquitto](https://mosquitto.org/)

## Architecture

There are 2 modes (env var = `APP_MODE`):

- `watcher` mode listens for the rako bridge to issue change of state commands, then posts a home assistant compatible message to your mqtt broker
- `commander` mode subscribes to the home assistant topic and upon receiving a message, posts a command to the rako bridge


## Config

There are 4 env vars to be aware of:
- `APP_MODE` = state_watcher or commander
- `MOSQUITTO_HOST` = host for you mqtt broker (currently hardcoded to port 1883)
- `MOSQUITTO_USER` = username for you mqtt broker
- `MOSQUITTO_PASSWORD` = password for you mqtt broker


## Run

```bash
python -um rakomqtt
```


## Build and deploy

```bash
docker-compose -f docker-compose.yaml up -d --build
```


## Home assistant light config

Use the Home assistant [mqtt light platform](https://www.home-assistant.io/components/light.mqtt/). 
```yaml
- platform: mqtt
  name: <name of the room>
  schema: json
  state_topic: "rako/room/<rako-room-id>"
  command_topic: "rako/room/<rako-room-id>/set"
  brightness: true
```

For example
```yaml
- platform: mqtt
  name: hallway
  schema: json
  state_topic: "rako/room/42"
  command_topic: "rako/room/42/set"
  brightness: true
```

