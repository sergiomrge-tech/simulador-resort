#pragma once
#include "CoreMinimal.h"
#include "Camera/CameraActor.h"
#include "MareTitle.generated.h"

class AMareController;

/** Story opening of a new game (07/11, Sergio: "apresentação inicial do jogo"): postcards with a slow zoom and a caption
 *  (title.json "story": image asset + text), Space/Enter/click advances, Esc skips; then the bus arrival. */
namespace MareStory
{
 bool Show(AMareController* Owner,TFunction<void()> OnDone);
 bool IsOpen();
}


/** Title screen camera (07/11, Sergio: "início travado sem abertura, precisa ter uma tela inicial"; "o menu inicial já é a
 *  tela do jogo"): instead of the menu over a paused world, a slow flight over the bay at golden hour while the world
 *  lives. Path and hour in Content/Data/title.json (points [x, y, z, pitch, yaw], seconds per loop). */
UCLASS()
class MAREALTA_API AMareTitleCamera : public ACameraActor
{
 GENERATED_BODY()
public:
 AMareTitleCamera();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 /** Hour of the title scene (game minutes), from title.json. */
 static double TitleMinutes();
private:
 TArray<FVector> Points;TArray<FRotator> Angles;float Loop=80.f,Time=0.f;
 void Place(float T);
};
