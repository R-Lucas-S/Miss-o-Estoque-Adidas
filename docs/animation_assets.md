# Origem dos assets de animação

Foi usada a ferramenta integrada `image_gen`, pela skill imagegen. Não foi
usado CLI/API alternativo. As referências foram os sprites locais de cada
personagem; a identidade de Daniel não foi aplicada a Luiza ou Andrew.

Arquivos finais no projeto (todos acompanhados por manifestos `.json`):

- `missao_estoque/assets/characters/playable/daniel/gait_v4.png`
- `missao_estoque/assets/characters/playable/daniel/rest_v4.png`
- `missao_estoque/assets/characters/playable/luiza/gait_v4.png`
- `missao_estoque/assets/characters/playable/luiza/rest_v4.png`
- `missao_estoque/assets/characters/playable/andrew_lessa/gait_v4.png`
- `missao_estoque/assets/characters/playable/andrew_lessa/rest_v4.png`

Os atlas de caminhada foram construídos primeiro como quatro contatos/passagens
alternados, com uma segunda linha correspondente carregando a caixa.
Versões intermediárias de oito frames foram rejeitadas visualmente.

## Prompt final aplicado à caminhada dos três personagens

> Targeted edit ONLY: lower the lifted knee in columns TWO and FOUR of BOTH rows so this is a relaxed WALK passing pose, NOT a high-knee march. Swing toe should clear ground only slightly, knee below mid thigh. Preserve the planted supporting leg, same leg identities, opposite striped leg contacts in columns ONE and THREE COMPLETELY UNCHANGED. Near leg supports in column two; far leg supports in column four. Keep the FOUR columns TWO rows layout, eight full sprites, every character head size, face, arms, body, uniform, hair and carrying box EXACTLY as input. Every character faces RIGHT. Do not change arms, box or hands. Only redraw the raised legs in columns 2 and 4 to be low natural walk passing poses with a small knee bend. Transparent background, no text/shadows.

## Prompt final aplicado ao idle dos três personagens

> Create companion IDLE sprite atlas for this exact same character, unchanged identity/style/head/body/uniform and proportions. 4 columns TWO rows, exactly eight full-body sprites facing RIGHT with both feet planted side by side neutrally on identical baseline, no walking, no wide legs, no raised knee. Row one FOUR extremely subtle breathing frames: neutral, chest/shoulders raised by one source pixel, neutral, relaxed. Feet and head size remain fixed. Row two FOUR matching neutral idle breathing poses holding the same small cardboard box from reference with both hands attached, same box size, below chin. No free/swinging arms in carry row. Same size character in all cells, consistent centered pelvis, adequate margins, no text/labels/shadows/background. Real transparent alpha. A production game sprite sheet, exact appearance of input character retained.

O loader apenas recorta, limpa resíduos de alpha baixo, aplica escala comum,
posiciona no canvas e espelha. Não redesenha membros proceduralmente.
