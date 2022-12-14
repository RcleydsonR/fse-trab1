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

        self.input = [self.server, sys.stdin]

        # initialize gpio, ports and related states
        self.initial_state()

    def initial_state(self):
        # GPIO.setmode(GPIO.BCM)
        self.light_1 = utils.get_obj_by_id(self.config_data["outputs"], "L_01")["gpio"],
        self.light_2 = utils.get_obj_by_id(self.config_data["outputs"], "L_02")["gpio"],
        self.air_conditioning = utils.get_obj_by_id(self.config_data["outputs"], "AC")["gpio"]
        self.projector = utils.get_obj_by_id(self.config_data["outputs"], "PR")["gpio"]
        self.alarm = utils.get_obj_by_id(self.config_data["outputs"], "AL_BZ")["gpio"]
        self.presence_sensor = utils.get_obj_by_id(self.config_data["inputs"], "SPres")["gpio"]
        self.smoke_sensor = utils.get_obj_by_id(self.config_data["inputs"], "SFum")["gpio"]
        self.window_sensor = utils.get_obj_by_id(self.config_data["inputs"], "SJan")["gpio"]
        self.door_sensor = utils.get_obj_by_id(self.config_data["inputs"], "SPor")["gpio"]
        self.entry_people_counting_sensor = utils.get_obj_by_id(self.config_data["inputs"], "SC_IN")["gpio"]
        self.exit_people_counting_sensor = utils.get_obj_by_id(self.config_data["inputs"], "SC_OUT")["gpio"]
        self.temperature_sensor = self.config_data["sensor_temperatura"]["gpio"]
        self.states = utils.get_initial_state()
        self.entry = 0

        # self.input_sensors = {
        #     self.presence_sensor: {"name": "SPres", "callback_func": self._presence_sensor_callback},
        #     self.smoke_sensor: {"name": "SFum", "callback_func": self._smoke_sensor_callback},
        #     self.window_sensor: {"name": "SJan", "callback_func": self._window_sensor_callback},
        #     self.door_sensor: {"name": "SPor", "callback_func": self._door_sensor_callback},
        #     self.entry_people_counting_sensor: {"name": "SC_IN", "callback_func": self._entry_sensor_callback},
        #     self.exit_people_counting_sensor : {"name": "SC_OUT", "callback_func": self._exit_sensor_callback},
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
    #     self.states["SC_IN"] = 1
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
        self._run()

    def exit(self, message):
        print(message)
        self.input.remove(self.server)
        self.input.remove(sys.stdin)
        self.server.close()

    def _run(self):
        while self.input:
            inputs, _, _ = select.select(self.input,[],[])

            for input in inputs:
                self._handle_input(input)

    def _handle_input(self, inputs):
        if inputs == self.server:
            data = inputs.recv(1024).decode("utf-8")
            if data == "":
                self.exit("servidor central foi desligado\nSaindo...")
                return
            json_data = json.loads(data)
            self._decode_server_message(json_data)
        else:
            message = input()
            if message == "1":
                self.server.send(utils.encode_message(type="states_refresh", worker_id=self.id_on_server, states=self.states, time= str(datetime.now())))
                

    def _decode_server_message(self, json_msg):
        if (json_msg["type"] == "trigger"):
            print("triggered")
            # self.trigger...
            state_id = json_msg["state_id"]
            self.states[state_id] = json_msg["value"]
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=[state_id], values = [json_msg["value"]]))
        elif (json_msg["type"] == "turn_on_all_lights"):
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=["L_01", "L_02"], values = [1, 1]))
        elif (json_msg["type"] == "turn_off_all_lights"):
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=["L_01", "L_02"], values = [0, 0]))
        elif (json_msg["type"] == "turn_off_all"):
            self.server.send(utils.encode_message(type="confirmation", worker_id=self.id_on_server, states_id=["L_01", "L_02", "AC", "PR", "AL_BZ"], values = [0, 0, 0, 0, 0]))
        else:
            print("mensagem desconhecida")