def ask_main_menu():
    return [
        "[0] - Sair",
        "[1] - Monitorar dispositivos",
        "[2] - Acionar dispositivos",
        "[3] - Gerar log de comandos",
    ]

def ask_worker(workers, alarme):
    return [
        "[0] - Voltar",
        *[f"[{index + 1}] - {worker.name}" for index, worker in enumerate(workers)],
        f"[{len(workers) + 1}] - Ligar todas as lampadas do predio",
        f"[{len(workers) + 2}] - Desligar todas as cargas do predio (Lampadas, projetores e aparelhos de Ar-Condicionado)",
        f"[{len(workers) + 3}] - Ligar/Desligar o sistema de alarme do predio - {'Desligado' if alarme== 0 else 'Ligado'}",
    ]

def ask_command(states):
    return [
        "[0] - Voltar",
        f"[1] - Ligar/Desligar lampada 1 - {'Desligada' if states['L_01'] == 0 else 'Ligada'}",
        f"[2] - Ligar/Desligar lampada 2 - {'Desligada' if states['L_02'] == 0 else 'Ligada'}",
        f"[3] - Ligar/Desligar ar condicionado - {'Desligado' if states['AC'] == 0 else 'Ligado'}",
        f"[4] - Ligar/Desligar projetor - {'Desligado' if states['PR'] == 0 else 'Ligado'}",
        f"[5] - Ligar/Desligar sirene do alarme - {'Desligado' if states['AL_BZ'] == 0 else 'Ligado'}",
        f"[6] - Ligar/Desligar alarme de incendio - {'Desligado' if states['SFum'] == 0 else 'Ligado'}",
        "[7] - Ligar todas as lampadas",
        "[8] - Desligar todas as lampadas",
        "[9] - Desligar todas as cargas (Lampadas, projetores e aparelhos de Ar-Condicionado)"
    ]

# print(ask_worker(5))