import click
from servidor_distribuido import Worker
from threading import Thread

@click.command()
@click.option("--config", "-c", help="Dashboard configuration (Json config file)", required=True)
def main(config):
    worker = Worker(config)

    try:
        worker.start()
        # Thread(target=worker.input_proc).start()
        # Thread(target=worker.verifyTemperature).start()
    except KeyboardInterrupt:
        worker.exit("\nSaindo do servidor...")
        
if __name__ == "__main__":
    main()