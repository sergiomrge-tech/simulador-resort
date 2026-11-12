# Personalização de tudo — plano (pedido de 01/11/2026)

Pedido do Sergio: "Para que um simulador seja um simulador, precisa ter personalização. Personalização
de tudo. 5 tipos de item de cada. Cada item com maior valor... mais detalhados, mais bonitos, para
tudo. No quiosque, nas expansões, no hotel... cama, sofá, armário, TV... piscina, tobogã... no mínimo
5 opções de cada."

## Regras de design

- **Cada objeto personalizável tem 5 níveis** (Simples → Bom → Caprichado → Luxo → Premium), cada um com
  modelo/material próprio, mais detalhado e bonito que o anterior, e preço crescente
  (base × 1, ×2,5, ×6, ×14, ×30).
- **Valor real no jogo, não só visual:** cada nível soma pontos de *Conforto* e *Beleza* ao local.
  - Quiosque: satisfação dos clientes, gorjeta e tempo de permanência sobem; fama +.
  - Casa: descanso melhor (energia), bônus de humor no dia seguinte.
  - Hotel/pousada: avaliação (estrelas), ocupação e diária (`HotelNight`) sobem.
  - Piscina/tobogã/praia: atratividade → mais visitantes e consumo no bar.
- **Onde comprar:** app *Personalizar* no celular (B), com abas por local e cartões com
  foto, preço, Conforto/Beleza; e **no próprio objeto**: mirar + E → "Trocar modelo" com prévia ao vivo
  (a prévia não cobra; confirmar cobra, devolve 30% do item anterior). Regra mantida da Godot:
  personalizar o quiosque só com ele fechado e sem clientes/louça.
- **Save:** `custom.<local>.<slot> = nível` (padrão 1 = o que existe hoje), compatível com saves antigos.
- **Assets:** Poly Haven (CC0) primeiro, Fab gratuito (CC BY / Standard, creditado) e Blender quando não
  houver; nada low poly. Cada item registrado em `CREDITS.md` e no catálogo de itens.

## Inventário (≈ 45 objetos × 5 = ≈ 225 itens)

| Local | Objetos personalizáveis |
|---|---|
| Quiosque | balcão, banquetas, mesas, cadeiras, guarda-sóis, luminárias, placa/letreiro, quadro de cardápio, geladeira/expositor, piso/deck, plantas, decoração de parede |
| Casa | cama, sofá, armário, TV, mesa de jantar, cadeiras, tapete, luminárias, cozinha, chuveiro/banheiro, quadros |
| Praia / quiosque externo | espreguiçadeiras, guarda-sóis de praia, redes, tochas/postes, deck |
| Piscina (pousada e hotel) | espreguiçadeiras, guarda-sóis, bar da piscina, tobogã (cores/forma), luzes da piscina, borda/piso |
| Hotel | recepção (balcão), sofás e poltronas do lobby, mesas de centro, luminárias, plantas, quadros, restaurante (mesas/cadeiras), academia (aparelhos), **quartos** (cama, armário, TV, banheiro) |
| Expansões (pousada, bar, sorveteria, aluguel, surfe, food truck, souvenir) | balcão/fachada, assentos, letreiro, decoração |

## Fases (cada uma jogável e validada antes da próxima)

1. **Sistema** (C++): catálogo de dados `Content/Data/customization.json`, troca de malha/material por
   slot em tempo real, compra/prévia/reembolso, save, efeitos de Conforto/Beleza, app no celular e "E no
   objeto". Teste automático cobrindo compra, prévia sem cobrança, reembolso, save/load e efeito.
2. **Quiosque** completo (12 objetos × 5).
3. **Casa** (11 objetos × 5).
4. **Praia, piscina e tobogã.**
5. **Hotel** (lobby, restaurante, academia) e **quartos com interior** (hoje a torre é só fachada).
6. **Expansões/negócios.**

Pendências ligadas: biquíni/sunga exigem restaurar o corpo completo dos personagens (UBC Quaternius CC0).
