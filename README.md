# Jogo do Thor

> Pense em um animal. Eu tento adivinhar — e, quando erro, eu aprendo.

Reimplementação em Python do clássico jogo de adivinhar animais por árvore de
decisão, conhecido nos anos 1970 e 1980 simplesmente como **ANIMAL**.

Toda partida começa pela mesma pergunta — *"É o Thor?"* — e só depois de um
"não" o jogo desce a árvore de decisão. Dali em diante ele faz perguntas de
sim/não, chega a um palpite e, quando erra, pede ao jogador o animal correto e
uma pergunta que o distinga do palpite errado. Essa pergunta vira um nó novo na
árvore: a cada partida perdida, o jogo fica um pouco melhor. A base de
conhecimento é gravada em JSON e recarregada na próxima sessão.

## Como jogar

Requer **Python 3.11+**. Não há dependências além da biblioteca padrão.

```bash
# instalação em modo editável (recomendado para desenvolvimento)
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# jogar
sardinha

# ou, sem instalar nada
python -m sardinha
```

Por padrão a base de conhecimento fica em `animais.json`, no diretório atual.
Para usar outro arquivo:

```bash
sardinha --base ~/.local/share/sardinha/animais.json
```

Se o arquivo não existir, o jogo começa sem animais cadastrados. Depois da
pergunta inicial *"É o Thor?"*, a primeira resposta "não" pede diretamente o
animal pensado e cria a primeira folha da árvore.

### Uma partida típica

```
*** JOGO DO THOR ***
Pense em um animal. Eu tento adivinhar — e, quando erro, eu aprendo.

Você pensou em um animal? (s/n) s
É o Thor? (s/n) n
Errei. Me ensine, então.
Em que animal você pensou? tatu
Aprendido. Agora conheço 1 animal.
```

Responde-se com `s`/`sim` ou `n`/`não` (também valem `y`, `yes`, `no`, `1`, `0`).
`Ctrl+C` encerra a sessão salvando o que foi aprendido até ali.

## Como funciona

A base de conhecimento é uma **árvore binária**:

- **nós internos** (`Pergunta`) guardam uma pergunta de sim/não e os dois ramos;
- **folhas** (`Folha`) guardam um animal.

Jogar é descer a árvore, escolhendo o ramo `sim` ou `nao` a cada resposta, até
chegar a uma folha — o palpite.

A pergunta de abertura *"É o Thor?"* (`PERGUNTA_DE_ABERTURA`, em `game.py`) fica
deliberadamente **fora** da árvore: assim ela é sempre a primeira pergunta,
qualquer que seja a base carregada do disco, e o aprendizado do jogo nunca a
desloca nem a apaga. Responder "sim" encerra a partida ali, sem alterar a base.
 Aprender é substituir aquela folha por uma nova
`Pergunta` cujos ramos são o animal novo e o palpite errado:

```
antes                depois

cachorro             ele tem casco?
                      ├── sim → tatu
                      └── não → cachorro
```

Os nós são *dataclasses* imutáveis (`frozen=True`), então aprender não altera a
árvore anterior: `aprender()` devolve uma árvore nova.

## Estrutura

```
sardinha/
├── __init__.py    # versão e reexportações
├── tree.py        # modelo da árvore, navegação, aprendizado e persistência JSON
├── game.py        # laço de interação com o jogador
├── cli.py         # entry point do comando "sardinha"
└── __main__.py    # suporte a "python -m sardinha"
tests/
├── test_tree.py   # inserção de nó, round-trip JSON, navegação
├── test_game.py   # laço de interação com entrada/saída simuladas
└── test_cli.py    # partida completa pela linha de comando
```

`tree.py` não contém `input()` nem `print()`: toda a conversa com o jogador vive
em `game.py`, e a entrada e a saída são injetáveis, o que permite testar uma
partida inteira sem terminal.

### Formato do arquivo

```json
{
  "tipo": "pergunta",
  "texto": "ele vive na água?",
  "sim": { "tipo": "folha", "animal": "baleia" },
  "nao": { "tipo": "folha", "animal": "cachorro" }
}
```

## Testes

```bash
pip install -e ".[dev]"
pytest
```

## Origem histórica

*Animal* é um dos jogos mais antigos e mais copiados da computação pessoal: um
programa que adivinha o animal em que você pensou e, ao errar, pede que você o
ensine — de modo que a base cresce com cada jogador. A ideia é anterior ao
microcomputador e circulou em minicomputadores antes de virar listagem de
revista.

Duas passagens costumam ser lembradas:

- A versão em BASIC publicada por David H. Ahl na coletânea *BASIC Computer
  Games* (Creative Computing, 1978), livro que levou dezenas desses programas
  para os micros domésticos. Foi assim que muita gente digitou o jogo linha por
  linha nos anos 1980.
- A versão para UNIVAC 1100 que, em 1975, foi distribuída junto com uma rotina
  que a copiava para outros diretórios do sistema — episódio citado com
  frequência como um dos primeiros programas autorreplicantes.

*Não verificado:* os créditos exatos de autoria e adaptação de cada versão
variam conforme a fonte, e este README não os afirma. Se você precisa da
atribuição precisa, confira diretamente a listagem do livro de Ahl.

Esta implementação não deriva de nenhum código original: é uma reescrita do
mecanismo (árvore de decisão que aprende com o jogador), com a piada final
no espírito das listagens em BASIC da época.

## Licença

MIT.
