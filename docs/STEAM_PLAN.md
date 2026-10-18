# Maré Alta Resort — Steam Plan (v0.2.0)

*Written 17/10/2026 (America/Sao_Paulo). Status: no Steamworks integration and nothing uploaded to Steam. This is a plan only.*

## 1. Where the game stands
- **Engine:** Godot 4.5.1. The PC build uses Forward+ (SDFGI, SSIL, SSR, SSAO, volumetric fog, soft 4096 shadows, TAA/MSAA, FSR 2). Textures are capped at **2K**. The Android build stays on the Mobile renderer.
- **Loop:** the hero lives in a fishing-village house and wakes up at 06:30. He works at the beach kiosk (iced coconut, caipirinha, snacks) and also helps at the inn: check-in, cleaning bungalows, buying hammocks. After 20:00 he goes home to sleep, and the game saves.
- **Already "Steam-ready" in this build:**
  - main menu: New game, Continue, Load, Settings, Quit
  - pause on Esc/Start
  - 3 save slots
  - full settings: graphics presets (Ultra is the default on PC), window mode, resolution, V-Sync, 3D scale with FSR 2, FOV, master/music/effects volume, mouse/gamepad sensitivity, invert Y, keyboard rebinding
  - PT-BR and EN text
  - gamepad support (XInput layout)
  - .ico icon in the .exe
  - portable build that runs from D: (see §6)

## 2. What's needed for Steam (nothing has been done yet)
1. **Steamworks partner account:** sign up and pay the US$100 Steam Direct fee per app (recouped after US$1,000 in revenue). Fill in tax and banking info (W-8BEN for Brazil).
2. **App ID:** Valve assigns it when the app is created. A **Demo App ID** comes separately, which the Next Fest demo needs.
3. **GodotSteam:** use the GDExtension (prebuilt for Godot 4.5) or the precompiled editor/templates. Steps:
   - `Steam.steamInitEx(true, APP_ID)` at startup, and `Steam.run_callbacks()` every frame.
   - `steam_appid.txt` next to the exe during development only.
   - Achievements, for example: "Primeiro check-in", "100 cocos vendidos", "5 estrelas", "Todas as redes", "Dia 30".
   - Rich Presence ("Dia 4 — Turno no quiosque").
   - Steam Cloud for `user://save_slot*.json` and `settings.cfg` (Auto-Cloud works without code).
   - Steam Input: the current gamepad support covers Xbox and PlayStation through SDL, and Steam Input can remap on top of that.
4. **Depots/builds:** a Windows x86_64 depot, uploaded with SteamPipe (`steamcmd +run_app_build`) on beta and default branches. The exe and .pck as exported today are enough.
5. **Steam Deck:** test it, using the "Médio" preset and 0.75 scale. The UI already scales with resolution and has full gamepad support.

## 3. Store page (checklist)
- **Capsule art (required sizes):**
  - header 920×430
  - small 462×174
  - main 1232×706
  - vertical 748×896
  - page background 1438×810
  - library: capsule 600×900, hero 3840×1240, logo 1280×720
- **Screenshots:** at least 5 at 1920×1080, from the PC build on the Ultra preset. Suggested shots:
  - golden-hour aerial of the village
  - kiosk with customers
  - pousada at night with lanterns
  - bungalow interior lit by GI
  - pedra-portuguesa street with the church
- **Trailer:** 30–60 s, gameplay first: wake up, walk to the kiosk, serve, check-in, sunset, sleep. CC0 bossa music.
- **Short description (PT/EN):** "Viva numa vila de pescadores do Nordeste, trabalhe no quiosque da praia e transforme a pousada Maré Alta num resort 5 estrelas." / "Live in a Brazilian fishing village, work the beach kiosk and grow the Maré Alta inn into a 5-star resort."
- **Tags:** Simulation, Management, First-Person, Relaxing, Cozy, Life Sim, Beach, Singleplayer, Realistic, Building.
- **Languages:** Portuguese (Brazil) and English, interface and subtitles. Spanish is planned next (big LATAM market).
- **Mature content survey:** alcohol (caipirinha) appears but isn't promoted, so likely "General Mature Content: no". Check the "alcohol reference" box.
- **Minimum PC requirements (estimate, to be confirmed on real hardware):** Windows 10/11 64-bit, GTX 1060 / RX 580 with Vulkan, 8 GB RAM, 3 GB disk. **Recommended:** RTX 3060 / RX 6600, 16 GB RAM. The developer's PC (RTX 4060 Ti, Ryzen 7 5700G, 32 GB) should run Ultra at 1080p–1440p. That hasn't been measured yet.

## 4. Steam Next Fest demo
- **Timing:** apply for the next Next Fest at least 2 months ahead (the dates are on the partner site). A "Coming Soon" page must be live and approved by Valve first. Valve's guidance is to have the page up for weeks before the event to collect wishlists.
- **Demo scope:** 3 in-game days (~40 minutes) covering the kiosk, 2 bungalows, the hammock shop, the full village and sleeping. Locked: future expansions (more bungalows, staff, a restaurant). End screen with a "Wishlist now" link (`Steam.activateGameOverlayToStore`).
- **Technical:** a separate app (Demo App ID), the same branch, and a `DEMO` feature flag via a custom export feature. The day limit is checked in `Core.sleep()`.
- **Before the festival:** a playtest via Steam Playtest, plus a closed beta with 50–200 players to measure FPS across GPUs.

## 5. Pricing (references, Steam price checked on 17/10/2026)
| Reference | Steam price | Notes |
|---|---|---|
| Supermarket Simulator | US$ 19.99 | 92% positive, co-op, the genre benchmark |
| Motel Manager Simulator | US$ 17.99 | 84% positive, first-person check-ins and cleaning, the closest comparison |
| Hotel Renovator | US$ 24.99 | 77% positive, more renovation/decoration content |
| Hotel Renovator Simulator (2026) | US$ 9.99 | 64% positive, smaller scope |

**Suggestion:**
- **Early Access at US$ 12.99**, with Brazilian regional pricing around **R$ 32,99–37,99** (follow Valve's suggested regional price). That means 6–10 h of content: 5–8 bungalows, kiosk upgrades, staff, events (festa junina, réveillon).
- **1.0 at US$ 16.99–19.99** once there's construction/decoration and more NPCs.
- **Launch discount:** 10–15%. Don't go below US$ 9.99, which signals a small game.

## 6. PC build and the C: drive (user's PC)
- **Today's delivery** is a portable zip: extract it to `D:\Games\MareAltaResort\` and run `Jogar_portatil_D.bat`. The .bat points `APPDATA` at `userdata\` next to the exe, so saves, settings and Godot's shader cache stay on D:. Opening `MareAltaResort.exe` directly also works, but then saves go to `%APPDATA%\Maré Alta Resort` on C: (a few KB, plus the shader cache, typically tens of MB).
- **NVIDIA's own driver shader cache** (`%LOCALAPPDATA%\NVIDIA\DXCache` / `GLCache`) is controlled by the driver, not the game. It can be moved or capped in the NVIDIA Control Panel ("Shader Cache Size").
- **On Steam:** the user picks the library on D: (Steam > Settings > Storage > add drive D:). Saves go through Steam Cloud plus `%APPDATA%`.

## 7. Porting to Unreal Engine 5 (later)
- **Why consider it:** Lumen/Nanite give a big jump in visual fidelity, marketplace assets (Fab) are much more realistic, and the "photoreal simulator" audience sells well.
- **Cost/risk:**
  - Everything gets rewritten in C++/Blueprints. The GDScript code here (~3.5k lines) is the spec: state, economy, guest loop, kiosk, day/sleep, settings, i18n, slots.
  - Build sizes grow to 5–15 GB.
  - Minimum requirements rise (RTX 2060+).
  - Steam Deck is harder.
- **What carries over directly:**
  - design (GDD), balancing (rates, prices, timings)
  - CC0 textures and models (Poly Haven provides FBX/glTF, which UE imports)
  - CC0 audio
  - the village layout (coordinates in `world_village.gd`)
  - PT/EN strings (export to UE's String Tables CSV)
- **Recommendation:** ship Early Access in Godot (lower risk, already running), validate wishlists and sales, then decide on UE5 for a "2.0" or a sequel. If going UE5 from the start: UE 5.5+, Lumen HW RT optional, Nanite for vegetation/rocks, World Partition (overkill for this map size), Mass AI for villagers, and the Steam Online Subsystem plugin instead of GodotSteam.

## 8. Next technical steps
1. Measure FPS on the RTX 4060 Ti (Ultra at 1440p). If it's under 60, lower SDFGI cascades or use FSR 2 at 0.77.
2. Replace the UAL mannequins with real characters (CC0 or commissioned).
3. Build out the 6–10 hours of Early Access content (see §5), then achievements and Cloud via GodotSteam once the App ID exists.
