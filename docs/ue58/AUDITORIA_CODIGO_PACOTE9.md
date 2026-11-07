# Pacote 9 — auditoria estática do C++ (somente leitura)

**Base:** `0ba71c4cd15d23a5007edfb7f142f6dfa98f263f` · 07/11/2026. **Não houve compilação, PIE, medição de FPS nem correção em Source.** Os diffs abaixo são propostas para Claude. Prioridade P0 = bloquear demo; P1 = afetar experiência; P2 = endurecimento de dados/robustez. Conferir linhas novamente depois de outros merges.

## 1. P0 — lista de estações do rádio não corresponde ao leitor C++

**Fonte:** `unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp:27-42`; dado `unreal/MareAlta/Content/Data/radio.json:2-28`.

**Cenário reproduzível:** `radio.json` define cada estação como array `["radio_havaiana", "Aloha FM · havaiana"]`, mas `RadioStations()` e `RadioName()` fazem `V->AsObject()` e procuram `id`/`name`. Para elementos array, `AsObject()` não produz o objeto esperado; os IDs viram nomes vazios. Como o array `Stations` ganha elementos, o fallback de lista vazia também não é aplicado. Resultado esperado: rádio sem faixa válida, nomes errados e navegação quebrada no celular e nos aparelhos. **Gravidade: crítica, bloqueia a demo.**

**Diff proposto (aceitar formatos antigo e atual, validar IDs e não incluir entradas vazias):**

```diff
--- a/unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp
@@ RadioStations()
-   if(RadioDefs()->TryGetArrayField(TEXT("stations"),List))for(const auto& V:*List)Stations.Add(FName(UMareSimulation::String(V->AsObject(),TEXT("id"))));
+   if(RadioDefs()->TryGetArrayField(TEXT("stations"),List))for(const auto& V:*List){
+    FString Id;
+    if(V.IsValid() && V->Type==EJson::Array){
+     const auto& Pair=V->AsArray();
+     if(Pair.Num()>0 && Pair[0].IsValid())Id=Pair[0]->AsString();
+    }else if(V.IsValid() && V->Type==EJson::Object)
+     Id=UMareSimulation::String(V->AsObject(),TEXT("id"));
+    if(!Id.IsEmpty())Stations.AddUnique(FName(*Id));
+   }
@@ RadioName(FName Station)
-   if(FName(UMareSimulation::String(V->AsObject(),TEXT("id")))==Station)return UMareSimulation::String(V->AsObject(),TEXT("name"));
+  {FString Id,Name;
+   if(V.IsValid() && V->Type==EJson::Array){const auto& P=V->AsArray();
+    if(P.Num()>1){Id=P[0]->AsString();Name=P[1]->AsString();}}
+   else if(V.IsValid() && V->Type==EJson::Object){Id=UMareSimulation::String(V->AsObject(),TEXT("id"));Name=UMareSimulation::String(V->AsObject(),TEXT("name"));}
+   if(FName(*Id)==Station)return Name;
+  }
```

Antes de integrar, validar includes de EJson e compilação; testar estações anteriores/próximas/off e nomes reais; `mare.ShowUI phone0` só em QA. **Não editar `radio.json` neste pacote.**

## 2. P1 — dica do aparelho de rádio nunca dispara

**Fonte:** `unreal/MareAlta/Source/MareAlta/MareServiceTarget.cpp:86-94` e `MareHomeWorld.cpp:80-92`.

**Cenário:** `Use()` retorna na linha 91 ao delegar qualquer ação `Home*` para `UMareHomeWorld::Use`. O `Sim->ShowTip(Action.ToString())` vem somente na linha 93; por isso uma dica com chave existente `HomeStereoKiosk` não é exibida. **Gravidade: média para onboarding da demo.**

```diff
--- a/unreal/MareAlta/Source/MareAlta/MareServiceTarget.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MareServiceTarget.cpp
@@ void AMareServiceTarget::Use(APlayerController* Controller)
- if(Action.ToString().StartsWith(TEXT("Home"))){GetWorld()->GetSubsystem<UMareHomeWorld>()->Use(Action);return;}
+ if(Action.ToString().StartsWith(TEXT("Home"))){
+  if(Sim && (Action==TEXT("HomeStereoKiosk") || Action==TEXT("HomeStereo") || Action==TEXT("HomeStereoHotel")))
+   Sim->ShowTip(Action.ToString());
+  GetWorld()->GetSubsystem<UMareHomeWorld>()->Use(Action);return;
+ }
```

**Dica preparada, NÃO incluída no tutorial.json sem gatilho:** chave `HomeStereoKiosk`; título: **Rádio do quiosque**; texto: **Use E no rádio para trocar a música. No celular, escolha anterior, próxima ou desligar.** Quando o Claude implementar o gatilho, incluir `tutorial.json`, atualizar `source.json` e **todos os 12** arquivos de idioma, sem traduzir a chave. Não exibir dica ao usar a TV ou chuveiro.

## 3. P1 — opção de desativar toda música é só contrato de JSON, não implementação

**Fonte:** `MareGame.cpp:2224-2235` (quatro sliders: Master/Music/Effects/Ambient), `MareAudioWorld.cpp:54-98,135-184`, `Content/Data/radio_ui.json:8-18`.

**Cenário:** o menu Opções > Áudio não tem `Desativar música` e nenhum leitor `MusicMuted`/`MusicLastNonZero` na inicialização de `UMareAudioWorld`. O jogador pode zerar manualmente o volume de Música, mas não existe o checkbox prometido pelo contrato; ao alterar o slider, não é preservado o nível anterior de uma opção exclusiva de mute. **Gravidade: média/alta para a demo e para stream.**

```diff
--- a/unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp
@@ Initialize(...)
+ // Carregar bMusicMuted e MusicLastNonZero do GGameUserSettingsIni;
+ // valor efetivo de Music = bMusicMuted ? 0 : volume salvo.
@@ SetVolume(FName Bus,float Value)
+ // Ao alterar Music, preservar último volume >0 e sincronizar estado mute.
+ // Aplicar a rádio, estéreo da casa e faixas das zonas; NÃO silenciar efeitos/ambiente.
--- a/unreal/MareAlta/Source/MareAlta/MareGame.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MareGame.cpp
@@ SMareOptions::AudioPage(...)
+ // Checkbox 'Desativar música', acessível por teclado/gamepad; restaura último volume.
```

Este diff é **pseudodiff de integração** (depende de campos/métodos nos headers, excluídos pelo pedido); não colar como patch compilável. Teste obrigatório: música 35% → desligar → reiniciar → continua silenciosa → ligar → 35%; mar e cliques permanecem audíveis.

## 4. P1 — áudio legado de 'music_bossa' provavelmente não corresponde ao novo rádio

**Fonte:** `MareAudioWorld.cpp:101-111,158-168` e `Content/Data/radio.json`.

**Cenário:** `RadioStations()` inclui `radio_cc0_01` a `radio_cc0_12`, mas `StartSoundscape` só carrega `USoundWave` quando `audio.json` aponta para asset existente. Para novas faixas não importadas ou caminho incorreto, `Sounds.FindRef` falha silenciosamente e o aparelho indica tocando mesmo sem áudio. Há documentação expressa de faixas candidatas ainda sem liberação em `docs/ue58/RADIO_MUSICAS.md`. **Gravidade: alta se a build incluir estações indisponíveis** (verificação de cooker, não afirmar arquivo ausente sem o editor).

```diff
--- a/unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MareAudioWorld.cpp
@@ StartSoundscape(...)
+ // Após carregar Catalog, registrar IDs das estações sem USoundWave em log de erro QA.
+ // Bloquear seleção de estação sem asset ou oferecer fallback de faixa licenciada;
+ // não trocar automaticamente para faixas sem aprovação jurídica.
```

**Gate:** conferir no package/cook se cada faixa permitida possui licença e gravação auditada (incluindo Content ID para stream). Não habilitar as 12 candidatas pelo simples fato de constarem em `radio.json`.

## 5. P2 — riscos numéricos e integridade na natação/tobogã

**Fonte:** `MarePoolSwimWorld.cpp:216-235,241-259,320-338`.

- `GetPlayLength()` na linha 224 assume que `Clips["Jump_Start"]` não é ponteiro nulo; `Contains` sozinho não valida o objeto. Se uma animação foi removida/ficou nula em um MetaHuman, o mergulho pode falhar. Proposta compilável: substituir `Contains` por `auto* Clip=Person->Clips.FindRef(TEXT("Jump_Start")); if(S.Timer<=0 && IsValid(Clip))` e usar `Clip->GetPlayLength()`.
- `S.Along += Dt / Num(...,"ride_seconds",6)` (linha 253), e `Gone / Flight` (linha 232). O JSON atual tem 6 e 0,8, logo **não há divisão zero com os dados presentes**, mas configuração 0 após edição causaria infinidade/NaN. Proposta: `Dt/FMath::Max(.05,Num(...))` e `Gone/FMath::Max(.05f,Flight)`; adicionalmente `data_lint` deve rejeitar 0.
- `Forced=FCString::Atoi(*A)` linha 356 permite negativos arbitrários. O valor especial -1 é o único automático; validar `A` com parser e limitar [0,20] para QA; isso evita comandos acidentais.

Estes são **guardas preventivos P2**, não crashes observados. Não exibir o tobogã do Grand Hotel na demo.

## 6. P1 — créditos legais em tela incompletos

**Fonte:** `MareGame.cpp:1837-1845`. A UI usa um parágrafo estático, diz apenas "Feito na Unreal Engine 5.8"; o EULA requer avisos específicos se o produto tiver créditos. Há também atribuições CC BY 3.0 (game-icons.net). **Gravidade: bloqueio de compliance antes de vender**, mesmo que o gameplay funcione. Integrar `Content/Data/credits.json` na tela de créditos e final do milhão, com texto do EULA literalmente e link/licença adequada; diff conceitual:

```diff
--- a/unreal/MareAlta/Source/MareAlta/MareGame.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MareGame.cpp
@@ EPage::Credits
- [MareUI::Text(LOCTEXT("CreditsText", "Maré Alta Resort ... Obrigado por jogar!").ToString(),12)]
+ // Construir lista rolável dos dados credits.json, manter linha EULA exata e autores.
+ // Usar localização com chaves pt-BR + catálogos; liberar também na tela final da dívida.
```

Referências: https://www.unrealengine.com/eula/unreal e https://www.fab.com/eula.

## Ordem de correção e teste do Claude

1. Rádio P0: corrigir leitor de arrays e validar estações e nomes com unidade + PIE + build empacotada.
2. Música e dicas P1: concluir áudio persistente e gatilho; extrair/localizar 12 idiomas.
3. Créditos/EULA P1: integração com tela real e final da dívida, atribuições visíveis/distribuídas.
4. Natação P2: sanitização e guardas; QA com `mare.PoolSwim 6` **apenas em save temporário**.
5. Rodar `python tools/ue58/i18n_extract.py`, checar 12 catálogos e `python tools/ue58/qa/data_lint.py --json`; testes nativos Unreal/PIE/package continuam indispensáveis.

**Limite:** leitura estática não comprova ausência de outros problemas. O Pacote 9 não altera código, binários nem áudios.

## Cobertura completa da inspeção

A leitura estática foi estendida aos **69 arquivos `unreal/MareAlta/Source/MareAlta/*.cpp`** presentes no commit base, inclusive testes/QA, com atenção ao fluxo de dinheiro, saves, estados, divisores, índices, formatação e relógios. Achados não observados ou casos que dependem de dados ausentes não foram classificados como bugs comprovados; exemplos de guardas preventivas incluem divisores configuráveis de natação e pool.

**Correções anteriores verificadas na base:** `MareGame.cpp:2881` — `SaveClock+=DeltaSeconds` agora está fora do comentário e salva a cada 30s; `MareSimulation.cpp:424-429` — XP negativo reduz fama com piso do nível; `MareStays.cpp:102` — limpa `vip_asked` e `vip_done` por estadia. Esses pontos não devem ser reintroduzidos como bugs sem novo cenário.

**Observação adicional P2:** `MarePoolWorld.cpp:41` divide a sujeira por `PoolDefs.scoop`; os dados padrão precisam manter `scoop > 0`. Se for zero em config, o número de folhas não é válido. Correção proposta (endurecimento):

```diff
--- a/unreal/MareAlta/Source/MareAlta/MarePoolWorld.cpp
+++ b/unreal/MareAlta/Source/MareAlta/MarePoolWorld.cpp
@@ Tick(float DeltaSeconds)
-const int32 Clusters=bOwned?FMath::CeilToInt(UMareSimulation::Number(P,TEXT("dirt"))/UMareSimulation::Number(Defs,TEXT("scoop"),25)):0;
+const double Scoop=FMath::Max(1.,UMareSimulation::Number(Defs,TEXT("scoop"),25));
+const int32 Clusters=bOwned?FMath::CeilToInt(UMareSimulation::Number(P,TEXT("dirt"))/Scoop):0;
```

Conferir no linter `scoop > 0`. **Sem crash observado** e sem alteração C++ neste PR.
