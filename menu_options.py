def ask_main_menu():
    return [
        "[0] - Sair",
        "[1] - Monitorar dispositivos",
        "[2] - Acionar dispositivos",
        "[3] - Gerar log de comandos",
    ]

def ask_trigger(workers, alarme, alarme_incendio):
    return [
        "[0] - Voltar",
        *[f"[{index + 1}] - {worker.name}" for index, worker in enumerate(workers)],
        f"[{len(workers) + 1}] - Ligar todas as lampadas do predio",
        f"[{len(workers) + 2}] - Desligar todas as cargas do predio (Lampadas, projetores e aparelhos de Ar-Condicionado)",
        f"[{len(workers) + 3}] - Ligar/Desligar o sistema de alarme do predio - {'Desligado' if alarme== 0 else 'Ligado'}",
        f"[{len(workers) + 4}] - Ligar/Desligar o sistema de alarme de incendio do predio - {'Desligado' if alarme_incendio== 0 else 'Ligado'}",
    ]

def ask_command(states):
    return [
        "[0] - Voltar",
        f"[1] - Ligar/Desligar lampada 1 - {'Desligada' if states['L_01'] == 0 else 'Ligada'}",
        f"[2] - Ligar/Desligar lampada 2 - {'Desligada' if states['L_02'] == 0 else 'Ligada'}",
        f"[3] - Ligar/Desligar ar condicionado - {'Desligado' if states['AC'] == 0 else 'Ligado'}",
        f"[4] - Ligar/Desligar projetor - {'Desligado' if states['PR'] == 0 else 'Ligado'}",
        "[5] - Ligar todas as lampadas",
        "[6] - Desligar todas as lampadas",
        "[7] - Desligar todas as cargas (Lampadas, projetores e aparelhos de Ar-Condicionado)"
    ]