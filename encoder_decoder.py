def ask_main_menu():
    return [
        "[0] - Sair",
        "[1] - Monitorar dispositivos",
        "[2] - Acionar dispositivos",
        "[3] - Gerar log de comandos",
    ]

def ask_monitoring():
    return [
        "[0] - Voltar",
        "[1] - Todos os estados",
        "[2] - Estado dos sensores",
        "[3] - Estado das saidas",
        "[4] - Temperatura e umidade",
        "[5] - Numero de pessoas na sala",
        "[6] - Numero de pessoas no predio"
    ]

def ask_command(state):
    return [
        "[0] - Voltar",
        "[1] - Acionar lampada 0",
        "[2] - Acionar ar condicionado",
        "[3] - Acionar projetor",
        "[4] - Acionar sistema de alarme",
        "[5] - Acionar alarme de incendio"
        "[6] - Ligar todas as lampadas do predio"
        "[6] - Desligar todas as lampadas do predio"
        "[7] - Ligar todas as cargas do predio (Lampadas, projetores e aparelhos de Ar-Condicionado)"
    ]