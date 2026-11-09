# Missão: Estoque Perfeito

Um jogo 2D em Python sobre rotinas de estoque. A demo acompanha um treinamento em uma loja: receber produtos, organizar prateleiras, conferir divergências, separar um pedido e repor itens no salão.

> **Status:** demo de playtest `0.5.0-demo.1` para Windows. O repositório também contém o código-fonte em Python.

## Imagens

| Menu principal | Seleção de personagem |
| --- | --- |
| ![Menu principal da demo Missão: Estoque Perfeito](docs/images/menu-principal.png) | ![Tela de seleção de personagem](docs/images/selecao-personagem.png) |

### Missão de recebimento

![Cena da missão de recebimento, com caixas e orientação da personagem Marcelli](docs/images/missao-recebimento.png)

## O que você encontra

- Tutorial e campanha com cinco missões sobre etapas do trabalho no estoque.
- Personagens, diálogos e orientações durante as tarefas.
- Identificação de produtos por categoria, referência e tamanho.
- Scanner nas missões que indicam esse recurso.
- Progresso e configurações salvos localmente.

## Como jogar a demo no Windows

1. Baixe e extraia a pasta completa da demo.
2. Abra `MissaoEstoque_Demo.exe`.
3. Siga o tutorial se for sua primeira vez. Não mova nem apague os arquivos internos da pasta.

Os controles e as instruções de feedback estão em [`README_DEMO.txt`](README_DEMO.txt).

> O executável não está armazenado na raiz atual do repositório. Confira a seção **Releases** para saber se há uma build disponível. Se não houver, use as instruções para executar pelo código-fonte.

## Executar pelo código-fonte

Requer Python e Windows. No terminal, na pasta do projeto:

```bash
python -m venv .venv
```

Ative o ambiente virtual e instale as dependências:

```bash
pip install -r requirements.txt
```

Inicie o jogo:

```bash
python -m missao_estoque.main
```

## Controles da demo

| Ação | Teclas |
| --- | --- |
| Mover | `A` / `D` ou setas esquerda / direita |
| Pular | `Espaço` |
| Interagir, pegar ou armazenar caixas | `E` |
| Usar scanner quando indicado | `Q` |
| Consultar informações quando indicado | `Tab` |
| Voltar ou pausar quando disponível | `Esc` |
| Alternar janela e tela cheia | `F11` ou `Alt` + `Enter` |

## Feedback e dados locais

Conte qual fase foi mais divertida, onde encontrou dificuldades e se os objetivos ficaram claros. Para relatar um erro, envie uma captura de tela e o `crash.log` da pasta `%LOCALAPPDATA%\MissaoEstoqueDemo\logs\`.

A demo informa que não envia telemetria nem dados pela internet. Progresso e configurações ficam em `%LOCALAPPDATA%\MissaoEstoqueDemo\save_demo.json`.

## Tecnologias

- Python
- Pygame 2.6.1
- PyInstaller para empacotamento da demo
