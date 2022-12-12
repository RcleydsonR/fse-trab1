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

def ask_worker(workers_size):
    return [
        "[0] - Voltar",
        *[f"[{i + 1}] - Servidor {i + 1}" for i in range(workers_size)],
        f"[{workers_size + 1}] - Ligar todas as lampadas do predio",
        f"[{workers_size + 2}] - Desligar todas as cargas do predio (Lampadas, projetores e aparelhos de Ar-Condicionado)",
    ]

def ask_command(states):
    return [
        "[0] - Voltar",
        f"[1] - Acionar lampada 1 - {'Desligada' if states['L_01'] == 0 else 'Ligada'}",
        f"[2] - Acionar lampada 2 - {'Desligada' if states['L_02'] == 0 else 'Ligada'}",
        f"[3] - Acionar ar condicionado - {'Desligado' if states['AC'] == 0 else 'Ligado'}",
        f"[4] - Acionar projetor - {'Desligado' if states['PR'] == 0 else 'Ligado'}",
        f"[5] - Acionar sistema de alarme - {'Desligado' if states['AL_BZ'] == 0 else 'Ligado'}",
        f"[6] - Acionar alarme de incendio - {'Desligado' if states['SFum'] == 0 else 'Ligado'}",
        "[7] - Ligar todas as lampadas",
        "[8] - Desligar todas as lampadas",
        "[9] - Desligar todas as cargas (Lampadas, projetores e aparelhos de Ar-Condicionado)"
    ]

# print(ask_worker(5))