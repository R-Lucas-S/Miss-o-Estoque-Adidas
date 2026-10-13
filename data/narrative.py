"""Dados narrativos da campanha; manter falas fora das cenas de gameplay."""

CHARACTERS = {
    "rafael": {"name": "Rafael", "role": "Gerente", "color": (70, 155, 232), "portrait_dir": "rafael"},
    "larissa": {"name": "Larissa", "role": "Subgerente", "color": (164, 92, 228), "portrait_dir": "larissa"},
    "marcelli": {"name": "Marcelli", "role": "Líder", "color": (50, 193, 132), "portrait_dir": "marcelli"},
    "jessica": {"name": "Jéssica", "role": "Líder", "color": (237, 73, 145), "portrait_dir": "jessica"},
    # mantém compatibilidade com os diálogos antigos enquanto eles são migrados.
    "conferente": {"name": "Marcelli", "role": "Líder", "color": (50, 193, 132), "portrait_dir": "marcelli"},
    "supervisor": {"name": "Rafael", "role": "Gerente", "color": (70, 155, 232), "portrait_dir": "rafael"},
}

CUTSCENES = {
    "prologue": {
        "focus_x": 320,
        "title": "TREINAMENTO",
        "subtitle": "Bem-vindo ao estoque",
        "lines": (
            {"speaker": "rafael", "expression": "normal", "text": "Bem-vindo. Organização e atenção fazem diferença todos os dias."},
            {"speaker": "marcelli", "expression": "smile", "text": "Eu mostro o básico. Vamos começar pelo treinamento."},
        ),
    },
    "level1_intro": {
        "focus_x": 790,
        "title": "MISSÃO 1",
        "subtitle": "RECEBIMENTO",
        "lines": (
            {"speaker": "marcelli", "expression": "normal", "text": "Chegaram novos produtos. Observe a identificação de cada caixa."},
            {"speaker": "marcelli", "expression": "smile", "text": "Leve cada item para a seção correta antes de seguir."},
        ),
    },
    "level2_intro": {
        "focus_x": 970,
        "title": "MISSÃO 2",
        "subtitle": "ORGANIZAÇÃO",
        "lines": (
            {"speaker": "jessica", "expression": "normal", "text": "Agora precisamos de mais precisão."},
            {"speaker": "jessica", "expression": "smile", "text": "Confira categoria, referência e tamanho antes de armazenar."},
        ),
    },
    "level3_intro": {
        "focus_x": 760,
        "title": "MISSÃO 3",
        "subtitle": "CONFERÊNCIA",
        "lines": (
            {"speaker": "larissa", "expression": "serious", "text": "Nem sempre o estoque estará perfeito."},
            {"speaker": "larissa", "expression": "normal", "text": "Encontre os produtos fora da seção e corrija as divergências."},
        ),
    },
    "level4_intro": {
        "focus_x": 760,
        "title": "MISSÃO 4",
        "subtitle": "SEPARAÇÃO",
        "lines": (
            {"speaker": "rafael", "expression": "smile", "text": "Você já sabe receber, organizar e conferir."},
            {"speaker": "rafael", "expression": "normal", "text": "Agora localize os itens certos e prepare o pedido A-104."},
        ),
    },
    "level5_intro": {
        "focus_x": 2180,
        "title": "MISSÃO 5",
        "subtitle": "REPOSIÇÃO",
        "lines": (
            {"speaker": "jessica", "expression": "serious", "text": "Pessoal, precisamos de reposição no salão."},
            {"speaker": "jessica", "expression": "normal", "text": "Tem cliente procurando esse tamanho. Vamos agilizar."},
            {"speaker": "larissa", "expression": "smile", "text": "Confere as referências e separa por prioridade antes de levar."},
        ),
    },
}

COMMS = {
    "wrong": ("Confira a etiqueta novamente.", "Observe referência e tamanho antes de continuar."),
    "correct": ("Boa leitura da etiqueta.", "Certo. Continue nesse ritmo."),
    "scanner": ("O scanner confirma o item do pedido.", "Use o scanner para tirar qualquer dúvida."),
}
