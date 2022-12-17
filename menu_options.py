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

def ask_worker(workers):
    return [
        "[0] - Voltar",
        *[f"[{index + 1}] - {worker.name}" for index, worker in enumerate(workers)],
        f"[{len(workers) + 1}] - Ligar todas as lampadas do predio",
        f"[{len(workers) + 2}] - Desligar todas as cargas do predio (Lampadas, projetores e aparelhos de Ar-Condicionado)",
        f"[{len(workers) + 3}] - Ligar o sistema de alarme do prédio",
        f"[{len(workers) + 4}] - Desligar o sistema de alarme do prédio",
    ]

def ask_command(states):
    return [
        "[0] - Voltar",
        f"[1] - Acionar lampada 1 - {'Desligada' if states['L_01'] == 0 else 'Ligada'}",
        f"[2] - Acionar lampada 2 - {'Desligada' if states['L_02'] == 0 else 'Ligada'}",
        f"[3] - Acionar ar condicionado - {'Desligado' if states['AC'] == 0 else 'Ligado'}",
        f"[4] - Acionar projetor - {'Desligado' if states['PR'] == 0 else 'Ligado'}",
        f"[5] - Acionar sirene do alarme - {'Desligado' if states['AL_BZ'] == 0 else 'Ligado'}",
        f"[6] - Acionar alarme de incendio - {'Desligado' if states['SFum'] == 0 else 'Ligado'}",
        f"[7] - Acionar sistema de alarme - {'Desligado' if states['Alarme'] == 0 else 'Ligado'}",
        "[8] - Ligar todas as lampadas",
        "[9] - Desligar todas as lampadas",
        "[10] - Desligar todas as cargas (Lampadas, projetores e aparelhos de Ar-Condicionado)"
    ]

# print(ask_worker(5))