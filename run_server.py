import sys
import click
import threading
from servidor_central import Server

@click.command()
@click.option('--ip', '-i', default='127.0.0.1', help='Ip address of the central server', show_default=True)
@click.option('--port', '-p', default=7777, help='Port of the central server', show_default=True)
def main(ip, port):
    server = Server(ip, port)

    # menu_thread = threading.Thread(target=server.menu)
    # menu_thread.start()

    try:
        server.start()
    except KeyboardInterrupt:
        print("Finalizando...")
    finally:
        server.close()

if __name__ == '__main__':
    main()