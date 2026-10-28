# Abertura — Uma nova maré

Roteiro original para a versão Unreal; ainda não integrado ao jogo. A cena deve
ser jogável, com legendas em português e sem exigir dublagem. O jogador pode
avançar ou pular a parte cinematográfica, sem pular a leitura da carta nem criar
empresa automaticamente. Usar um perfil novo para testes e preservar saves antigos.

## 1. A chegada

O ônibus percorre devagar a rua da vila. Pela janela, o mar aparece entre as
casas; ao longe, o quiosque ainda está fechado. O veículo para. O protagonista
desce com sua mala e o ônibus parte. O controle passa ao jogador, que encontra
uma indicação discreta para a casa do avô.

Legenda: “Fazia tempo que eu não voltava. A vila parecia menor... e o mar,
exatamente do tamanho das minhas lembranças.”

## 2. A casa

O jogador abre a porta, entra e encontra um envelope sobre uma superfície
acessível. A casa preserva seus móveis e detalhes de praia. A porta funciona
normalmente, inclusive depois da sequência. Ao interagir, aparece a carta:

> Meu neto,
>
> Se você está lendo esta carta, chegou à nossa vila. Ainda me lembro de você
> pequeno, correndo pela areia enquanto eu abria o quiosque. Você dizia que o mar
> tinha cheiro de aventura. Eu respondia que também tinha cheiro de casa.
>
> Nosso negócio começou com um balcão, alguns cocos e a vontade de acolher quem
> chegava. Nem todos os dias foram fáceis. Quando o vento virou, foram as pessoas
> da vila que nos ajudaram a continuar. Cada cadeira guarda uma conversa; cada
> freguês deixou um pedacinho de sua história conosco.
>
> Hoje minhas mãos precisam descansar um pouco mais, mas o sonho da família ainda
> tem muito caminho pela frente. Quero passar o quiosque para você. Abra as portas,
> conheça nossos vizinhos e faça deste lugar também o seu lugar.
>
> Se puder, ajude o negócio a crescer. Mas lembre-se de que o que construímos de
> mais valioso nunca coube em uma caixa registradora: foi o carinho com que
> recebemos cada pessoa.
>
> Não tenha pressa. Mesmo de longe, vou torcer por você a cada nova maré.
>
> Com todo meu amor,
>
> Vô

Botão: **Guardar a carta**. Ela permanece disponível para releitura. O avô está
vivo; a história não pressupõe morte nem inventa uma despedida definitiva.

## 3. O primeiro dia

Ao guardar a carta, o jogador recebe o objetivo de conhecer o quiosque, criar seu
nome no celular e abrir a placa física. O quiosque começa fechado. Não avançar
automaticamente metas existentes nem conceder dinheiro, produtos ou expansões.
Os clientes chegam somente quando o negócio estiver aberto e no horário.

Legenda ao chegar: “Um balcão, alguns cocos e um sonho. É por aqui que começo.”

## Requisitos de implementação e teste

- A sequência só começa para um save realmente novo; saves anteriores sem a
  chave da introdução são tratados como existentes. Arquivo inválido nunca deve
  ser sobrescrito durante detecção. Registrar etapa e conclusão para retomada.
- Ônibus importado de ajanhallinta, CC0, sem interior: exige adaptação visual e
  solução convincente para desembarque antes de se considerar a cena pronta.
  Não fingir que existe animação de porta ou interior que não foi implementada.
- Não prender o jogador, a câmera, o mouse ou o controle ao pular, pausar,
  carregar ou fechar a carta. Verificar colisões e caminho até a porta da casa.
- Validar início, desembarque, carta, releitura, progressão, saves antigos,
  continuação após interrupção e funcionamento do objetivo no executável empacotado,
  em pasta de dados separada. Conferir imagens e áudio reais.

**Estado de implementação:** há um protótipo em C++ no projeto Unreal. A carta e a
cena ainda requerem acabamento visual e testes no executável; o ônibus importado
não tem interior nem porta animada. Consulte o checkpoint da varredura antes de
tratar a abertura como concluída.
