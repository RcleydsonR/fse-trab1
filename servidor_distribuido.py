import socket
import select
import sys
import json
from typing import TextIO
from datetime import datetime
import utils
# import RPi.GPIO as GPIO
# import Adafruit_DHT
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

        self.inputs = [self.server, sys.stdin]
        self.running = False

        # initialize gpio, ports and related states
        self.initial_state()

    def initial_state(self):
        # GPIO.setmode(GPIO.BCM)
        self.light_1 = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.L_01.value)["gpio"],
        self.light_2 = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.L_02.value)["gpio"],
        self.air_conditioning = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.AC.value)["gpio"]
        self.projector = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.PR.value)["gpio"]
        self.alarm = utils.get_obj_by_element(self.config_data["outputs"], 'id', utils.Sensor.AL_BZ.value)["gpio"]
        self.presence_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SPres.value)["gpio"]
        self.smoke_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SFum.value)["gpio"]
        self.window_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SJan.value)["gpio"]
        self.door_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SPor.value)["gpio"]
        self.entry_people_counting_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SC_IN.value)["gpio"]
        self.exit_people_counting_sensor = utils.get_obj_by_element(self.config_data["inputs"], 'id', utils.Sensor.SC_OUT.value)["gpio"]
        self.temperature_sensor = self.config_data["sensor_temperatura"]["gpio"]
        self.states = utils.get_initial_state()
        self.entry = 0

        # self.input_sensors = {
        #     self.presence_sensor: {"name": utils.Sensor.SPres.value, "callback_func": self._presence_sensor_callback},
        #     self.smoke_sensor: {"name": utils.Sensor.SFum.value, "callback_func": self._smoke_sensor_callback},
        #     self.window_sensor: {"name": utils.Sensor.SJan.value, "callback_func": self._window_sensor_callback},
        #     self.door_sensor: {"name": utils.Sensor.SPor.value, "callback_func": self._door_sensor_callback},
        #     self.entry_people_counting_sensor: {"name": utils.Sensor.SC_IN.value, "callback_func": self._entry_sensor_callback},
        #     self.exit_people_counting_sensor : {"name": utils.Sensor.SC_OUT.value, "callback_func": self._exit_sensor_callback},
        # }

    # def turn_on_off_projector(self):
    #     GPIO.setup(self.projector, GPIO.OUT)
    #     for _ in range(20):
    #         GPIO.output(self.projector, GPIO.HIGH)
    #         sleep(0.5)
    #         GPIO.output(self.projector, GPIO.LOW)
    #         sleep(0.5)

    # def verifyTemperature(self):
    #     while True:
    #         humidity, temperature = Adafruit_DHT.read_retry(22, self.temperature_sensor)
    #         if humidity is not None and temperature is not None:
    #             self.states["Temperature"] = temperature
    #             self.states["Humidity"] = humidity
    #         sleep(2)

    # def apply_sensor_transition(self, sensor):
    #     self.states[self.input_sensors[sensor]["name"]] = 1 if self.states[self.input_sensors[sensor]["name"]] == 0 else 0

    # def restart_sensor_event_detection(self, sensor, callback_func):
    #     GPIO.remove_event_detect(sensor)
    #     GPIO.add_event_detect(sensor, GPIO.RISING, callback=callback_func, bouncetime=200)

    # def _presence_sensor_callback(self, sensor):
    #     self.apply_sensor_transition(sensor)
    #     self.restart_sensor_event_detection(sensor, self._presence_sensor_callback)

    # def _smoke_sensor_callback(self, sensor):
    #     self.apply_sensor_transition(sensor)
    #     self.restart_sensor_event_detection(sensor, self._smoke_sensor_callback)

    # def _window_sensor_callback(self, sensor):
    #     self.apply_sensor_transition(sensor)
    #     self.restart_sensor_event_detection(sensor, self._window_sensor_callback)

    # def _door_sensor_callback(self, sensor):
    #     self.apply_sensor_transition(sensor)
    #     self.restart_sensor_event_detection(sensor, self._door_sensor_callback)

    # def _entry_sensor_callback(self, sensor):
    #     print("entrei: ", sensor)
    #     self.states[utils.Sensor.SC_IN.value] = 1
    #     self.entry += 1
    #     print(self.entry)
    #     self.restart_sensor_event_detection(sensor, self._entry_sensor_callback)

    # def _exit_sensor_callback(self, sensor):
    #     self.states[self.input_sensors[sensor]["name"]] += 1
    #     self.restart_sensor_event_detection(sensor, self._exit_sensor_callback)

    # def input_proc(self):
    #     for sensor in self.input_sensors:
    #         GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #         GPIO.add_event_detect(sensor, GPIO.RISING, callback=self.input_sensors[sensor]["callback_func"], bouncetime=200)

    #     while True:
    #         sleep(3)
    #         [print(key, value) for key, value in self.states.items()]
    #         print("------------------------------------------\n\n")

    # def verifyEntrance(self):
    #     GPIO.setup(self.entry_people_counting_sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #     GPIO.add_event_detect(self.entry_people_counting_sensor, GPIO.RISING, callback=self._entry_button_callback, bouncetime=200)
    #     while True:
    #         sleep(1)

    # def verifyExit(self):
    #     GPIO.setup(self.exit_people_counting_sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
    #     GPIO.add_event_detect(self.exit_people_counting_sensor, GPIO.RISING, callback=self._exit_button_callback, bouncetime=200)
    #     while True:
    #         sleep(1)

    def start(self):
        print(f"Conectado ao servidor central.\nIP: {self.config_data['ip_servidor_central']}\nPORT: {self.config_data['porta_servidor_central']}")
        self.running = True
        self._run()

    def exit(self, message):
        print(message)
        self.inputs = []
        self.running = False
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
                self.server.send(utils.encode_message(type="worker_identify", id=self.id_on_server))
            except Exception as e:
                sleep(2)
                continue
            
            self.inputs = [sys.stdin, self.server]
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
        else:
            message = input()
            if message == "1":
                self.server.send(utils.encode_message(type="states_refresh", worker_id=self.id_on_server, states=self.states))
                

    def _decode_server_message(self, json_msg):
        if(json_msg["type"] == "invalid_id"):
            self.exit("O ip e nome da sala que estao no arquivo de configuracao json ja estao em uso")
        if (json_msg["type"] == "trigger"):
            print("triggered")
            # self.trigger...
            state_id = json_msg["state_id"]
            self.states[state_id] = json_msg["value"]
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=[state_id], values = [json_msg["value"]]))
        elif (json_msg["type"] == "turn_on_all_lights"):
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=[utils.Sensor.L_01.value, utils.Sensor.L_02.value], values = [1, 1]))
        elif (json_msg["type"] == "turn_off_all_lights"):
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=[utils.Sensor.L_01.value, utils.Sensor.L_02.value], values = [0, 0]))
        elif (json_msg["type"] == "turn_off_all"):
            self.server.send(
                utils.encode_message(
                    type="confirmation", worker_id=self.id_on_server, 
                    states_id=[utils.Sensor.L_01.value, utils.Sensor.L_02.value, utils.Sensor.AC.value, utils.Sensor.PR.value, utils.Sensor.AL_BZ.value],
                    values = [0, 0, 0, 0, 0]))
        elif (json_msg["type"] ==  "states_backup"):
            self.states = json_msg["states"]
        else:
            pass