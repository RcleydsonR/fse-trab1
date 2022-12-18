import socket
import select
import sys
import json
from typing import TextIO
from datetime import datetime
import utils
import RPi.GPIO as GPIO
import Adafruit_DHT
from time import sleep
import threading

class Worker():
    server: socket.socket
    ip: str
    port: int
    inputs: "list[socket.socket | TextIO]"
    id_on_server: str

    def __init__(self, config):
        # read json config file
        try:
            config_file = open(config)
            self.config_data = json.load(config_file)
            config_file.close()
        except:
            print("Arquivo invalido, tenha certeza de passar um arquivo json seguindo o exemplo!")
            sys.exit()

        # server tcp/ip configs
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id_on_server = f"{self.config_data['ip_servidor_distribuido']}:{self.config_data['nome']}"
        try:
            self.server.connect((self.config_data["ip_servidor_central"], self.config_data["porta_servidor_central"]))
            self.server.send(utils.encode_message(type="worker_identify", id=self.id_on_server))
        except:
            print("Servidor inatingivel, verifique o ip e porta passado no arquivo de configuracao")
            sys.exit()

        self.inputs = [self.server]
        self.running = False

        # initialize gpio, ports and related states
        self.initial_state()

    def initial_state(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.light_1 = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.L_01.value)["gpio"],
        self.light_2 = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.L_02.value)["gpio"],
        self.air_conditioning = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.AC.value)["gpio"]
        self.projector = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.PR.value)["gpio"]
        self.alarm_buzzer = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.AL_BZ.value)["gpio"]
        self.presence_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SPres.value)["gpio"]
        self.smoke_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SFum.value)["gpio"]
        self.window_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SJan.value)["gpio"]
        self.door_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SPor.value)["gpio"]
        self.entry_people_counting_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SC_IN.value)["gpio"]
        self.exit_people_counting_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SC_OUT.value)["gpio"]
        self.temperature_sensor = self.config_data["sensor_temperatura"]["gpio"]

        self.input_sensors = {
            self.presence_sensor: {"id": utils.Sensor.SPres.value, "callback_func": self._presence_sensor_callback},
            self.smoke_sensor: {"id": utils.Sensor.SFum.value, "callback_func": self._smoke_sensor_callback},
            self.window_sensor: {"id": utils.Sensor.SJan.value, "callback_func": self._window_sensor_callback},
            self.door_sensor: {"id": utils.Sensor.SPor.value, "callback_func": self._door_sensor_callback},
            self.entry_people_counting_sensor: {"id": utils.Sensor.SC_IN.value, "callback_func": self._entry_sensor_callback},
            self.exit_people_counting_sensor : {"id": utils.Sensor.SC_OUT.value, "callback_func": self._exit_sensor_callback},
        }

        self._setup_sensors()

        self.states = {
            utils.Sensor.L_01.value: GPIO.input(self.light_1[0]),
            utils.Sensor.L_02.value: GPIO.input(self.light_2[0]),
            utils.Sensor.AC.value: GPIO.input(self.air_conditioning),
            utils.Sensor.PR.value: GPIO.input(self.projector),
            utils.Sensor.AL_BZ.value: GPIO.input(self.alarm_buzzer),
            utils.Sensor.SPres.value: GPIO.input(self.presence_sensor),
            utils.Sensor.SFum.value: GPIO.input(self.smoke_sensor),
            utils.Sensor.SJan.value: GPIO.input(self.window_sensor),
            utils.Sensor.SPor.value: GPIO.input(self.door_sensor),
            utils.Sensor.SC_IN.value: GPIO.input(self.entry_people_counting_sensor),
            utils.Sensor.SC_OUT.value: GPIO.input(self.exit_people_counting_sensor),
            utils.Sensor.Temperature.value: 0,
            utils.Sensor.Humidity.value: 0,
            utils.Sensor.Alarme.value: 0
        }

    def _setup_sensors(self):
        GPIO.setup(self.light_1, GPIO.OUT)
        GPIO.setup(self.light_2, GPIO.OUT)
        GPIO.setup(self.air_conditioning, GPIO.OUT)
        GPIO.setup(self.projector, GPIO.OUT)
        GPIO.setup(self.alarm_buzzer, GPIO.OUT)
        for sensor in self.input_sensors:
            GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def turn_on_off_outputs(self, output_ids, value):
        outputs = []
        for id in output_ids:
            outputs.append(utils.get_obj_by_element(self.config_data["outputs"], 'id', id)["gpio"])
        GPIO.output(outputs, value)
        for index, output in enumerate(outputs):
            if GPIO.input(output) == value:
                self.states[output_ids[index]] = value
            else:
                return False
        return True

    def verifyTemperature(self):
        humidity, temperature = Adafruit_DHT.read_retry(22, self.temperature_sensor)
        if humidity is not None and temperature is not None:
            self.states[utils.Sensor.Temperature.value] = temperature
            self.states[utils.Sensor.Humidity.value] = humidity
            self._send_states_update_message([utils.Sensor.Temperature.value, utils.Sensor.Humidity.value], [temperature, humidity])
    
    def _turn_off_lights_in_15_seconds(self):
        sleep(15)
        if GPIO.input(self.presence_sensor) == 0:
            self.turn_on_off_outputs([utils.Sensor.L_01.value, utils.Sensor.L_02.value], 0)
    
    def _apply_presence_sensor_logic(self):
        if GPIO.input(self.presence_sensor) == 1:
            breakpoint()
            if self.states[utils.Sensor.Alarme.value] == 1:
                self.turn_on_off_outputs([utils.Sensor.AL_BZ.value], 1)
            else:
                self.turn_on_off_outputs([utils.Sensor.L_01.value, utils.Sensor.L_02.value], 1)
        else:
            threading.Thread(target=self._turn_off_lights_in_15_seconds()).start()
    
    def apply_sensor_transition(self, sensor):
        new_state = 1 if GPIO.input(sensor) else 0
        self.states[self.input_sensors[sensor]["id"]] = new_state
        return new_state

    def restart_sensor_event_detection(self, sensor, callback_func):
        GPIO.remove_event_detect(sensor)
        GPIO.add_event_detect(sensor, GPIO.BOTH, callback=callback_func, bouncetime=200)

    def _presence_sensor_callback(self, sensor):
        new_state = self.apply_sensor_transition(sensor)
        self._apply_presence_sensor_logic()
        self._send_states_update_message([utils.Sensor.SPres.value], [new_state])
        self.restart_sensor_event_detection(sensor, self._presence_sensor_callback)

    def _smoke_sensor_callback(self, sensor):
        new_state = self.apply_sensor_transition(sensor)
        if new_state == 1:
            self.turn_on_off_outputs([utils.Sensor.AL_BZ.value], 1)
        if ((new_state == 0 and self.states[utils.Sensor.Alarme.value] == 0)
            or new_state == 0 and self.states[utils.Sensor.SJan.value] == 0
            and self.states[utils.Sensor.SPor.value] == 0 and self.states[utils.Sensor.SPres.value] == 0):
            self.turn_on_off_outputs([utils.Sensor.AL_BZ.value], 0)
        self._send_states_update_message([utils.Sensor.SFum.value], [new_state])
        self.restart_sensor_event_detection(sensor, self._smoke_sensor_callback)

    def _window_sensor_callback(self, sensor):
        new_state = self.apply_sensor_transition(sensor)
        self._send_states_update_message([utils.Sensor.SJan.value], [new_state])
        self.restart_sensor_event_detection(sensor, self._window_sensor_callback)

    def _door_sensor_callback(self, sensor):
        new_state = self.apply_sensor_transition(sensor)
        self._send_states_update_message([utils.Sensor.SPor.value], [new_state])
        self.restart_sensor_event_detection(sensor, self._door_sensor_callback)

    def _entry_sensor_callback(self, sensor):
        self.states[self.input_sensors[sensor]["id"]] += 1
        self._send_states_update_message([utils.Sensor.SC_IN.value], [self.states[self.input_sensors[sensor]["id"]]])
        GPIO.remove_event_detect(sensor)
        GPIO.add_event_detect(sensor, GPIO.RISING, callback=self._entry_sensor_callback, bouncetime=200)

    def _exit_sensor_callback(self, sensor):
        self.states[self.input_sensors[sensor]["id"]] += 1
        self._send_states_update_message([utils.Sensor.SC_OUT.value], [self.states[self.input_sensors[sensor]["id"]]])
        self.restart_sensor_event_detection(sensor, self._exit_sensor_callback)
        GPIO.remove_event_detect(sensor)
        GPIO.add_event_detect(sensor, GPIO.RISING, callback=self._entry_sensor_callback, bouncetime=200)

    def input_proc(self):
        for sensor in self.input_sensors:
            if sensor in [self.entry_people_counting_sensor, self.exit_people_counting_sensor]:
                GPIO.add_event_detect(sensor, GPIO.RISING, callback=self.input_sensors[sensor]["callback_func"], bouncetime=200)
                continue
            GPIO.add_event_detect(sensor, GPIO.BOTH, callback=self.input_sensors[sensor]["callback_func"], bouncetime=200)

        while self.running:
            self.verifyTemperature()
            sleep(2)

    def start(self):
        print(f"Conectado ao servidor central.\nIP: {self.config_data['ip_servidor_central']}\nPORT: {self.config_data['porta_servidor_central']}")
        self.running = True
        self._run()

    def exit(self, message):
        print(message)
        self.running = False
        self.inputs = []
        GPIO.cleanup()
        self.server.close()

    def _try_to_reconnect(self, message):
        print(message)
        self.running = False
        self.server.detach()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(10):
            print(f"Tentativa de reconexão {i + 1} de 10.")
            try:
                self.server.connect((self.config_data["ip_servidor_central"], self.config_data["porta_servidor_central"]))
                self.server.send(utils.encode_message(type="worker_identify", states=self.states, id=self.id_on_server))
            except Exception as e:
                sleep(2)
                continue
            
            self.inputs = [self.server]
            self.running = True
            print(f"\nServidor central de volta ao ar.\nIP: {self.config_data['ip_servidor_central']}\nPORT: {self.config_data['porta_servidor_central']}")
            self._run()
            return

        self.exit("Tentativas falharam, desconectando esse servidor.")
    
    def _run(self):
        while self.running:
            inputs, _, _ = select.select(self.inputs,[],[])

            for input in inputs:
                self._handle_input(input)

    def _handle_input(self, inputs):
        if inputs == self.server:
            data = inputs.recv(2048).decode("utf-8")
            if data == "":
                threading.Thread(target=self._try_to_reconnect("servidor central foi desligado ou caiu")).start()
                return
            json_data = json.loads(data)
            self._decode_server_message(json_data)
                
    def _send_states_update_message(self, states_id, values):
        self.server.send(
            utils.encode_message(
                type="states_update", worker_id=self.id_on_server, states_id=states_id, values = values
        ))

    def _decode_server_message(self, json_msg):
        if(json_msg["type"] == "invalid_id"):
            self.exit("O ip e nome da sala que estao no arquivo de configuracao json ja estao em uso")
        if (json_msg["type"] == "trigger_output"):
            state_id = json_msg["state_id"]
            command = self.turn_on_off_outputs([state_id], json_msg["value"])
            self.server.send(utils.encode_message(type="confirmation", success=command, worker_id=self.id_on_server, states_id=[state_id], values = [json_msg["value"]]))
        elif (json_msg["type"] == "turn_on_all_lights"):
            command = self.turn_on_off_outputs([utils.Sensor.L_01.value, utils.Sensor.L_02.value], 1)
            self.server.send(utils.encode_message(type="confirmation", success=command, worker_id=self.id_on_server, states_id=[utils.Sensor.L_01.value, utils.Sensor.L_02.value], values = [1, 1]))
        elif (json_msg["type"] == "turn_off_all_lights"):
            command = self.turn_on_off_outputs([utils.Sensor.L_01.value, utils.Sensor.L_02.value], 0)
            self.server.send(utils.encode_message(type="confirmation", success=command, worker_id=self.id_on_server, states_id=[utils.Sensor.L_01.value, utils.Sensor.L_02.value], values = [0, 0]))
        elif (json_msg["type"] == "turn_off_all"):
            command = self.turn_on_off_outputs([utils.Sensor.L_01.value, utils.Sensor.L_02.value, utils.Sensor.AC.value, utils.Sensor.PR.value], 0)
            self.server.send(
                utils.encode_message(
                    type="confirmation", success=command, worker_id=self.id_on_server, 
                    states_id=[utils.Sensor.L_01.value, utils.Sensor.L_02.value, utils.Sensor.AC.value, utils.Sensor.PR.value, utils.Sensor.AL_BZ.value],
                    values = [0, 0, 0, 0, 0]))
        elif (json_msg["type"] ==  "trigger_alarm"):
            if json_msg["value"] == 0:
                self.turn_on_off_outputs([utils.Sensor.AL_BZ.value], 0)
            self.states[utils.Sensor.Alarme.value] = json_msg["value"]
            self.server.send(utils.encode_message(type="confirmation", success=True, worker_id=self.id_on_server, states_id=[utils.Sensor.Alarme.value], values = [json_msg["value"]]))
        elif (json_msg["type"] ==  "states_backup"):
            self.states = json_msg["states"]
        else:
            pass