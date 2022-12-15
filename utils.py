import json
from enum import Enum

def get_obj_by_element(object_list: list, element_key: str, element_to_find):
    return next(
        (obj for obj in object_list if obj[element_key] == element_to_find),
        None
    )

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

def show_state(state):
    show_mode = 0
    people_inside = state[Sensor.SC_IN.value] - state[Sensor.SC_OUT.value]
    for key, value in state.items():
        if show_mode == 0:
            print(f"\t{SensorName[key].value}: {'Desligado(a)' if value == 0 else 'Ligado(a)'}")
            if key == Sensor.SPor.value:
                show_mode = 1
        else:
            print(f"\t{SensorName[key].value}: {value}")
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
        Sensor.SC_IN.value: 13,
        Sensor.SC_OUT.value: 2,
        Sensor.Temperature.value: 0,
        Sensor.Humidity.value: 0
    }

def encode_message(**data):
    encoded_json = {}
    for key, value in data.items():
        encoded_json[key] = value
    return bytes(json.dumps(encoded_json), encoding='utf-8')

def get_valid_option(possible_option, show_possible_option):
    option = -1
    while not(option in possible_option):
        try:
            option = int(input())
        except ValueError:
            print("Por favor, digite um valor inteiro")
        if option in possible_option:
            break
        print("Opcao invalida, digite novamente, opcoes disponiveis:", *show_possible_option, "", sep="\n")
    return option