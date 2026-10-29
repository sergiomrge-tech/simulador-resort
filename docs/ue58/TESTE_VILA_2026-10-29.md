# Prévia para teste — vila, casa e abertura — 29/10/2026

**Fonte do executável: `45cc1e69`. Unreal 5.8.3, Windows x64/DX12.**
Esta é uma prévia funcional da migração; não é a conversão completa do jogo.

## Arquivos prontos no drive D

- Pasta: `D:/Downloads/MareAltaResort_UE58_Vila_2026-10-29`.
- Iniciar: `Jogar.vbs` ou `Jogar.cmd` dentro dessa pasta.
- ZIP: `D:/Downloads/MareAltaResort_UE58_Vila_2026-10-29.zip`.
- Tamanho do ZIP: 1.733.856.077 bytes.
- SHA-256: `fb43c9511470819cfaf41f35484c7381df592c787a2e21c8389423975e1b62e8`.
- Build original testado: `D:/Builds/MareAltaUE58_VilaTeste_2026-10-29/Windows`.

Começa com dados novos, chegada de ônibus e carta do avô. Leia a carta antes de
criar a empresa no celular. A placa física abre/fecha o quiosque. Os atalhos mantêm
o progresso desta prévia em `userdata` na pasta do D. Instalações antigas não foram
substituídas; o ZIP não inclui dados de jogador nem exige instalar a Unreal.

## Mudanças incluídas

- Cinco moradores físicos e doze pedestres no padrão de qualidade alta; cinco
  pedestres na distância baixa. Rotas existentes validadas no NavMesh ampliado.
- Conversas físicas com moradores, texto completo em cartão compacto; E/Esc
  encerra a conversa e B não sobrepõe o celular durante o diálogo.
- Espera pela navegação na inicialização, recuperação de caminho obstruído sem
  teleporte e desvio entre pessoas. Cápsula dos moradores ajustada à largura.
- Troca de aparência sem acumular cabelo ou perder o clip. Modelos verificados
  nos GLBs: Human_2 é feminino; 0/1/3 são masculinos. Nomes dos clientes e
  associação dos moradores corrigidos com base nessa informação.
- Corpo/mãos, produtos acompanhando as mãos, natação, TV, som e sofá do lote
  anterior. Abertura com ônibus detalhado, motorista, interior, porta e degraus.
- Celular portátil B, placa física, sem preparo, pagamento automático e único
  atendente preservados. Gramado contínuo com 177454 instâncias mantido.

## Verificação executada neste pacote

- **87/87 verificações funcionais**, saída 0, sem erros nos padrões de script,
  recurso ausente, compilação de material ou fallback de uso de material.
  Perfil: `D:/CodexTemp/ue58-package-qa-20261029-173943`.
- Áudio master efetivamente gravado: audível RMS 0,005814 / pico 0,047363;
  mute e pausa RMS 0. Sem clipping no trecho medido.
- Chegada natural **12/12** e opção de avançar **11/11**, incluindo caminhada
  física até porta/carta: `D:/CodexTemp/ue58-intro-package-20261029-174340`.
- Capturas reais do EXE revisadas; diálogo completo e separação dos pedestres
  confirmados. Exemplos em `graphics-reference/vila-20261029/`.
- Sete arquivos EXE/Pak/IoStore copiados conferidos por SHA-256 contra o build
  testado; integridade CRC de todos os arquivos do ZIP aprovada, sem userdata.
  Resultado: `D:/Downloads/MareAltaResort_UE58_Vila_2026-10-29-verificacao.json`.

## Desempenho medido

RTX 4060 Ti 8 GB, câmera fixa no bosque, 1920×1080 nativo, limite de FPS removido
somente no teste, Lumen/Nanite/PCG ativos e população presente:

| Medida | Resultado |
|---|---:|
| FPS médio | 72,1 |
| Frame médio / P95 | 13,864 / 17,138 ms |
| GPU média | 12,569 ms |
| Game thread média | 5,313 ms |
| Render thread média | 13,888 ms |
| Memória local GPU média | 3157 MB |

Evidência: `D:/CodexTemp/ue58-render-profile-20261029-174431/summary.json`.
Não é garantia de 60 FPS em todo o mapa; o P95 passou de 16,67 ms. A entrega
normal mantém limite de 60 e inicia em janela 1280×720. Alternativa média via Esc.
Mitigação de estabilidade `r.Lumen.AsyncCompute=0` preservada.

## Limitações e continuação

- Efeito visual/câmera do chuveiro ainda em revisão: a captura olha para um painel
  cinza e não comprova a qualidade da água. Controle abre/fecha passou.
- Horizonte subaquático, arte de pessoas/fauna e iluminação noturna ainda precisam
  de acabamento. Não tratar todos os modelos atuais como arte final aprovada.
- Outros negócios ainda precisam de operação completa, além de mostrar/comprar
  construções. Capítulos/fama/pesca/fotos e vida ambiente adicional seguem pendentes.
- Três propostas de interface continuam para depois dos sistemas anteriores.
- Guia integral: `PENDENCIAS_2026-10-29.md`. Preservar saves e as três pastas Actors
  antigas não rastreadas. Novos testes sempre com dados separados no D.

O primeiro empacotamento foi bloqueado por DLL do editor aberto; o editor foi
fechado e a geração refeita com sucesso. O script agora detecta esse caso antes
de exportar, sem encerrar processos automaticamente.
