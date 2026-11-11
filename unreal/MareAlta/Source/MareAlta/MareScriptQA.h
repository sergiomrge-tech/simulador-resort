#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MareScriptQA.generated.h"

// Scripted photo run of the packaged game (11/11: what had only been seen in the editor is checked in the executable).
// MareAlta.exe -MareScriptQA=D:/CodexTemp/<file>.txt -MareSkipMenu -MareSaveRoot=D:/CodexTemp/<new folder>
// One step per line of the file ("#" = comment):
//   wait <real seconds> | clock <minutes of the day> | pose x,y,z,pitch,yaw (hero flying there) | speed <time dilation>
//   hire (kiosk attendant) | pastel <own|customers:n|open|fill|seal:1|dip|fry:7|out|deliver|close> (pastel minigame) | shot <name> (PNG with the UI in the save root) | people <name> (who is around, to script-qa.json)
//   anything else is a console command ("mare.QA company Teste", "mare.Weather 1", "mare.ShowUI close").
// Writes script-qa.json after every step and quits at the end.
UCLASS()
class AMareScriptQA : public AActor
{
 GENERATED_BODY()
public:
 AMareScriptQA();
 virtual void Tick(float DeltaSeconds) override;
private:
 FString Root;
 TArray<FString> Lines;
 int32 Line=-1;
 double Next=0;
 TArray<TSharedPtr<class FJsonValue>> Records;
 void Write(bool bFinished);
};
