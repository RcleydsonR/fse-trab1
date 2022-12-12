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
        print("Digite uma das opcoes:", *menu_options.ask_main_menu(), "", sep="\n")
        # print(("Qual a informacao desejada:\n1. Estado das entradas\n2. Estado das saídas\n3. Valor da temperatura e umidade\n4. Contador de ocupações\n"))

    def menu(self):
        try:
            opt = int(input())
        except ValueError:
            print("Por favor, digite um valor inteiro")
            return

        if len(self.workers) == 0:
            print("Aguardando algum servidor distribuido se conectar\n\n")
            return

        # possible_options = [i + 1 for i in range(len(self.workers))]
        possible_options = [i for i in range(len(menu_options.ask_main_menu()))]
        if not(opt in possible_options):
            #print("Opcao invalida, digite novamente:\n1. Estado das entradas\n2. Estado das saídas\n3. Valor da temperatura e umidade\n4. Contador de ocupações\n")
            print("Opcao invalida, digite novamente:", *menu_options.ask_main_menu(), "", sep="\n")
            return

        self._handle_main_menu_opt(opt)

    def _handle_main_menu_opt(self, opt):
        if opt == 0:
            self.close()
        elif opt == 1:
            print(self.states)
        elif opt == 2:
            self._define_worker()
            pass
        else:
            pass

        # json_message = {
        #     "type": "teste",
        #     "message": "Enviando mensagem para worker correto"
        # }
        # data = json.dumps(json_message)
        # self.workers[opt - 1].sendall(bytes(data, encoding="utf-8"))
    def _define_worker(self):
        print("Qual o servidor ou opcao:\n[0] - Voltar")
        [print(f"[{i + 1}] - Servidor {i + 1}") for i in range(len(self.workers))]
        try:
            worker = int(input())
        except ValueError:
            print("Por favor, digite um valor inteiro")
            return
        
        possible_workers = [0, *[i + 1 for i in range(len(self.workers))]]

        while not(worker in possible_workers):
            print("Opcao invalida, digite novamente, servidores/opcoes disponiveis:\n[0] - Voltar")
            [print(f"[{i + 1}] - Servidor {i + 1}") for i in range(len(self.workers))]
            try:
                worker = int(input())
            except ValueError:
                print("Por favor, digite um valor inteiro")
                worker = -1

        if(worker == 0):
            print()
            self.show_menu()
            return
            
        self.workers[worker - 1].sendall(bytes(utils.encode_command(type="turn_on_all_lights"), encoding="utf-8"))
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
        return

    def send_message(self, conn: socket.socket, message):
        message_encoded = self._encode_message(message)
        conn.sendall(message_encoded)

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
        if exceptions in self.outputs:
            self.outputs.remove(exceptions)
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
