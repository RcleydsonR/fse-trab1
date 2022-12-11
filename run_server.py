import sys
import click
import threading
from servidor_central import Server

@click.command()
@click.option("--ip", "-i", help="Ip address of the central server", required=True)
@click.option("--port", "-p", default=10000, help="Port of the central server", show_default=True)
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

if __name__ == "__main__":
    main()