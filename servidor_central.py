import socket
import select
import sys
import json
import menu_options
import utils
from typing import TextIO
from time import sleep
import threading
from datetime import datetime

class Server():
    server: socket.socket
    ip: str
    port: int
    max_connections: int
    inputs: "list[socket.socket | TextIO]"
    workers: "list[ServerWorker]"

    def __init__(self, ip, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.ip = ip
        self.port = port
        self.inputs = [self.server, sys.stdin]
        self.workers = []
        self.states = {}
        self.waiting_response = 0
        self.step = utils.Steps.MENU.value
        self.selected_worker = -1
        self.states = {
            utils.Sensor.Alarme.value: 0,
            utils.Sensor.Alarme_Incendio.value: 0
        }
        self.trigger_confirmation_response = 0
        self.trigger_confirmation_error = False
        self.csv_data = []

    def start(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen()
        self._run()

    def close(self):
        print("Fechando conexões")
        for worker in self.workers:
            worker.conn.close()
        self.server.close()
        self.inputs = []
        return

    def show_menu(self):
        self.step = utils.Steps.MENU.value
        print("", "------------------------------------------------", "Voce esta no menu principal, o que deseja fazer:", *menu_options.ask_main_menu(), "", sep="\n")

    def _handle_stdin(self, option):
        try:
            opt = int(option)
        except ValueError:
            print("Por favor, digite um valor inteiro")
            return
        
        if self.step == utils.Steps.MENU.value:
            self._menu(opt)
        elif self.step == utils.Steps.TRIGGER.value:
            self._define_trigger(opt)
        else:
            self._define_command(opt)


    def _menu(self, option):
        if len(self.workers) == 0:
            print("Aguardando algum servidor distribuido se conectar\n")
            return

        possible_options = [i for i in range(len(menu_options.ask_main_menu()))]

        if utils.is_option_valid(possible_options, menu_options.ask_main_menu(), option):
            self._handle_main_menu_opt(option)

    def _handle_main_menu_opt(self, option):
        if option == 0:
            self.close()
        elif option == 1:
            self._show_states()
        elif option == 2:
            print("Qual o servidor ou opcao:", *menu_options.ask_trigger(self.workers, self.states[utils.Sensor.Alarme.value], self.states[utils.Sensor.Alarme_Incendio.value]), "", sep="\n")
            self.step = utils.Steps.TRIGGER.value
            pass
        else:
            csv_header = ['Comando', 'Ambiente', 'Data do comando', 'Estado do Comando']
            file_name = utils.generate_csv_file(csv_header, self.csv_data)  
            print(f"Arquivo csv disponibilizado com sucesso em: {file_name}")
            self.show_menu() 
    
    def _show_states(self):
        people_total = 0
        for worker in self.workers:
            print(f"\n{worker.name}:")
            utils.show_state(self.states[worker.id])
            people_total += self.states[worker.id][utils.Sensor.SC_IN.value] - self.states[worker.id][utils.Sensor.SC_OUT.value]
        print(f"Total de pessoas no prédio: {people_total} pessoas")
        print(f"Sistema de alarme do predio: {'Desligado' if self.states[utils.Sensor.Alarme.value] == 0 else 'Ligado'}")
        print(f"Sistema de alarme de incendio do predio: {'Desligado' if self.states[utils.Sensor.Alarme_Incendio.value] == 0 else 'Ligado'}")
        self.show_menu()        

    def _define_trigger(self, option):
        workers_size = len(self.workers)
        possible_options = [0, *[i + 1 for i in range(workers_size + 4)]]

        if not utils.is_option_valid(possible_options, menu_options.ask_trigger(self.workers, self.states[utils.Sensor.Alarme.value], self.states[utils.Sensor.Alarme_Incendio.value]), option):
            return -1

        if(option == 0):
            print()
            self.show_menu()
            return
        
        if option <= workers_size:
            self.selected_worker = self.workers[option - 1]
            print(f"O que deseja fazer na(o) {self.selected_worker.name}:", *menu_options.ask_command(self.states[self.selected_worker.id]), "", sep="\n")
            self.step = utils.Steps.COMMAND.value
            return
        elif option == workers_size + 1:
            self.csv_data.append(["Ligar todas as lampadas", "Todos", str(datetime.now())])
            self._send_all_workers_command(utils.encode_message(type="turn_on_all_lights"))
        elif option == workers_size + 2:
            self.csv_data.append(["Desligar todas as cargas", "Todos", str(datetime.now())])
            self._send_all_workers_command(utils.encode_message(type="turn_off_all"))
        elif option == workers_size + 3:
            value_to_trigger = 0 if self.states[utils.Sensor.Alarme.value] == 1 else 1
            self.csv_data.append([f"{'Ligar' if value_to_trigger == 1 else 'Desligar'} o sistema de alarme", "Todos", str(datetime.now())])
            self.trigger_confirmation_response = len(self.workers)
            self._send_all_workers_command(utils.encode_message(type="verify_trigger_alarm", value=value_to_trigger))
        elif option == workers_size + 4:
            self.csv_data.append(["Ligar todas as lampadas", "Todos", str(datetime.now())])
            value_to_trigger = 0 if self.states[utils.Sensor.Alarme_Incendio.value] == 1 else 1
            self.csv_data.append([f"{'Ligar' if value_to_trigger == 1 else 'Desligar'} o alarme de incendio", "Todos", str(datetime.now())])
            self.states[utils.Sensor.Alarme_Incendio.value] = value_to_trigger
            self._send_all_workers_command(utils.encode_message(type="trigger_fire_alarm", value=value_to_trigger))
        self.waiting_response = len(self.workers)
        threading.Thread(target=self._load_animation).start()

    def _define_command(self, option):
        ask_command = menu_options.ask_command(self.states[self.selected_worker.id])
        possible_options = [*[i for i in range(len(ask_command))]]
        if utils.is_option_valid(possible_options, ask_command, option):
            self._handle_triggered_action(self.selected_worker, option)
    
    def _handle_triggered_action(self, worker, option):
        if option == 0:
            print("Qual o servidor ou opcao:", *menu_options.ask_trigger(self.workers, self.states[utils.Sensor.Alarme.value], self.states[utils.Sensor.Alarme_Incendio.value]), "", sep="\n")
            self.step = utils.Steps.TRIGGER.value
            return
        elif option == 1:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.L_01.value] == 1 else 1
            self.csv_data.append([f"{'Ligar' if value_to_trigger == 1 else 'Desligar'} a Lampada 1", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.L_01.value, value=value_to_trigger))
        elif option == 2:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.L_02.value] == 1 else 1
            self.csv_data.append([f"{'Ligar' if value_to_trigger == 1 else 'Desligar'} a Lampada 2", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.L_02.value, value=value_to_trigger))
        elif option == 3:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.AC.value] == 1 else 1
            self.csv_data.append([f"{'Ligar' if value_to_trigger == 1 else 'Desligar'} o Ar Condicionado", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.AC.value, value=value_to_trigger))
        elif option == 4:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.PR.value] == 1 else 1
            self.csv_data.append([f"{'Ligar' if value_to_trigger == 1 else 'Desligar'} o Projetor", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.PR.value, value=value_to_trigger))
        elif option == 5:
            self.csv_data.append(["Ligar todas as lampadas", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="turn_on_all_lights"))
        elif option == 6:
            self.csv_data.append(["Desligar todas as lampadas", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="turn_off_all_lights"))
        elif option == 7:
            self.csv_data.append(["Desligar todas as cargas", worker.name, str(datetime.now())])
            worker.conn.sendall(utils.encode_message(type="turn_off_all"))
        
        self.waiting_response = 1
        threading.Thread(target=self._load_animation).start()


    def _load_animation(self):
        timeout = 0
        breaked_by_timeout = False
        loading_steps = ['|', '/', '-', '\\']
        self.step = utils.Steps.MENU.value

        while self.waiting_response != 0:
            for loading_step in loading_steps:
                print(f"\rAguardando confirmacao do comando {loading_step}", end=" ")
                sleep(0.25)
                timeout += 1
                if self.trigger_confirmation_error:
                    self.waiting_response = 0
                    break
                if self.waiting_response != 0:
                    break
                if timeout == 20:
                    breaked_by_timeout = True
                    self.waiting_response = 0
                    break
        
        if self.trigger_confirmation_error == True:
            self.csv_data[len(self.csv_data) - 1].append("Falha")
            print(f"\rComando nao confirmado. Algum sensor de (presenca, abertura de porta ou janela) esta ativado.", u'\u2717', end=" ")
        elif breaked_by_timeout:
            self.csv_data[len(self.csv_data) - 1].append("Falha por tempo de espera")
            print(f"\rComando nao confirmado (Timeout exceed) ", u'\u2717', end=" ")
        else:
            self.csv_data[len(self.csv_data) - 1].append("Sucesso")
            print(f"\rComando confirmado com sucesso ", u'\u2713', "   ", end=" ")
        
        self.trigger_confirmation_error = False
        self.show_menu()
        return

    def _send_all_workers_command(self, encoded_command):
        for worker in self.workers:
            worker.conn.sendall(bytes(encoded_command))
        
    def _run(self):
        print("Aguardando em ", (self.ip, self.port))

        while self.inputs:
            readable, _, exceptional = select.select(
                self.inputs, [] , []
            )

            for r in readable:
                self._handle_readable(r)

            for e in exceptional:
                self._handle_exceptions(e)

    def _handle_readable(self, inputs: socket.socket):
        if inputs is self.server:
            self._manage_connection(inputs)
        elif isinstance(inputs, socket.socket):
            data = inputs.recv(2048).decode("utf-8")
            if data == "":
                self._close_connection(inputs)
                return
            else:
                for json_decodable in utils.decode_recv_message(data):
                    json_data = json.loads(json_decodable)
                    self._decode_worker_message(json_data, inputs)
        else:
            option = input()
            if self.waiting_response != 0:
                pass
            else:
                self._handle_stdin(option)

    def _handle_exceptions(self, exceptions: socket.socket):
        self.inputs.remove(exceptions)
        worker_to_remove = utils.find_worker_by_conn(self.workers, exceptions)
        if worker_to_remove:
            self.workers.remove(worker_to_remove)
        exceptions.close()

    def _manage_connection(self, s):
        connection, _ = s.accept()
        connection.setblocking(0)

        self.inputs.append(connection)

    def _close_connection(self, conn):
        print(conn, "Desconectado")

        self.inputs.remove(conn)
        worker_to_remove = utils.find_worker_by_conn(self.workers, conn)
        if worker_to_remove:
            self.workers.remove(worker_to_remove)
        conn.close()

    def _decode_worker_message(self, json_msg, conn: socket.socket):
        if (json_msg["type"] == "worker_identify"):
            worker_id = json_msg["id"]

            # Verify if id is already connected
            if utils.find_worker_by_id(self.workers, worker_id):
                conn.sendall(utils.encode_message(type="invalid_id", message="Already in use"))
                self.inputs.remove(conn)
                conn.close()
                return

            self.workers.append(ServerWorker({"id": worker_id, "conn": conn, "name": worker_id.split(':')[1]}))
            if(len(self.workers) == 1): # First connection on the server
                print("O primeiro servidor distribuido foi conectado.\n")
                self.show_menu()

            if worker_id in self.states:
                conn.sendall(utils.encode_message(type="states_backup", states=self.states[worker_id]))
            else:
                self.states[worker_id] = json_msg["states"] if "states" in json_msg else utils.get_initial_state()

        elif (json_msg["type"] == "confirmation"):
            worker_id = json_msg["worker_id"]
            #print(f"\nO comando foi executado com {'sucesso' if json_msg['success'] else 'falha'} na {worker_id.split(':')[1]}.")
            for index, state in enumerate(list(json_msg["states_id"])):
                self.states[worker_id][state] = list(json_msg["values"])[index]
            self.waiting_response -= 1

        elif (json_msg["type"] == "confirmation_trigger_alarm"):
            worker_id = json_msg["worker_id"]
            if json_msg['success']:
                self.trigger_confirmation_response -= 1
            else:
                self.trigger_confirmation_error = True
            if self.trigger_confirmation_response == 0 and self.trigger_confirmation_error == False:
                self._send_all_workers_command(utils.encode_message(type="trigger_alarm", value=json_msg['value']))
                self.states[utils.Sensor.Alarme.value] = json_msg['value']

        elif (json_msg["type"] == "states_update"):
            worker_id = json_msg["worker_id"]
            for index, state in enumerate(list(json_msg["states_id"])):
                self.states[worker_id][state] = list(json_msg["values"])[index]
                # if state in [utils.Sensor.SPres.value, utils.Sensor.SPor.value, utils.Sensor.SJan.value] and self.states[utils.Sensor.Alarme.value] == 1:
                #     worker = utils.find_worker_by_id(self.workers, worker_id)
                #     worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.AL_BZ.value, value=1))
                # if state == utils.Sensor.Alarme_Incendio.value and self.states[utils.Sensor.Alarme_Incendio.value] == 1:
                #     worker = utils.find_worker_by_id(self.workers, worker_id)
                #     worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.AL_BZ.value, value=1))
        else:
            print(json_msg)

class ServerWorker(object):
    def __init__(self, *initial_data, **kwargs):
        # id, conn, name
        for dict in initial_data:
            for key in dict:
                setattr(self, key, dict[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])