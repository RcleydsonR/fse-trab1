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
        print("", "------------------------------------------------", "Bem vindo ao menu principal, o que deseja fazer:", *menu_options.ask_main_menu(), "", sep="\n")

    def menu(self):
        if len(self.workers) == 0:
            input()
            print("Aguardando algum servidor distribuido se conectar\n")
            return

        possible_options = [i for i in range(len(menu_options.ask_main_menu()))]
        option = utils.get_valid_option(possible_options, menu_options.ask_main_menu())

        self._handle_main_menu_opt(option)

    def _handle_main_menu_opt(self, option):
        if option == 0:
            self.close()
        elif option == 1:
            print(self.states)
        elif option == 2:
            self._define_worker()
            pass
        else:
            pass

    def _define_worker(self):
        workers_size = len(self.workers)
        print("Qual o servidor ou opcao:", *menu_options.ask_worker(self.workers), "", sep="\n")
        possible_options = [0, *[i + 1 for i in range(workers_size + 2)]]

        option = utils.get_valid_option(possible_options, menu_options.ask_worker(self.workers))

        if(option == 0):
            print()
            self.show_menu()
            return
        
        if option <= workers_size:
            self._define_trigger(self.workers[option - 1])
        elif option == workers_size + 1:
            self._send_all_workers_command(utils.encode_message(type="turn_on_all_lights"))
        else:
            self._send_all_workers_command(utils.encode_message(type="turn_off_all"))

    def _define_trigger(self, worker):
        ask_command = menu_options.ask_command(self.states[worker.id])
        print("O que deseja fazer:", *ask_command, "", sep="\n")
        possible_options = [*[i for i in range(len(ask_command))]]
        option = utils.get_valid_option(possible_options, ask_command)

        self._handle_triggered_action(worker, option)
        return
    
    def _handle_triggered_action(self, worker, option):
        if option == 0:
            return
        elif option == 1:
            value_to_trigger = 0 if self.states[worker.id]["L_01"] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger", state_id="L_01", value=value_to_trigger))
        elif option == 2:
            value_to_trigger = 0 if self.states[worker.id]["L_02"] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger", state_id="L_02", value=value_to_trigger))
        elif option == 3:
            value_to_trigger = 0 if self.states[worker.id]["AC"] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger", state_id="AC", value=value_to_trigger))
        elif option == 4:
            value_to_trigger = 0 if self.states[worker.id]["PR"] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger", state_id="PR", value=value_to_trigger))
        elif option == 5:
            value_to_trigger = 0 if self.states[worker.id]["AL_BZ"] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger", state_id="AL_BZ", value=value_to_trigger))
        elif option == 6:
            value_to_trigger = 0 if self.states[worker.id]["SFum"] == 1 else 1
            worker.conn.sendall(utils.encode_message(type="trigger", state_id="SFum", value=value_to_trigger))
        elif option == 7:
            worker.conn.sendall(utils.encode_message(type="turn_on_all_lights"))
        elif option == 8:
            worker.conn.sendall(utils.encode_message(type="turn_off_all_lights"))
        elif option == 9:
            worker.conn.sendall(utils.encode_message(type="turn_off_all"))
        self.waiting_response = 1
        threading.Thread(target=self._load_animation).start()


    def _load_animation(self):
        timeout = 0
        breaked_by_timeout = False
        steps = ['|', '/', '-', '\\']

        while self.waiting_response != 0:
            for step in steps:
                if self.waiting_response != 0:
                    break
                if timeout == 20:
                    breaked_by_timeout = True
                    self.waiting_response = 0
                    break
                print(f"\rAguardando confirmacao do comando {step}", end=" ")
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
                json_data = json.loads(data)
                self._decode_worker_message(json_data, inputs)
        else:
            if self.waiting_response != 0:
                input()
            else:
                self.menu()

    def _handle_exceptions(self, exceptions: socket.socket):
        self.inputs.remove(exceptions)
        if exceptions in self.workers:
            self.workers.remove(exceptions)
        exceptions.close()

    def _manage_connection(self, s):
        connection, _ = s.accept()
        connection.setblocking(0)

        self.inputs.append(connection)

    def _close_connection(self, conn):
        print(conn, "Desconectado")

        self.inputs.remove(conn)
        conn.close()

    def _decode_worker_message(self, json_msg, conn):
        if (json_msg["type"] == "worker_identify"):            
            worker_id = json_msg["id"]
            self.workers.append(ServerWorker({"id": worker_id, "conn": conn, "name": worker_id.split(':')[1]}))
            self.states[worker_id] = utils.get_initial_state()

            if(len(self.workers) == 1): # First connection on the server
                print("A primeira conexao com o servidor foi feita.\n")
                self.show_menu()
        elif (json_msg["type"] == "confirmation"):
            worker_id = json_msg["worker_id"]
            # self.turn_on_all_lights...
            for index, state in enumerate(list(json_msg["states_id"])):
                self.states[worker_id][state] = list(json_msg["values"])[index]
                #breakpoint()
            self.waiting_response -= 1
        else:
            print("mensagem desconhecida")

class ServerWorker(object):
    def __init__(self, *initial_data, **kwargs):
        for dict in initial_data:
            for key in dict:
                setattr(self, key, dict[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])