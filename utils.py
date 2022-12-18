import json
from enum import Enum

def get_obj_by_element(object_list: list, element_key: str, element_to_find):
    for obj in object_list:
        if obj[element_key] == element_to_find:
            return obj
    return None

def find_worker_by_conn(workers: list, conn):
    for worker in workers:
        if worker.conn == conn:
            return worker
    return None

def find_worker_by_id(workers: list, id):
    for worker in workers:
        if worker.id == id:
            return worker
    return None

class Steps(Enum):
    MENU = "MENU"
    TRIGGER = "TRIGGER"
    COMMAND = "COMMAND"

class Sensor(Enum):
    L_01 = "L_01"
    L_02 = "L_02"
    AC = "AC"
    PR = "PR"
    AL_BZ = "AL_BZ"
    SPres = "SPres"
    SFum = "SFum"
    SJan = "SJan"
    SPor = "SPor"
    SC_IN = "SC_IN"
    SC_OUT = "SC_OUT"
    Temperature = "Temperature"
    Humidity = "Humidity"
    Alarme = "Alarme"

class SensorName(Enum):
    L_01 = "Lâmpada 01"
    L_02 = "Lâmpada 02"
    AC = "Ar-Condicionado"
    PR = "Projetor Multimidia"
    AL_BZ = "Sirene do Alarme"
    SPres = "Sensor de Presença"
    SFum = "Sensor de Fumaça"
    SJan = "Sensor de Janela"
    SPor = "Sensor de Porta"
    SC_IN = "Sensor de Contagem de Pessoas Entrada"
    SC_OUT = "Sensor de Contagem de Pessoas Saída"
    Temperature = "Temperatura"
    Humidity = "Umidade"
    Alarme = "Sistema de Alarme"

def show_state(state):
    people_inside = state[Sensor.SC_IN.value] - state[Sensor.SC_OUT.value]
    for key, value in state.items():
        if key in [Sensor.SC_IN.value, Sensor.SC_OUT.value, Sensor.Temperature.value, Sensor.Humidity.value]:
            print(f"\t{SensorName[key].value}: {value}")
        else:
            print(f"\t{SensorName[key].value}: {'Desligado(a)' if value == 0 else 'Ligado(a)'}")
    print(f"\tTotal de pessoas na sala: {people_inside} pessoas")
    print()

def get_initial_state():
    return {
        Sensor.L_01.value: 0,
        Sensor.L_02.value: 0,
        Sensor.AC.value: 0,
        Sensor.PR.value: 0,
        Sensor.AL_BZ.value: 0,
        Sensor.SPres.value: 0,
        Sensor.SFum.value: 0,
        Sensor.SJan.value: 0,
        Sensor.SPor.value: 0,
        Sensor.SC_IN.value: 0,
        Sensor.SC_OUT.value: 0,
        Sensor.Temperature.value: 0,
        Sensor.Humidity.value: 0
    }

def encode_message(**data):
    encoded_json = {}
    for key, value in data.items():
        encoded_json[key] = value
    return bytes(json.dumps(encoded_json), encoding='utf-8')

def is_option_valid(possible_option, show_possible_option, option):
    is_valid = True
    if not(option in possible_option):
        print("Opcao invalida, digite novamente, opcoes disponiveis:", *show_possible_option, "", sep="\n")
        is_valid = False
    return is_valid

def decode_recv_message(data):
    data_list = []
    while data.find('type', 0, 10) != -1:
        end_index = data.find('type', 11, len(data))
        end_index = end_index - 2 if end_index != -1 else len(data)
        data_list.append(data[0:end_index])
        data = data[end_index:len(data)]
    return data_list
