# Auditoria de tamanho das traduções — Pacote 5

Referência editorial: 07/11/2026; base `2bea4d2d`. Fontes em `unreal/MareAlta/Content/Localization/Mare/`. Nenhuma chave ou tradução foi alterada.

## Método e limites

Foram comparadas **4064 entradas por idioma**, incluindo 113 LOCTEXT e 3951 strings. O gatilho exige simultaneamente **mais de 30% e mais de 25 caracteres extras**. Conta-se NFC visível: `<br>` vale uma quebra; outras tags não contam; espaços e marcadores continuam contando. Ordenação: caracteres extras decrescentes, razão decrescente, seção e chave.

Cada lista contém até os **50 piores** que realmente atingem ambos os limites. Nenhum idioma possui 50 casos; não foram inventados candidatos para completar a lista. O JSON irmão guarda todos os casos e hashes SHA-256. `I18N_SUGESTOES_CURTAS.json` guarda as propostas completas, separadas dos catálogos do jogo.

Comprimento é triagem, não teste de recorte. Os locais indicados como botão/cartão são hipóteses pelo texto, não inspeção do widget. O Claude precisa medir fonte, escala, placeholders expandidos e quebras em 1280×720 e 1920×1080, teclado/controle, e verificar celular vertical com texto grande. Zero casos em japonês/chinês/coreano não prova que cabem: caracteres de largura dupla exigem inspeção. As versões curtas são sugestões editoriais; revisão nativa e teste visual continuam pendentes.

## Resultado por idioma

| Idioma | Entradas | Acima dos dois limites | Exibidas | Faltantes | Marcadores divergentes |
|---|---:|---:|---:|---:|---:|
| de | 4064 | 19 | 19 | 0 | 0 |
| en | 4064 | 2 | 2 | 0 | 0 |
| es | 4064 | 0 | 0 | 0 | 0 |
| fr | 4064 | 25 | 25 | 0 | 0 |
| it | 4064 | 11 | 11 | 0 | 0 |
| ja | 4064 | 0 | 0 | 0 | 0 |
| ko | 4064 | 0 | 0 | 0 | 0 |
| nl | 4064 | 3 | 3 | 0 | 0 |
| pl | 4064 | 2 | 2 | 0 | 0 |
| pt-PT | 4064 | 0 | 0 | 0 | 0 |
| ru | 4064 | 1 | 1 | 0 | 0 |
| zh-Hans | 4064 | 0 | 0 | 0 | 0 |

## de

Arquivo: `unreal/MareAlta/Content/Localization/Mare/de.json`. **19 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | Cem. Contei com a régua do meu avô, que media tudo em palmos. Deu muitos palmos. | Hundert. Ich hab's mit dem Lineal meines Großvaters gemessen, der alles in Handspannen maß. Es kamen sehr viele Handspannen heraus. | 80 → 131; +51, +63.7% | Hundert. Opas Lineal maß in Handspannen. Das waren viele Handspannen. | 69 | cartão/aviso: conferir largura no celular |
| 2 / strings | Segure o sabor (clique, 1 a 6 ou A) e solte no verde · setas escolhem o pote · Enter entrega · Esc ou B sai | Halte die Geschmackswahl gedrückt (Klick, 1 bis 6 oder A) und lass im grünen Bereich los · Pfeile wählen den Behälter · Enter liefert · Esc oder B beendet | 107 → 154; +47, +43.9% | Sorte halten (Klick, 1–6 oder A), im Grün loslassen · Pfeile: Becher · Enter: servieren · Esc/B: raus | 101 | cartão/aviso: conferir largura no celular |
| 3 / strings | Seríssimo. Em 1987 esqueceram uma vez e a Onda levou a praia, o bar e o meu bigode. O bigode nunca mais cresceu igual. | Todernst. 1987 haben sie es einmal vergessen, und die Welle hat den Strand, die Bar und meinen Schnurrbart mitgenommen. Der Schnurrbart ist nie wieder so gewachsen. | 118 → 164; +46, +39.0% | Todernst. 1987 vergaßen sie es: Die Welle nahm Strand, Bar und Schnurrbart mit. Der wuchs nie wieder gleich. | 108 | cartão/aviso: conferir largura no celular |
| 4 / strings | Ops, essa dobra fora de ordem amassou o papel. Pode seguir ou pegar papel novo. | Hoppla, diese Falte in falscher Reihenfolge hat das Papier zerknittert. Du kannst weitermachen oder neues Papier nehmen. | 79 → 120; +41, +51.9% | Hoppla, falsch gefaltet: Papier zerknittert. Weiter oder neues Papier nehmen. | 77 | cartão/aviso: conferir largura no celular |
| 5 / strings | Um crítico de comida vem aí. Dizem que ele já fez um chef chorar só olhando para um pastel. Capriche nas receitas. | Ein Gastrokritiker ist unterwegs. Angeblich hat er einen Koch zum Weinen gebracht, nur indem er einen Pastel angesehen hat. Gib dir Mühe mit den Rezepten. | 114 → 154; +40, +35.1% | Ein Gastrokritiker kommt. Ein Blick auf einen Pastel brachte einen Koch zum Weinen. Gib dir Mühe! | 97 | cartão/aviso: conferir largura no celular |
| 6 / strings | Lembra do robalo? Pensei melhor: tinha uns cinco quilos. Quase me puxou do barco. | Erinnerst du dich an den Wolfsbarsch? Ich habe nachgedacht: Er hatte so fünf Kilo. Hätte mich fast aus dem Boot gezogen. | 81 → 120; +39, +48.1% | Der Wolfsbarsch? Eher fünf Kilo. Hätte mich fast aus dem Boot gezogen. | 70 | cartão/aviso: conferir largura no celular |
| 7 / strings | Volta amanhã. E traz coco gelado, que o de ontem chegou morno. O vulcão reclamou. Eu também. | Komm morgen wieder. Und bring eine eiskalte Kokosnuss mit, die von gestern kam lauwarm an. Der Vulkan hat sich beschwert. Ich auch. | 92 → 131; +39, +42.4% | Komm morgen mit kalter Kokosnuss. Gestern war sie lauwarm. Der Vulkan meckerte. Ich auch. | 89 | cartão/aviso: conferir largura no celular |
| 8 / strings | Compre peças dos artesãos e arrume a prateleira: a vitrine vende mais. Embrulhe na ordem certa com a fita pedida. | Kaufe Stücke von Kunsthandwerkern und fülle das Regal: Die Auslage steigert den Verkauf. Verpacke in der richtigen Reihenfolge mit dem gewünschten Band. | 113 → 152; +39, +34.5% | Handwerk kaufen, Regal füllen: Die Auslage verkauft mehr. Richtig falten, gewünschtes Band wählen. | 98 | cartão/aviso: conferir largura no celular |
| 9 / strings | Solte aqui o ingrediente da mão. Com tudo no copo, faça o passo pedido (socar, bater ou liquidificar) e sirva. | Lege die Zutat aus deiner Hand hier ab. Wenn alles im Glas ist, führe den verlangten Schritt aus (zerdrücken, schütteln oder mixen) und serviere. | 110 → 145; +35, +31.8% | Zutat hier ablegen. Alles im Glas? Wie verlangt zerdrücken, schütteln oder mixen, dann servieren. | 97 | cartão/aviso: conferir largura no celular |
| 10 / strings | A garoupa, sabe? Eram trinta quilos e ela falava. Pediu pra eu soltar e eu soltei, por educação. | Der Zackenbarsch, weißt du? Dreißig Kilo, und er konnte sprechen. Er bat mich, ihn freizulassen, und ich tat es, aus Höflichkeit. | 96 → 129; +33, +34.4% | Der Zackenbarsch? Dreißig Kilo, konnte sprechen! Bat um Freiheit. Ich ließ ihn höflich frei. | 92 | cartão/aviso: conferir largura no celular |
| 11 / strings | Dormir fecha o dia: salários são pagos, o jogo é salvo e o celular mostra o resumo e a previsão de amanhã. | Schlafen beendet den Tag: Löhne werden gezahlt, das Spiel wird gespeichert und das Handy zeigt die Übersicht und die Vorhersage für morgen. | 106 → 139; +33, +31.1% | Schlafen: Löhne zahlen, speichern. Am Handy: Tagesbilanz und Wetter für morgen. | 79 | cartão/aviso: conferir largura no celular |
| 12 / strings | Segure E, Espaço, clique ou A para bater e solte no verde · passou, derramou | Halte E, Leertaste, Mausklick oder A zum Mixen und lass im grünen Bereich los · zu spät bedeutet verschüttet | 76 → 108; +32, +42.1% | E, Leertaste, Klick oder A halten, im Grün loslassen · zu spät: verschüttet | 75 | cartão/aviso: conferir largura no celular |
| 13 / strings | Pinball do Farol: Espaço lança a bola, A e D (ou Shift esquerdo e direito) batem os flippers. | Leuchtturm-Flipper: Die Leertaste startet die Kugel; A und D (oder linke und rechte Umschalttaste) bewegen die Flipperhebel. | 93 → 124; +31, +33.3% | Leuchtturm-Flipper: Leertaste startet; A/D oder linke/rechte Shift-Taste: Flipperhebel. | 87 | cartão/aviso: conferir largura no celular |
| 14 / strings | Vovó Dilce mandou um áudio de sete minutos. Resumo: está muito orgulhosa e quer o quarto com vista. | Oma Dilce hat eine siebenminütige Sprachnachricht geschickt. Zusammenfassung: Sie ist sehr stolz und will das Zimmer mit Aussicht. | 99 → 130; +31, +31.3% | Oma Dilce schickte sieben Minuten Audio: sehr stolz, will ein Zimmer mit Aussicht. | 82 | cartão/aviso: conferir largura no celular |
| 15 / strings | Anote o pedido, pegue o prato pronto no passe da cozinha e sirva. Rapidez rende gorjeta. | Nimm die Bestellung auf, hol das fertige Gericht an der Küchenausgabe und serviere es. Schnelligkeit bringt Trinkgeld. | 88 → 118; +30, +34.1% | Bestellung aufnehmen, fertiges Gericht an der Küchenausgabe holen, servieren. Schnell sein bringt Trinkgeld. | 108 | cartão/aviso: conferir largura no celular |
| 16 / strings | Meu avô dizia: errar é humano, desperdiçar cachaça é crime. | Mein Opa sagte immer: Irren ist menschlich, cachaça zu verschwenden ist ein Verbrechen. | 59 → 87; +28, +47.5% | Opa sagte: Irren ist menschlich, Cachaça verschwenden ein Verbrechen. | 69 | cartão/aviso: conferir largura no celular |
| 17 / strings | Seu Tibúrcio: "Trinta anos sem descer esse morro. A trilha encolheu ou fui eu que cresci?" | Seu Tibúrcio: „Dreißig Jahre nicht von diesem Berg heruntergekommen. Ist der Pfad geschrumpft oder bin ich gewachsen?“ | 90 → 118; +28, +31.1% | Seu Tibúrcio: „30 Jahre nicht vom Berg runter. Ist der Pfad geschrumpft oder ich gewachsen?“ | 92 | cartão/aviso: conferir largura no celular |
| 18 / strings | Cuida de todo o quiosque: anota pedidos, entrega produtos prontos, recebe e recolhe a louça. | Kümmert sich um den ganzen Kiosk: nimmt Bestellungen auf, gibt fertige Produkte aus, kassiert und räumt das Geschirr ab. | 92 → 120; +28, +30.4% | Betreut den Kiosk: Bestellungen, fertige Produkte, Zahlung und Geschirr. | 72 | cartão/aviso: conferir largura no celular |
| 19 / strings | (converse com quem pediu para avançar) | (sprich mit der Person, die darum gebeten hat, um weiterzukommen) | 38 → 65; +27, +71.1% | (zum Fortfahren mit dem Auftraggeber reden) | 43 | texto curto: conferir botão/cartão no contexto |

## en

Arquivo: `unreal/MareAlta/Content/Localization/Mare/en.json`. **2 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | Cem. Contei com a régua do meu avô, que media tudo em palmos. Deu muitos palmos. | A hundred. I measured with my grandpa's ruler, which measured everything in hand spans. It came to a lot of hand spans. | 80 → 119; +39, +48.8% | A hundred. Grandpa measured in hand spans. His ruler counted plenty of those. | 77 | cartão/aviso: conferir largura no celular |
| 2 / strings | Antes de subir, dê água e protetor a cada um. Quem sobe sem isso cansa e reclama. | Before heading up, give everyone water and sunscreen. Anyone who goes without them gets tired and complains. | 81 → 108; +27, +33.3% | Give everyone water and sunscreen before climbing. Without them, they tire and complain. | 88 | cartão/aviso: conferir largura no celular |

## es

Nenhuma entrada ultrapassa simultaneamente os dois limites. Manter teste visual; não significa ausência de risco em botões curtos.


## fr

Arquivo: `unreal/MareAlta/Content/Localization/Mare/fr.json`. **25 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | Escolha o recheio, arraste para fechar a borda e frite até dourar: olhe a cor e ouça o sinal. Caldo de cana na moenda. | Choisissez la garniture, faites glisser pour fermer le bord et faites frire jusqu'à ce qu'il soit doré : regardez la couleur et écoutez le signal. Jus de canne à la presse. | 118 → 172; +54, +45.8% | Choisissez la farce, glissez pour sceller, puis faites dorer : couleur et son vous guident. Pressez la canne pour le jus. | 121 | cartão/aviso: conferir largura no celular |
| 2 / strings | Misture no copo da bancada para descobrir receitas novas (cada uma dá fama). | Mélangez les ingrédients dans le verre au comptoir pour découvrir de nouvelles recettes (chacune donne de la renommée). | 76 → 119; +43, +56.6% | Mélangez au comptoir : chaque recette découverte rapporte de la renommée. | 73 | cartão/aviso: conferir largura no celular |
| 3 / strings | A planta está na praia a leste do hotel, perto do farol: E em cada peça transparente para montar antes dos convidados. | Le plan se trouve sur la plage à l'est de l'hôtel, près du phare : appuyez sur E devant chaque élément transparent pour l'installer avant l'arrivée des invités. | 118 → 160; +42, +35.6% | Plage à l’est de l’hôtel, près du phare : E sur chaque pièce transparente. Montez tout avant les invités. | 105 | cartão/aviso: conferir largura no celular |
| 4 / loctext | Começar um novo jogo no slot {0}? O progresso atual desse slot fica guardado só como backup (.bak). | Commencer une nouvelle partie sur l'emplacement {0} ? La progression actuelle de cet emplacement sera seulement gardée en sauvegarde (.bak). | 99 → 140; +41, +41.4% | Nouvelle partie, emplacement {0} ? La progression actuelle ne restera qu’en copie (.bak). | 89 | cartão/aviso: conferir largura no celular |
| 5 / strings | Pegue um ingrediente por vez e leve ao copo. A ordem não importa, só a mistura certa. | Prenez un ingrédient à la fois et mettez-le dans le verre. L'ordre n'a pas d'importance, seule la bonne combinaison compte. | 85 → 123; +38, +44.7% | Un ingrédient à la fois dans le verre. Seul le mélange compte, pas l’ordre. | 75 | cartão/aviso: conferir largura no celular |
| 6 / strings | Nos quartos 301, 302 e 303, resolver pessoalmente (E no quarto) é de graça e dá fama. | Dans les chambres 301, 302 et 303, résoudre le problème vous-même (E dans la chambre) est gratuit et donne de la renommée. | 85 → 122; +37, +43.5% | Chambres 301–303 : réglez le problème sur place (E), gratuitement, avec gain de renommée. | 89 | cartão/aviso: conferir largura no celular |
| 7 / strings | O guia contratado faz o passeio sozinho com nota 3, sem gorjeta. Indo junto, a nota, a gorjeta e a fama sobem. | Le guide engagé mène seul l'excursion avec une note de 3, sans pourboire. En l'accompagnant, vous augmentez la note, les pourboires et la renommée. | 110 → 147; +37, +33.6% | Guide seul : note 3, sans pourboire. Accompagnez-le pour gagner note, pourboire et renommée. | 92 | cartão/aviso: conferir largura no celular |
| 8 / strings | Negocie a diária dos hóspedes do hotel como na pousada. Quem você não atender em 2 horas, a equipe recebe pela oferta. | Négociez le prix de la nuit des clients de l'hôtel comme à la pension. Ceux que vous ne servez pas en 2 heures, l'équipe les accueille à leur prix proposé. | 118 → 155; +37, +31.4% | Négociez les nuitées comme à la pension. Après 2 h sans réponse, l’équipe accepte l’offre du client. | 100 | cartão/aviso: conferir largura no celular |
| 9 / strings | Motor forte: o pulso certo fica mais fácil e o batido rende mais gorjeta. | Moteur puissant : il est plus facile de trouver le bon rythme et les cocktails rapportent plus de pourboires. | 73 → 109; +36, +49.3% | Moteur puissant : rythme plus facile, cocktails plus généreux en pourboires. | 76 | cartão/aviso: conferir largura no celular |
| 10 / strings | As fotos do seu álbum (tecla P) viram cartões-postais: com o farol, a baleia ou o pôr do sol vendem mais caro. | Les photos de votre album (touche P) deviennent des cartes postales : celles du phare, de la baleine ou du coucher de soleil se vendent plus cher. | 110 → 146; +36, +32.7% | Photos (P) en cartes postales : phare, baleine et coucher de soleil se vendent plus cher. | 89 | cartão/aviso: conferir largura no celular |
| 11 / strings | Cem. Contei com a régua do meu avô, que media tudo em palmos. Deu muitos palmos. | Cent. Je les ai mesurés avec la règle de mon grand-père, qui mesurait tout en empans. Ça faisait beaucoup d'empans. | 80 → 115; +35, +43.8% | Cent. La règle de mon grand-père mesurait tout en empans. Beaucoup d’empans ! | 77 | cartão/aviso: conferir largura no celular |
| 12 / strings | Dormir fecha o dia: salários são pagos, o jogo é salvo e o celular mostra o resumo e a previsão de amanhã. | Dormir clôt la journée : les salaires sont payés, la partie est sauvegardée et le téléphone affiche le résumé et les prévisions du lendemain. | 106 → 141; +35, +33.0% | Dormir : salaires payés, partie sauvée. Bilan et météo de demain sur le téléphone. | 82 | cartão/aviso: conferir largura no celular |
| 13 / strings | Uma revista de viagem quer o resort na capa. O fotógrafo avisou que só fotografa "coisa bonita". Personalize a vila. | Un magazine de voyage veut le resort en couverture. Le photographe a prévenu qu'il ne photographie que les « belles choses ». Personnalisez le village. | 116 → 151; +35, +30.2% | Un magazine veut le resort en couverture. Le photographe ne prend que le « beau ». Décorez le village. | 102 | cartão/aviso: conferir largura no celular |
| 14 / loctext | Clique numa ação e aperte a nova tecla (Esc cancela). Se a tecla já estiver em uso, as duas ações trocam. | Cliquez sur une action puis appuyez sur la nouvelle touche (Échap annule). Si la touche est déjà utilisée, les deux actions sont échangées. | 105 → 139; +34, +32.4% | Cliquez sur l’action, puis appuyez sur la touche (Échap annule). Touche déjà prise ? Les actions s’échangent. | 109 | cartão/aviso: conferir largura no celular |
| 15 / strings | Os produtos já vêm prontos: pegue o que o cliente pediu. Quando acabar, reponha pelo celular ou aqui mesmo. | Les produits arrivent déjà prêts : prenez ce que le client a commandé. Quand il n'y en a plus, réapprovisionnez sur le téléphone ou ici même. | 107 → 141; +34, +31.8% | Produits prêts : prenez la commande. À court ? Réapprovisionnez ici ou sur le téléphone. | 88 | cartão/aviso: conferir largura no celular |
| 16 / strings | {0}: os convidados chegaram e quase nada estava montado ({1} de {2}). Ficou só o sinal, R$ {3}, e a fama caiu. | {0} : les invités sont arrivés et presque rien n'était installé ({1} sur {2}). Seul l'acompte de R$ {3} a été conservé, et la renommée a baissé. | 110 → 144; +34, +30.9% | {0} : invités arrivés, presque rien monté ({1}/{2}). Acompte seul : R$ {3}. Renommée en baisse. | 95 | cartão/aviso: conferir largura no celular |
| 17 / strings | O cooler está sem picolé: a sorveteria repõe a cada hora aberta. | Plus de glaces à l'eau dans la glacière : le glacier la réapprovisionne chaque heure d'ouverture. | 64 → 97; +33, +51.6% | Plus de glaces dans la glacière ! Le glacier la remplit chaque heure d’ouverture. | 81 | cartão/aviso: conferir largura no celular |
| 18 / strings | Ops, essa dobra fora de ordem amassou o papel. Pode seguir ou pegar papel novo. | Oups, ce pli fait dans le désordre a froissé le papier. Vous pouvez continuer ou prendre une nouvelle feuille. | 79 → 110; +31, +39.2% | Oups, mauvais pli : papier froissé. Continuez ou prenez une feuille neuve. | 74 | cartão/aviso: conferir largura no celular |
| 19 / strings | Dona Cecília quer resgatar as receitas da avó e levar comida boa até a rua principal. | Dona Cecília veut retrouver les recettes de sa grand-mère et apporter de la bonne cuisine jusqu'à la rue principale. | 85 → 116; +31, +36.5% | Dona Cecília veut faire revivre les recettes de sa grand-mère dans la rue principale. | 85 | cartão/aviso: conferir largura no celular |
| 20 / strings | Menor? Impossível. Peixe de história só cresce, nunca diminui. | Plus petit ? Impossible. Les poissons des histoires ne font que grandir, jamais rapetisser. | 62 → 91; +29, +46.8% | Plus petit ? Impossible ! Un poisson de légende ne fait que grandir. | 68 | cartão/aviso: conferir largura no celular |
| 21 / strings | Lojinha: a prateleira está vazia! Compre artesanato e arrume a vitrine. | Boutique de souvenirs : l'étagère est vide ! Achetez des objets artisanaux et remplissez la vitrine. | 71 → 100; +29, +40.8% | Boutique : étagère vide ! Achetez de l’artisanat, remplissez la vitrine. | 72 | cartão/aviso: conferir largura no celular |
| 22 / strings | (no nível "Pôr do sol no mar" abre o passeio de jangada no fim da tarde) | (au niveau « Coucher de soleil en mer », la sortie en jangada devient disponible en fin d'après-midi) | 72 → 101; +29, +40.3% | (niveau « Coucher de soleil en mer » : jangada en fin d’après-midi) | 67 | cartão/aviso: conferir largura no celular |
| 23 / strings |  (no nível "Pôr do sol no mar" abre o passeio de jangada no fim da tarde) |  (au niveau « Coucher de soleil en mer », la sortie en jangada devient disponible en fin d'après-midi) | 73 → 102; +29, +39.7% |  (niveau « Coucher de soleil en mer » : jangada en fin d’après-midi) | 68 | cartão/aviso: conferir largura no celular |
| 24 / strings | Antes de subir, dê água e protetor a cada um. Quem sobe sem isso cansa e reclama. | Avant de monter, donnez de l'eau et de la crème solaire à chacun. Sans cela, ils se fatiguent et se plaignent. | 81 → 110; +29, +35.8% | Avant de monter : eau et crème solaire pour tous. Sans elles, fatigue et plaintes. | 82 | cartão/aviso: conferir largura no celular |
| 25 / strings | Chegamos bem na hora do pôr do sol! | Nous sommes arrivés juste à temps pour le coucher du soleil ! | 35 → 61; +26, +74.3% | Juste à temps pour le coucher du soleil ! | 41 | texto curto: conferir botão/cartão no contexto |

## it

Arquivo: `unreal/MareAlta/Content/Localization/Mare/it.json`. **11 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | Ofereça os extras que o grupo quer (criança pede colete, quem chega com fome quer lanche, primeira vez quer foto): rende mais e sobe a nota. Insistir no que não querem baixa a nota. | Offri gli extra che il gruppo desidera (i bambini chiedono il giubbotto salvagente, chi ha fame vuole uno spuntino, chi è alla prima esperienza vuole una foto): guadagni di più e il voto sale. Insistere su cose indesiderate abbassa il voto. | 181 → 240; +59, +32.6% | Offri gli extra richiesti: giubbotto ai bimbi, spuntino agli affamati, foto ai nuovi. Più incassi e voto migliore; insistere su altro lo abbassa. | 145 | cartão/diálogo: quebra e rolagem |
| 2 / strings | Seríssimo. Em 1987 esqueceram uma vez e a Onda levou a praia, o bar e o meu bigode. O bigode nunca mais cresceu igual. | Serissimo. Nel 1987 se ne sono dimenticati una volta e l'Onda si è portata via la spiaggia, il bar e i miei baffi. I baffi non sono più ricresciuti uguali. | 118 → 155; +37, +31.4% | Serissimo. Nel 1987 lo scordarono: l’Onda portò via spiaggia, bar e baffi. Non ricrebbero più uguali. | 101 | cartão/aviso: conferir largura no celular |
| 3 / strings | Mova o mouse para posicionar a raquete; o golpe sai sozinho quando a bola chega. Q sai da partida. | Muovi il mouse per posizionare la racchetta; il colpo parte automaticamente quando arriva la palla. Premi Q per uscire dalla partita. | 98 → 133; +35, +35.7% | Muovi il mouse: la racchetta colpisce da sola quando arriva la palla. Q esce. | 77 | cartão/aviso: conferir largura no celular |
| 4 / strings | Cem. Contei com a régua do meu avô, que media tudo em palmos. Deu muitos palmos. | Cento. Li ho misurati con il righello di mio nonno, che misurava tutto in spanne. Sono venute un sacco di spanne. | 80 → 113; +33, +41.3% | Cento. Il righello del nonno misurava a spanne. Tante spanne! | 61 | cartão/aviso: conferir largura no celular |
| 5 / strings | Dormir fecha o dia: salários são pagos, o jogo é salvo e o celular mostra o resumo e a previsão de amanhã. | Dormire chiude la giornata: si pagano gli stipendi, la partita viene salvata e il cellulare mostra il riepilogo e le previsioni di domani. | 106 → 138; +32, +30.2% | Dormire: stipendi pagati, partita salvata. Sul cellulare: riepilogo e meteo di domani. | 86 | cartão/aviso: conferir largura no celular |
| 6 / strings | O cooler está sem picolé: a sorveteria repõe a cada hora aberta. | Il frigo portatile ha finito i ghiaccioli: la gelateria lo rifornisce a ogni ora di apertura. | 64 → 93; +29, +45.3% | Ghiaccioli finiti! La gelateria riempie il frigo a ogni ora di apertura. | 72 | cartão/aviso: conferir largura no celular |
| 7 / strings | Na rua principal. Funciona até tarde e bomba nas festas. | Nella via principale. Resta aperto fino a tardi e va a gonfie vele durante le feste. | 56 → 84; +28, +50.0% | In via principale, aperto fino a tardi. Fa il pienone alle feste. | 65 | cartão/aviso: conferir largura no celular |
| 8 / strings | Balançaram tanto que fiquei enjoado. | L’abbiamo fatta oscillare così tanto che mi è venuta la nausea. | 36 → 63; +27, +75.0% | Avete dondolato tanto da farmi venire la nausea. | 48 | texto curto: conferir botão/cartão no contexto |
| 9 / strings | Folhas na água espantam os banhistas e baixam as estrelas. O piscineiro limpa sozinho. | Le foglie in acqua fanno scappare i bagnanti e abbassano le stelle. Il manutentore della piscina pulisce da solo. | 86 → 113; +27, +31.4% | Foglie in acqua: meno bagnanti e stelle. L’addetto alla piscina pulisce da solo. | 80 | cartão/aviso: conferir largura no celular |
| 10 / strings |  Faltou picolé para {0}: o cooler esvaziou. |  Sono mancati i ghiaccioli per {0}: il frigo portatile si è svuotato. | 43 → 69; +26, +60.5% |  Ghiaccioli finiti per {0}: frigo vuoto. | 40 | texto curto: conferir botão/cartão no contexto |
| 11 / strings | Misture no copo da bancada para descobrir receitas novas (cada uma dá fama). | Mescola gli ingredienti nel bicchiere sul bancone per scoprire nuove ricette (ognuna aumenta la fama). | 76 → 102; +26, +34.2% | Mescola nel bicchiere al bancone: ogni ricetta scoperta dà fama. | 64 | cartão/aviso: conferir largura no celular |

## ja

Nenhuma entrada ultrapassa simultaneamente os dois limites. Manter teste visual; não significa ausência de risco em botões curtos.


## ko

Nenhuma entrada ultrapassa simultaneamente os dois limites. Manter teste visual; não significa ausência de risco em botões curtos.


## nl

Arquivo: `unreal/MareAlta/Content/Localization/Mare/nl.json`. **3 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | A planta está na praia a leste do hotel, perto do farol: E em cada peça transparente para montar antes dos convidados. | De plattegrond ligt op het strand ten oosten van het hotel, bij de vuurtoren: druk op E bij elk doorzichtig onderdeel om het op te bouwen voordat de gasten aankomen. | 118 → 165; +47, +39.8% | Strand oostelijk van het hotel, bij de vuurtoren: E op elk doorzichtig deel. Bouw alles vóór de gasten komen. | 109 | cartão/aviso: conferir largura no celular |
| 2 / strings | Dormir fecha o dia: salários são pagos, o jogo é salvo e o celular mostra o resumo e a previsão de amanhã. | Slapen sluit de dag af: lonen worden betaald, het spel wordt opgeslagen en de telefoon toont het overzicht en de voorspelling voor morgen. | 106 → 138; +32, +30.2% | Slapen: lonen betalen en opslaan. Op je telefoon: dagoverzicht en het weer voor morgen. | 87 | cartão/aviso: conferir largura no celular |
| 3 / strings | A lenda da ilha vulcânica arrepiou! | De legende van het vulkanische eiland bezorgde ons kippenvel! | 35 → 61; +26, +74.3% | De vulkaanlegende gaf ons kippenvel! | 36 | texto curto: conferir botão/cartão no contexto |

## pl

Arquivo: `unreal/MareAlta/Content/Localization/Mare/pl.json`. **2 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | O cooler está sem picolé: a sorveteria repõe a cada hora aberta. | W lodówce turystycznej nie ma lodów na patyku: lodziarnia uzupełnia zapas co godzinę otwarcia. | 64 → 94; +30, +46.9% | Brak lodów na patyku! Lodziarnia napełnia lodówkę co godzinę otwarcia. | 70 | cartão/aviso: conferir largura no celular |
| 2 / strings | Segure E, Espaço, clique ou A para bater e solte no verde · passou, derramou | Przytrzymaj E, Spację, kliknięcie lub A, aby wstrząsać, i puść na zielonym · za długo oznacza rozlanie | 76 → 102; +26, +34.2% | Trzymaj E, Spację, klik lub A; puść na zielonym · za długo: rozlanie | 68 | cartão/aviso: conferir largura no celular |

## pt-PT

Nenhuma entrada ultrapassa simultaneamente os dois limites. Manter teste visual; não significa ausência de risco em botões curtos.


## ru

Arquivo: `unreal/MareAlta/Content/Localization/Mare/ru.json`. **1 de até 50** casos.

| # / seção | pt-BR | Tradução atual | pt → idioma / acréscimo | Versão curta sugerida | Tamanho curto | Risco |
|---|---|---|---|---|---:|---|
| 1 / strings | Segure E, Espaço, clique ou A para bater e solte no verde · passou, derramou | Удерживайте E, пробел, щелчок или A для взбивания и отпустите в зелёной зоне · передержите — прольётся | 76 → 102; +26, +34.2% | Держите E, пробел, кнопку мыши или A; отпустите на зелёном · позже — прольёте | 77 | cartão/aviso: conferir largura no celular |

## zh-Hans

Nenhuma entrada ultrapassa simultaneamente os dois limites. Manter teste visual; não significa ausência de risco em botões curtos.


## Suplemento: largura estimada em coreano

Os dois casos abaixo **não** atingem o corte por número de caracteres. A largura estimada Unicode os sinalizou porque Hangul ocupa mais espaço. A contagem de células não substitui a fonte da Unreal.

| pt-BR | Coreano atual | Sugestão em coreano |
|---|---|---|
| E o vulcão... está soltando fogos? Seu Tibúrcio: "Ele adora festa. Quem não adora?" | 그런데 화산이... 불꽃놀이를 하고 있어? Seu Tibúrcio: "저 녀석은 축제를 좋아해. 안 좋아하는 사람이 어디 있어?" | 화산이 불꽃놀이를? Seu Tibúrcio: "축제를 좋아하거든. 누가 싫어하겠어?" |
| {0} reclamou: multa sem amassado nenhum! A fama caiu. | {0}이(가) 항의했습니다: 찌그러짐도 없는데 벌금을 받았어요! 명성이 떨어졌습니다. | {0}의 항의: 흠집도 없는데 벌금이라니! 명성이 하락했습니다. |

## Aplicação pelo Claude

1. Confirmar o local real da string. Não aplicar texto curto de diálogo a uma instrução diferente.
2. Manter as chaves pt-BR. Alterar valores traduzidos só depois da revisão e propagar futuras mudanças do português nos 12 idiomas.
3. Preservar `{0}`, `{1}`, `%d`, `%.1f`, R$, números, atalhos e espaços dos fragmentos. Não reduzir texto cortando no meio nem removendo instruções de segurança ou custo.
4. Usar quebra/rolagem nos diálogos longos, dimensionar botões ao conteúdo e testar valores máximos. Não diminuir todas as fontes para esconder problemas.

## Reprodução

```sh
python tools/ue58/i18n_length_audit.py --self-test
python tools/ue58/i18n_length_audit.py --output docs/ue58/I18N_TAMANHO.json --suggestions docs/ue58/I18N_SUGESTOES_CURTAS.json --report docs/ue58/REVISAO_TRADUCOES_TAMANHO.md
```
