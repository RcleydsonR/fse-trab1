import socket
import select
import sys
import json
import menu_options
import utils
from typing import TextIO
from time import sleep
import threading

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
            print("Qual o servidor ou opcao:", *menu_options.ask_worker(self.workers), "", sep="\n")
            self.step = utils.Steps.TRIGGER.value
            pass
        else:
            pass
    
    def _show_states(self):
        people_total = 0
        for worker in self.workers:
            print(f"\n{worker.name}:")
            utils.show_state(self.states[worker.id])
            people_total += self.states[worker.id][utils.Sensor.SC_IN.value] - self.states[worker.id][utils.Sensor.SC_OUT.value]
        print(f"Total de pessoas no prédio: {people_total} pessoas")
        self.show_menu()        

    def _define_trigger(self, option):
        workers_size = len(self.workers)
        possible_options = [0, *[i + 1 for i in range(workers_size + 4)]]

        if not utils.is_option_valid(possible_options, menu_options.ask_worker(self.workers), option):
            return -1

        if(option == 0):
            print()
            self.show_menu()
            self.step = utils.Steps.MENU.value
            return
        
        if option <= workers_size:
            self.selected_worker = self.workers[option - 1]
            print("O que deseja fazer:", *menu_options.ask_command(self.states[self.selected_worker.id]), "", sep="\n")
            self.step = utils.Steps.COMMAND.value
        elif option == workers_size + 1:
            self._send_all_workers_command(utils.encode_message(type="turn_on_all_lights"))
        elif option == workers_size + 2:
            self._send_all_workers_command(utils.encode_message(type="turn_off_all"))
        elif option == workers_size + 3:
            self._send_all_workers_command(utils.encode_message(type="trigger_alarm", value=1))
        else:
            self._send_all_workers_command(utils.encode_message(type="trigger_alarm", value=0))

    def _define_command(self, option):
        ask_command = menu_options.ask_command(self.states[self.selected_worker.id])
        possible_options = [*[i for i in range(len(ask_command))]]
        if utils.is_option_valid(possible_options, ask_command, option):
            self._handle_triggered_action(self.selected_worker, option)
    
    def _handle_triggered_action(self, worker, option):
        if option == 0:
            print("Qual o servidor ou opcao:", *menu_options.ask_worker(self.workers), "", sep="\n")
            self.step = utils.Steps.TRIGGER.value
            return
        elif option == 1:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.L_01.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.L_01.value, value=value_to_trigger))
        elif option == 2:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.L_02.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.L_02.value, value=value_to_trigger))
        elif option == 3:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.AC.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.AC.value, value=value_to_trigger))
        elif option == 4:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.PR.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.PR.value, value=value_to_trigger))
        elif option == 5:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.AL_BZ.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.AL_BZ.value, value=value_to_trigger))
        elif option == 6:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.SFum.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_output", state_id=utils.Sensor.SFum.value, value=value_to_trigger))
        elif option == 7:
            value_to_trigger = 0 if self.states[worker.id][utils.Sensor.Alarme.value] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger_alarm", value=value_to_trigger))
        elif option == 8:
            worker.conn.sendall(utils.encode_message(type="turn_on_all_lights"))
        elif option == 9:
            worker.conn.sendall(utils.encode_message(type="turn_off_all_lights"))
        elif option == 10:
            worker.conn.sendall(utils.encode_message(type="turn_off_all"))
        threading.Thread(target=self._load_animation).start()


    def _load_animation(self):
        timeout = 0
        breaked_by_timeout = False
        loading_steps = ['|', '/', '-', '\\']
        self.step = utils.Steps.MENU.value

        while self.waiting_response != 0:
            for loading_step in loading_steps:
                if self.waiting_response != 0:
                    break
                if timeout == 20:
                    breaked_by_timeout = True
                    self.waiting_response = 0
                    break
                print(f"\rAguardando confirmacao do comando {loading_step}", end=" ")
                sleep(0.25)
                timeout += 1
        
        if breaked_by_timeout:
            print(f"\rComando nao confirmado (Timeout exceed) ", u'\u2717', end=" ")
        else:
            print(f"\rComando confirmado com sucesso ", u'\u2713', "   ", end=" ")
        
        self.show_menu()
        return

    def _send_all_workers_command(self, encoded_command):
        for worker in self.workers:
            worker.conn.sendall(bytes(encoded_command))
        self.waiting_response = len(self.workers)
        threading.Thread(target=self._load_animation).start()

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
            print(f"O comando foi executado com {'sucesso' if json_msg['success'] else 'falha'} na {worker_id.split(':')[1]}.")
            for index, state in enumerate(list(json_msg["states_id"])):
                self.states[worker_id][state] = list(json_msg["values"])[index]
            self.waiting_response -= 1
        elif (json_msg["type"] == "states_update"):
            worker_id = json_msg["worker_id"]
            for index, state in enumerate(list(json_msg["states_id"])):
                self.states[worker_id][state] = list(json_msg["values"])[index]
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