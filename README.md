# Trabalho Final - Redes

## Aluno
|Matrícula | Aluno |
| -- | -- |
| 19/0019085  |  Rafael Ramos |

## Uso

Instale as dependencias na raspberry pi:<br>
`pip install -r requirements.txt`<br>

Execute o servidor central:<br>
```
$ python run_server.py --help
#Usage: run_server.py [OPTIONS]
#
#Options:
#  -i, --ip TEXT       Ip address of the server
#  -p, --port INTEGER  Port of the server
#  --help              Show this message and exit.

$ python run_server.py -i 127.0.0.1 -p 10691
# Aguardando em  ('127.0.0.1', 10691)
```

Execute os servidores distribuidos com atenção ao arquivo de configuração 01 e 02:<br>
config 1 -> sala 01 e sala 03<br>
config 2 -> sala 02 e sala 04<br>

Atente-se aos parametros principais dos arquivos de configuração como: **ip_servidor_central**, **porta_servidor_central**, **ip_servidor_distribuido** e **nome**.

```
$ python run_worker.py -c config_sala_01.json
ou
$ python run_worker.py -c config_sala_02.json
```

O controle dos servidores distribuidos ocorre no servidor central, como monitoramento, acionamento de dispositivos e geração do log de comandos em formato csv.