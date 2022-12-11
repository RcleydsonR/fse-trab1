import socket
import select
import sys
import json
import encoder_decoder
from typing import TextIO

class Server():
    server: socket.socket
    ip: str
    port: int
    max_connections: int
    inputs: "list[socket.socket | TextIO]"
    workers: "list[socket.socket]"

    def __init__(self, ip, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.ip = ip
        self.port = port
        self.inputs = [self.server, sys.stdin]
        self.workers = []

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
        print("Digite uma das opcoes:", *encoder_decoder.ask_main_menu(), "", sep="\n")
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
        possible_options = [i for i in range(len(encoder_decoder.ask_main_menu()))]
        if not(opt in possible_options):
            #print("Opcao invalida, digite novamente:\n1. Estado das entradas\n2. Estado das saídas\n3. Valor da temperatura e umidade\n4. Contador de ocupações\n")
            print("Opcao invalida, digite novamente:", *encoder_decoder.ask_main_menu(), "", sep="\n")
            return

        self._handle_main_menu_opt(opt)

    def _handle_main_menu_opt(self, opt):
        if opt == 0:
            self.close()
        elif opt == 1:
            pass
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
        print("Qual o servidor:\n[0] - Voltar")
        [print(f"[{i + 1}] - Servidor {i + 1}") for i in range(len(self.workers))]
        try:
            worker = int(input())
        except ValueError:
            print("Por favor, digite um valor inteiro")
            return
        
        possible_workers = [0, *[i + 1 for i in range(len(self.workers))]]

        while not(worker in possible_workers):
            print("Opcao invalida, digite novamente, servidores disponiveis:\n[0] - Voltar")
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
            
        json_message = {
            "type": "teste",
            "message": f"Enviando mensagem para worker correto {worker - 1}"
        }

        data = json.dumps(json_message)
        self.workers[worker - 1].sendall(bytes(data, encoding="utf-8"))
        print("mensagem enviada com sucesso.\n\n")
        waiting_response = True
        self.show_menu()

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

    def _handle_writable(self, output: socket.socket):
        return

    def _handle_readable(self, inputs: socket.socket):
        if inputs is self.server:
            self._manage_connection(inputs)
        elif isinstance(inputs, socket.socket):
            if inputs.recv(1024).decode("utf-8") == "":
                self._close_connection(inputs)
                return
            print(inputs.recv(1024).decode("utf-8") == "")
            # data = inputs.recv(1024).decode("utf-8")
            # json_data = json.loads(data)
            # print(json_data)
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

        self.inputs.append(connection)
        self.workers.append(connection)

        if(len(self.workers) == 1): # First connection
            self.show_menu()

        json_message = {
            "type": "welcome",
            "message": len(self.inputs) - 1
        }
        data = json.dumps(json_message)
        connection.sendall(bytes(data, encoding="utf-8"))

    def _close_connection(self, conn):
        print(conn, "Desconectado")

        self.inputs.remove(conn)
        self.workers.remove(conn)

        conn.close()
