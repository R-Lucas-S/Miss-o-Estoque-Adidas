# Caminhada e animação dos personagens

## Diagnóstico visual (25/09/2026)

Foram abertos o sheet original de Daniel, os motion_atlas_v2 de Luiza/Andrew
e os três motion_atlas_v3 que estavam no disco, mas não eram carregados.
Os seis frames cadastrados não representavam seis fases úteis: especialmente
Luiza e Andrew repetiam a perna da frente, sem passagem e contato oposto
consistentes. V3 também continha duplicações; Andrew tinha sete figuras por
linha. Reordenar esses arquivos ou acelerar o timer não corrigia o desenho.

Havia ainda três problemas técnicos:

- `_scaled_frame` ajustava cada pose à própria altura, alterando sua escala.
- A física avançava 3 px por atualização, sem delta time; a animação usava
  tempo e estimava a velocidade multiplicando o deslocamento por 60.
- O flip ocorria antes de normalizar os canvases, permitindo deslocamento
  de um pixel quando as larguras tinham paridades diferentes.

## Arte utilizada e limite do ciclo

Cada personagem tem seus próprios `gait_v4.png/json` e `rest_v4.png/json` em
`missao_estoque/assets/characters/playable/{daniel,luiza,andrew_lessa}`.
Os atlas anteriores continuam disponíveis para os outros estados.

WALK e CARRY WALK usam **quatro poses-chave reais**, em ordem circular:

1. `walk_left_contact`: perna próxima com listras à frente, braço próximo atrás.
2. `walk_left_pass`: essa perna sustenta, a outra passa.
3. `walk_right_contact`: perna próxima atrás, braço próximo à frente.
4. `walk_right_pass`: a outra perna sustenta, a próxima passa.

As tentativas de oito desenhos voltaram a repetir o mesmo contato e soltar
uma mão da caixa. Não foram incorporadas. Portanto esta versão **não entrega
o ciclo ideal de oito desenhos independentes com DOWN/UP**; entrega os quatro
keyframes com alternância verificada. Não há ping-pong nem duplicação para
inflar a contagem. Os joelhos foram corrigidos para uma passagem mais baixa.

IDLE e CARRY IDLE têm quatro desenhos neutros, com variação pequena do tronco,
pés apoiados e 3 FPS. As ações especiais existentes foram preservadas.
Prompts e origem dos arquivos: [animation_assets.md](animation_assets.md).

## Escala, pivôs e caixa

Os manifestos descrevem recortes, pivôs, altura de referência e âncoras das
mãos em coordenadas do atlas. Uma única escala por atlas é aplicada no preload;
não se ajusta a altura de cada pose. No tamanho normal, os corpos ficam com
96–98 px de altura, dentro do canvas de 110 px. A variação de 1–2 px vem do
desenho/postura e da amostragem nearest-neighbor, não de escalas por frame.

O pivot horizontal foi alinhado pela cabeça/tronco, não pela largura variável
dos braços e pés. A base de apoio é y=110 em todos os WALK finais. O flip é
feito depois do padding completo. O desenho sempre usa MIDBOTTOM.

`Player.rect`/`hitbox` continua 56×92. `position` mantém a posição física em
ponto flutuante; `feet_position` expõe o midbottom da hitbox. Alterar o frame
não escreve nesses valores. Reposicionamentos pelas cenas continuam aceitos.

Caixa e mãos estão integradas na arte. Os manifestos fornecem `hand`, e
`carry_anchor()` acompanha esse ponto, inclusive espelhado. Salto/queda com
caixa reutilizam as poses de passagem do mesmo atlas; aterrissagem usa a pose
neutra. A entidade Box mantém seu comportamento, sem segunda caixa desenhada.

## Movimento e cadência

O loop principal fornece `systems.frame_time.seconds`. `Player.update` também
aceita `dt_seconds` explícito. A velocidade nominal continua 180 px/s,
equivalente aos 3 px/frame anteriores a 60 Hz. O deslocamento é resolvido antes
da animação, com a posição fracionária preservada. Delta é limitado a 50 ms
para evitar grandes saltos após uma travada.

No chão, o controlador consome `abs(actual_delta_x)` após colisões: WALK
completa um ciclo em 140 px; CARRY WALK, em 150 px. A 180 px/s isso produz,
respectivamente, cerca de 5,14 e 4,8 desenhos por segundo. Essa cadência foi
ajustada aos quatro keyframes, não aos oito frames da referência inicial.
Os contatos que emitem passos são os índices 0 e 2. Não há avanço de WALK
sem deslocamento real. O som mantém o cooldown existente.

Previews e estados sem deslocamento usam tempo: WALK 194 ms, CARRY WALK
208 ms, IDLE/CARRY IDLE 333 ms, RUN 83 ms. Tempo remanescente é preservado.
Começar a andar reinicia no contato 0; parar troca para IDLE neutro.

## Inspeção

- No jogo: **F8** exibe personagem, estado, frame/total, FPS da animação e do
  jogo, velocidade, direção, MIDBOTTOM e âncoras.
- **F9** alterna animação em 25%; a física continua normal. Esse modo serve
  para examinar poses, não para avaliar deslizamento em velocidade normal.
- Ambos começam desligados.
- `python -m tools.inspect_animations`: TAB personagem, cima/baixo estado,
  espaço play/pause, esquerda/direita frame, F flip, S 25%, O onion skin.
- `python -m tools.review_walk_cycle`: gera GIFs, folhas de poses,
  transições e trace em `artifacts/walk_review`. Requer Pillow apenas para
  exportar GIF; o jogo não depende dele.

## Validação realizada

Os quadros de um replay de oito segundos de `Player.update/draw` foram
renderizados e inspecionados: três personagens, direita/esquerda, parada,
retomada, caixa parada/em movimento, salto e aterrissagem. As folhas ampliadas
mostram todos os contatos e passagens em ambas as direções. Os GIFs permitem
revisar a continuidade temporal no visualizador do usuário.

46 testes passaram executando cada arquivo de teste em um processo separado.
Isso evita reutilizar objetos de fonte Pygame após `pygame.quit()` de outras
classes: a descoberta inteira em um único processo travou em testes de fonte/UI.
Não foi alterado o sistema de UI para contornar esse problema fora do escopo.

Os novos testes cobrem posição/fase equivalentes a 30, 60 e 144 FPS, chão,
hitbox, flip exato, ausência de avanço sem distância, contatos alternados,
parar/retomar, estados aéreos com e sem caixa e câmera lenta sem mudar a física.
Testes não substituem a avaliação artística; oito desenhos independentes
continuam sendo uma melhoria possível desta versão de quatro keyframes.
