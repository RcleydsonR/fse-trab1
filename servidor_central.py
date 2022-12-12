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
    workers: "list[str | socket.socket]"

    def __init__(self, ip, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.ip = ip
        self.port = port
        self.inputs = [self.server, sys.stdin]
        self.workers = []
        self.states = {}
        self.waiting_response = False

    def start(self):
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen()
        self._run()

    def close(self):
        print("Fechando conexões")
        for worker in self.workers:
            worker.close()
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
        print("Qual o servidor ou opcao:", *menu_options.ask_worker(workers_size), "", sep="\n")
        possible_options = [0, *[i + 1 for i in range(workers_size + 2)]]

        option = utils.get_valid_option(possible_options, menu_options.ask_worker(workers_size))

        if(option == 0):
            print()
            self.show_menu()
            return
        
        if option <= workers_size:
            self._define_trigger(option - 1)
        elif option == workers_size + 1:
            self._send_all_workers_command(utils.encode_command(type="turn_on_all_lights"))
        else:
            self._send_all_workers_command(utils.encode_command(type="turn_off_all"))

    def _define_trigger(self, worker):
        ask_command = menu_options.ask_command(self.states[str(worker + 2)])
        print("O que deseja fazer:", *ask_command, "", sep="\n")
        possible_options = [*[i for i in range(len(ask_command))]]
        option = utils.get_valid_option(possible_options, ask_command)

        self._handle_triggered_action(worker, option)
        return
    
    def _handle_triggered_action(self, worker, option):
        if option == 0:
            return
        elif option == 1:
            value_to_trigger = 0 if self.states[str(worker + 2)]["L_01"] == 1 else 1
            self.workers[worker].sendall(bytes(utils.encode_command(type="trigger", output="L_01", value=value_to_trigger), encoding="utf-8"))
        elif option == 2:
            value_to_trigger = 0 if self.states[str(worker + 2)]["L_02"] == 1 else 1
            self.workers[worker].sendall(bytes(utils.encode_command(type="trigger", output="L_02", value=value_to_trigger), encoding="utf-8"))
        elif option == 3:
            value_to_trigger = 0 if self.states[str(worker + 2)]["AC"] == 1 else 1
            self.workers[worker].sendall(bytes(utils.encode_command(type="trigger", output="AC", value=value_to_trigger), encoding="utf-8"))
        elif option == 4:
            value_to_trigger = 0 if self.states[str(worker + 2)]["PR"] == 1 else 1
            self.workers[worker].sendall(bytes(utils.encode_command(type="trigger", output="PR", value=value_to_trigger), encoding="utf-8"))
        elif option == 5:
            value_to_trigger = 0 if self.states[str(worker + 2)]["AL_BZ"] == 1 else 1
            self.workers[worker].sendall(bytes(utils.encode_command(type="trigger", output="AL_BZ", value=value_to_trigger), encoding="utf-8"))
        elif option == 6:
            value_to_trigger = 0 if self.states[str(worker + 2)]["SFum"] == 1 else 1
            self.workers[worker].sendall(bytes(utils.encode_command(type="trigger", output="SFum", value=value_to_trigger), encoding="utf-8"))
        elif option == 7:
            self.workers[worker].sendall(bytes(utils.encode_command(type="turn_on_all_lights"), encoding="utf-8"))
        elif option == 8:
            self.workers[worker].sendall(bytes(utils.encode_command(type="turn_off_all_lights"), encoding="utf-8"))
        elif option == 9:
            self.workers[worker].sendall(bytes(utils.encode_command(type="turn_off_all"), encoding="utf-8"))
        self.waiting_response = True
        threading.Thread(target=self._load_animation).start()


    def _load_animation(self):
        while self.waiting_response:
            steps = ['|', '/', '-', '\\']
            for step in steps:
                if not(self.waiting_response):
                    break
                print(f"\rAguardando confirmacao do comando {step}", end=" ")
                sleep(0.25)
        self.show_menu()
        return

    def _send_all_workers_command(self, encoded_command):
        for worker in self.workers:
            worker.sendall(bytes(encoded_command, encoding="utf-8"))
            self.waiting_response = True
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
            self.waiting_response = False
            data = inputs.recv(2048).decode("utf-8")
            if data == "":
                self._close_connection(inputs)
                return
            else:
                json_data = json.loads(data)
                print("\n", json_data)
        else:
            if self.waiting_response:
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
        new_connection_index = str(len(self.inputs))

        self.inputs.append(connection)
        self.workers.append(connection)
        self.states[new_connection_index] = utils.get_initial_state()
        connection.sendall(bytes(utils.encode_command(type="first_access", id_value=new_connection_index), encoding="utf-8"))
        print(new_connection_index)

        if(len(self.workers) == 1): # First connection on the server
            print("A primeira conexao com o servidor foi feita.\n")
            self.show_menu()

    def _close_connection(self, conn):
        print(conn, "Desconectado")

        self.inputs.remove(conn)
        self.workers.remove(conn)

        conn.close()
