import socket
import select
import sys
import json
from typing import TextIO
from datetime import datetime
import utils
# import RPi.GPIO as GPIO
# from pigpio_dht import DHT22
# import Adafruit_DHT
from time import sleep
import threading

class Worker():
    server: socket.socket
    ip: str
    port: int
    inputs: 'list[socket.socket | TextIO]'
    running: bool

    def __init__(self, ip, port, config):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((ip, port))
        self.inputs = [sys.stdin, self.server]
        self.running = False

        # Config port
        config_file = open(config)
        config_data = json.load(config_file)

        # GPIO.setmode(GPIO.BCM)
        self.light_1 = utils.get_obj_by_id(config_data['outputs'], 'L_01')['gpio'],
        self.light_2 = utils.get_obj_by_id(config_data['outputs'], 'L_02')['gpio'],
        self.air_conditioning = utils.get_obj_by_id(config_data['outputs'], 'AC')['gpio']
        self.projector = utils.get_obj_by_id(config_data['outputs'], 'PR')['gpio']
        self.alarm = utils.get_obj_by_id(config_data['outputs'], 'AL_BZ')['gpio']
        self.presence_sensor = utils.get_obj_by_id(config_data['inputs'], 'SPres')['gpio']
        self.smoke_sensor = utils.get_obj_by_id(config_data['inputs'], 'SFum')['gpio']
        self.window_sensor = utils.get_obj_by_id(config_data['inputs'], 'SJan')['gpio']
        self.door_sensor = utils.get_obj_by_id(config_data['inputs'], 'SPor')['gpio']
        self.entry_people_counting_sensor = utils.get_obj_by_id(config_data['inputs'], 'SC_IN')['gpio']
        self.exit_people_counting_sensor = utils.get_obj_by_id(config_data['inputs'], 'SC_OUT')['gpio']
        self.temperature_sensor = config_data['sensor_temperatura']['gpio']
        self.states = {}
        self.entry = 0

        self.initial_state()

    def initial_state(self):
        # 0 -> LOW, CLOSED
        # 1 -> HIGH, OPENED

        self.states = {
            "L_01": 0,
            "L_02": 0,
            "AC": 0,
            "PR": 0,
            "AL_BZ": 0,
            "SPres": 0,
            "SFum": 0,
            "SJan": 0,
            "SPor": 0,
            "SC_IN": 0,
            "SC_OUT": 0,
            "Temperature": 0,
            "Humidity": 0
        }

        # self.input_sensors = {
        #     self.presence_sensor: {'name': 'SPres', 'callback_func': self._presence_sensor_callback},
        #     self.smoke_sensor: {'name': 'SFum', 'callback_func': self._smoke_sensor_callback},
        #     self.window_sensor: {'name': 'SJan', 'callback_func': self._window_sensor_callback},
        #     self.door_sensor: {'name': 'SPor', 'callback_func': self._door_sensor_callback},
        #     self.entry_people_counting_sensor: {'name': 'SC_IN', 'callback_func': self._entry_sensor_callback},
        #     self.exit_people_counting_sensor : {'name': 'SC_OUT', 'callback_func': self._exit_sensor_callback},
        # }


    def start(self):
        print("Conexao concluida. Digite --HELP para ajuda.\n")
        self.running = True
        self._run()

    def close(self):
        self._exit_server()

    def _run(self):
        while self.running:
            inputs, _, _ = select.select(self.inputs,[],[])

            for input in inputs:
                self._handle_input(input)

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
    #             self.states['Temperature'] = temperature
    #             self.states['Humidity'] = humidity
    #         sleep(2)

    # def apply_sensor_transition(self, sensor):
    #     self.states[self.input_sensors[sensor]['name']] = 1 if self.states[self.input_sensors[sensor]['name']] == 0 else 0

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
    #     self.states['SC_IN'] = 1
    #     self.entry += 1
    #     print(self.entry)
    #     self.restart_sensor_event_detection(sensor, self._entry_sensor_callback)

    # def _exit_sensor_callback(self, sensor):
    #     self.states[self.input_sensors[sensor]['name']] += 1
    #     self.restart_sensor_event_detection(sensor, self._exit_sensor_callback)

    # def input_proc(self):
    #     for sensor in self.input_sensors:
    #         GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #         GPIO.add_event_detect(sensor, GPIO.RISING, callback=self.input_sensors[sensor]['callback_func'], bouncetime=200)

    #     while True:
    #         sleep(3)
    #         [print(key, value) for key, value in self.states.items()]
    #         print('------------------------------------------\n\n')

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

    def _handle_input(self, inputs):
        if inputs == self.server:
            data = inputs.recv(1024).decode('utf-8')
            json_data = json.loads(data)
            if(json_data['type'] == 'welcome'):
                self.id_on_server = json_data['message']
            print(json_data)
        else:
            message = input()
            json_message = {
                'id': self.id_on_server,
                'message': message,
                'time': str(datetime.now())
            }
            data = json.dumps(json_message)
            self.server.send(bytes(data, encoding='utf-8'))

    def _exit_server(self):
        print("Saindo do servidor...")
        self.inputs.remove(self.server)
        self.server.close()
        self.running = False
