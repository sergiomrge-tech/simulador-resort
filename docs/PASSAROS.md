# Pássaros no ambiente — 23/10/2026

Adicionados cantos mais perceptíveis, direcionais, vindos de pontos de vegetação
na vila, perto da casa, do quiosque e do resort. Reutilizam bird1.ogg e bird2.ogg,
gravações CC0 já presentes e creditadas em CREDITS.md; nenhum áudio com vozes.

Uma voz 3D por vez, alternando os dois cantos com pequenas variações de afinação.
Intervalo de 4 a 9 segundos após o canto anterior, volume baixo (-13 a -10 dB),
atenuação pela distância e limite de ganho para não ficar alto perto da fonte.
Dentro da casa, redução adicional de 8 dB. A seleção prioriza árvores próximas.

Silenciam à noite, na chuva, em tempestades, no menu e longe da vegetação
(como em mar aberto). Pausa interrompe o canto e congela o intervalo. Respeitam
mute e os volumes Master/SFX; o jogador controla em Configurações → Áudio.
Gaivotas da praia e grilos noturnos foram preservados.

Implementação: scripts/audio.gd, AmbientBirds e _tick_birds. Teste
`--loop-test --birds-test` confere reprodução 3D, mixagem real por AudioEffectCapture,
intervalos, pausa, noite, chuva, mute, volume zerado, vila e distância do mar.
Usar APPDATA isolado e repetir no executável, além do teste practical que cobre
os efeitos de interação. `tools/run_counter_batch.ps1` aceita ambos os testes.

Incluído na revisão conjunta de visual e gestão: empacotar com
`tools/package_quiosque_portable.py --variant refinado`, preservando os ZIPs e
releases anteriores. Nome: MareAltaResort_1.1_RC2_Refinado_2026-10-23.zip.
