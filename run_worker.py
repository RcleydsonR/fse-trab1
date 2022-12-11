import click
from servidor_distribuido import Worker
from threading import Thread

@click.command()
@click.option('--ip', '-i', default='127.0.0.1', help='Ip address of the server')
@click.option('--port', '-p', default=7777, help='Port of the server')
@click.option('--config', '-c', help='Dashboard configuration (Json file)')
def main(ip, port, config):
    worker = Worker(ip, port, config)

    try:
        worker.start()
        # Thread(target=worker.input_proc).start()
        # Thread(target=worker.verifyTemperature).start()
    except KeyboardInterrupt:
        worker.close()
        
if __name__ == '__main__':
    main()