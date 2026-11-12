#pragma once
#include "CoreMinimal.h"

class AMareController;
class SWidget;

/** The fight with a hooked fish (11/11, Fase 3: "pesca com isca, briga com o peixe e livro de espécies").
 *  Holding reels the line in (Progress up) and tightens it (Tension up); letting go slackens it. The fish pulls in
 *  bursts: reeling against a pull barely gains line and the tension climbs fast, so the player gives line while it pulls
 *  and reels between pulls. Tension over the limit for a moment snaps the line; a slack line for too long, or all the
 *  line lost, lets the fish go. Pure (no engine state): Step is driven by the widget and by the tests. */
struct FMareFishFight
{
 float Strength=.3f;        // 0..1: species and size
 float Progress=.25f;       // line recovered, 1 = landed
 float Tension=.35f;        // 0..1.2, the line snaps after staying at 1 or more
 float PullLeft=0,NextPull=1.2f,Over=0,Slack=0;
 int32 Result=0;            // 0 fighting, 1 landed, -1 line snapped, -2 the fish got away
 bool IsPulling()const{return PullLeft>0;}
 void Step(float Dt,bool bReel,float Rand01);
};

namespace MareFishing
{
 /** The pier fishing panel: bait choice, cast, strike, fight, and the species book (L or Tab). */
 TSharedRef<SWidget> Create(AMareController* Owner);
 /** QA ("mare.Fish <cmd>"): bait:<id>, bite, strike, reel:<seconds>, give:<seconds>, auto, book, state. */
 FString QA(const FString& Cmd);
}
