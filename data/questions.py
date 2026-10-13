"""Banco data-driven de situações operacionais usadas pelos quizzes."""


def q(identifier, question, correct, *wrong, tags=(), difficulty="medium"):
    return {
        "id": identifier,
        "question": question,
        "correct": correct,
        "options": (correct, *wrong),
        "explanation": EXPLANATIONS[identifier],
        "tags": tuple(tags),
        "difficulty": difficulty,
    }


EXPLANATIONS = {
    "q01": "Categoria, referência e tamanho precisam corresponder ao pedido.",
    "q02": "A referência identifica exatamente qual produto deve ser movimentado.",
    "q03": "O tamanho também faz parte da conferência quando aparece no pedido.",
    "q04": "Acessórios podem não ter tamanho; confira os dados que se aplicam.",
    "q05": "A categoria indica a área correta de armazenamento.",
    "q06": "Conferir antes de guardar reduz erros e retrabalho.",
    "q07": "O scanner compara os dados e ajuda a encontrar divergências.",
    "q08": "Uma divergência deve ser corrigida antes de seguir para outra etapa.",
    "q09": "Itens corretos do pedido devem ser reunidos no carrinho de picking.",
    "q10": "A lista continua sendo a fonte de verdade durante a separação.",
    "q11": "Prioridade alta atende primeiro a necessidade mais urgente do salão.",
    "q12": "Use a referência AC-018 para localizar o item exato.",
    "q13": "Consultar a lista reduz a chance de esquecer ou trocar itens.",
    "q14": "O pedido só termina quando todos os itens necessários foram separados.",
    "q15": "Uma etiqueta correta no lugar errado ainda é falha de organização.",
    "q16": "A quantidade solicitada informa quantas unidades devem ser levadas.",
    "q17": "A referência está certa, mas ainda falta uma unidade.",
    "q18": "Uma conferência rápida evita corrigir o processo depois.",
    "q19": "Referência e tamanho correspondem; o produto pode ser separado.",
    "q20": "Nem toda categoria utiliza os mesmos atributos.",
    "q21": "Quando o pedido informa tamanho, ele precisa ser respeitado.",
    "q22": "Diante de uma diferença, revise os dados antes de decidir.",
    "q23": "Identificação clara torna localização e conferência mais rápidas.",
    "q24": "O carrinho deve receber somente itens conferidos do pedido.",
    "q25": "Detectar cedo impede que a divergência avance no processo.",
    "q26": "Eficiência combina bom ritmo com precisão.",
    "q27": "O contador 4/5 mostra que ainda falta um item ou uma ação.",
    "q28": "Objetivo, lista e etiqueta existem para apoiar a decisão correta.",
    "q29": "Organização, categoria e referência aceleram a localização.",
    "q30": "Conferir garante que o item correto siga para a etapa correta.",
}


QUESTION_BANK = (
    q("q01", "O pedido solicita TN-014 tamanho 40. Você encontrou TN-014 tamanho 42. O que fazer?", "Procurar TN-014 tamanho 40", "Separar o tamanho 42", "Escolher qualquer tênis", "Finalizar o pedido", tags=("separacao", "tamanho")),
    q("q02", "Duas caixas são da mesma categoria. Qual dado identifica o produto exato?", "Referência", "Cor da caixa", "Posição do jogador", "Tamanho da sala", tags=("referencia", "organizacao"), difficulty="easy"),
    q("q03", "A referência confere, mas o tamanho é diferente. O item atende ao pedido?", "Não, é preciso o tamanho solicitado", "Sim, a referência basta", "Sim, se estiver perto", "Somente sem scanner", tags=("conferencia", "tamanho")),
    q("q04", "Uma caixa de acessórios não possui tamanho. O que conferir?", "Referência e categoria", "Inventar um tamanho", "A cor da parede", "A pontuação", tags=("referencia", "categoria"), difficulty="easy"),
    q("q05", "Uma caixa marcada ROUPAS deve ser armazenada onde?", "Na área ROUPAS", "Na área TÊNIS", "Em qualquer estante", "No recebimento", tags=("organizacao", "categoria"), difficulty="easy"),
    q("q06", "Qual atitude reduz retrabalho no armazenamento?", "Conferir a etiqueta antes de guardar", "Guardar e conferir depois", "Escolher pela cor", "Ignorar a categoria", tags=("organizacao", "eficiencia")),
    q("q07", "Para que serve o scanner durante a conferência?", "Comparar os dados do produto", "Mover a caixa", "Abrir o mapa", "Aumentar o combo", tags=("conferencia", "scanner"), difficulty="easy"),
    q("q08", "O scanner encontrou tamanho diferente da lista. Qual é a ação correta?", "Revisar e corrigir a divergência", "Confirmar assim mesmo", "Ignorar o scanner", "Trocar a lista", tags=("conferencia", "tamanho")),
    q("q09", "Após conferir um item correto do pedido, para onde levá-lo?", "Para o carrinho de picking", "Para uma prateleira aleatória", "Para o recebimento", "Para perto de um NPC", tags=("separacao", "carrinho"), difficulty="easy"),
    q("q10", "Durante uma separação com vários itens, o que deve orientar o trabalho?", "A lista do pedido", "A memória apenas", "A caixa mais próxima", "A pontuação", tags=("separacao", "organizacao")),
    q("q11", "Na reposição, qual item deve ser atendido primeiro?", "O de prioridade mais alta", "O maior volume", "O mais distante", "Qualquer item", tags=("reposicao", "prioridade")),
    q("q12", "Você precisa encontrar AC-018. Qual caixa deve procurar?", "A identificada como AC-018", "Qualquer acessório", "A maior caixa", "A mais próxima", tags=("referencia", "separacao"), difficulty="easy"),
    q("q13", "Por que consultar a lista durante toda a separação?", "Para reduzir a chance de erro", "Porque o scanner para", "Porque as caixas são iguais", "Para perder tempo", tags=("separacao", "eficiencia")),
    q("q14", "Você separou 2 de 3 produtos. O que fazer antes de concluir?", "Verificar qual item ainda falta", "Finalizar assim mesmo", "Adicionar qualquer produto", "Remover um item", tags=("separacao", "progresso")),
    q("q15", "Uma caixa correta foi colocada na prateleira errada. Isso é o quê?", "Um problema de organização", "Apenas um problema visual", "Um erro de tamanho", "Uma referência inválida", tags=("organizacao", "categoria")),
    q("q16", "Na reposição, qual informação mostra QUANTO levar?", "Quantidade solicitada", "Cor do HUD", "Número de NPCs", "Pontuação atual", tags=("reposicao", "quantidade"), difficulty="easy"),
    q("q17", "A lista pede 2 unidades de TN-014 e você colocou apenas 1. Qual o status?", "Reposição incompleta", "Reposição concluída", "Categoria incorreta", "Referência incorreta", tags=("reposicao", "quantidade")),
    q("q18", "Qual atitude tende a gerar menos retrabalho?", "Conferir movimentações importantes", "Agir rápido sem conferir", "Misturar caixas", "Ignorar diferenças", tags=("eficiencia", "conferencia")),
    q("q19", "Produto e pedido mostram TN-014 tamanho 40. O que fazer?", "Separar o produto", "Procurar outra referência", "Alterar o tamanho", "Registrar divergência", tags=("separacao", "conferencia")),
    q("q20", "Se um acessório não utiliza tamanho, qual é a melhor conduta?", "Conferir os demais dados aplicáveis", "Inventar um tamanho", "Usar o tamanho de outra caixa", "Ignorar a referência", tags=("categoria", "conferencia")),
    q("q21", "Há TN-014 nos tamanhos 40 e 42; o pedido pede 40. Qual escolher?", "TN-014 tamanho 40", "TN-014 tamanho 42", "Qualquer uma", "A caixa maior", tags=("tamanho", "separacao")),
    q("q22", "Scanner e lista mostram dados diferentes. Qual deve ser a primeira reação?", "Verificar novamente antes de confirmar", "Ignorar o scanner", "Confirmar imediatamente", "Alterar a lista", tags=("scanner", "conferencia")),
    q("q23", "Por que uma legenda clara na caixa é importante?", "Facilita identificar o produto", "Serve apenas de decoração", "Substitui a organização", "Aumenta a velocidade", tags=("referencia", "organizacao"), difficulty="easy"),
    q("q24", "O que deve acontecer antes de colocar um produto no carrinho?", "Conferir se corresponde ao pedido", "Finalizar a missão", "Remover a referência", "Misturar com outros itens", tags=("carrinho", "separacao")),
    q("q25", "Qual o benefício de detectar uma divergência durante a conferência?", "Evitar que o erro avance", "Aumentar o número de caixas", "Eliminar prateleiras", "Alterar o produto sozinho", tags=("conferencia", "eficiencia")),
    q("q26", "Qual opção representa uma operação eficiente?", "Trabalhar com ritmo e precisão", "Fazer rápido mesmo errando", "Conferir infinitamente", "Ignorar a lista", tags=("eficiencia",), difficulty="challenge"),
    q("q27", "Você terminou uma tarefa, mas o contador mostra 4/5. O que significa?", "Ainda falta um item ou ação", "A missão acabou", "O contador não importa", "É preciso fechar o jogo", tags=("progresso",), difficulty="easy"),
    q("q28", "Qual a melhor forma de lidar com uma dúvida durante a tarefa?", "Consultar objetivo, lista ou produto", "Escolher aleatoriamente", "Ignorar a informação", "Encerrar a missão", tags=("organizacao", "eficiencia")),
    q("q29", "Em uma área com muitas caixas, o que mais ajuda a localizar um item?", "Categoria, referência e organização", "O tamanho da sala", "A direção do jogador", "A pontuação", tags=("organizacao", "referencia")),
    q("q30", "Por que conferir antes de movimentar ou separar um produto?", "Para enviar o item certo à etapa certa", "Para tornar a tarefa lenta", "Para aumentar interações", "Para ouvir o scanner", tags=("conferencia", "eficiencia"), difficulty="challenge"),
)


LEVEL_TAGS = {
    "tutorial": ("categoria", "referencia", "organizacao"),
    "level1": ("categoria", "organizacao", "referencia"),
    "level2": ("categoria", "referencia", "tamanho"),
    "level3": ("conferencia", "scanner", "tamanho", "organizacao"),
    "level4": ("separacao", "carrinho", "referencia", "conferencia"),
    "level5": ("reposicao", "prioridade", "quantidade", "eficiencia", "conferencia"),
}

QUESTIONS_BY_LEVEL = {
    level: tuple(question for question in QUESTION_BANK if set(question["tags"]) & set(tags))
    for level, tags in LEVEL_TAGS.items()
}

# Compatibilidade com ferramentas e integrações anteriores do projeto.
QUIZ_TUTORIAL = QUESTIONS_BY_LEVEL["tutorial"]
QUIZ_LEVEL_1 = QUESTIONS_BY_LEVEL["level1"]
QUIZ_LEVEL_2 = QUESTIONS_BY_LEVEL["level2"]
QUIZ_LEVEL_3 = QUESTIONS_BY_LEVEL["level3"]
QUIZ_LEVEL_4 = QUESTIONS_BY_LEVEL["level4"]
QUIZ_LEVEL_5 = QUESTIONS_BY_LEVEL["level5"]
