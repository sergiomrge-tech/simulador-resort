#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MareServiceTarget.generated.h"
class UStaticMeshComponent;
class APlayerController;

/** Physical interaction point; invisible station targets only supplement the visible imported equipment. */
UCLASS()
class MAREALTA_API AMareServiceTarget : public AActor
{
 GENERATED_BODY()
public:
 AMareServiceTarget();
 virtual void Tick(float DeltaSeconds) override;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Interaction") FName Action=TEXT("Fridge");
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Interaction") FString Label=TEXT("Geladeira");
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Interaction") FVector FocusOffset=FVector::ZeroVector;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Interaction") float Reach=240.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Interaction") float OcclusionTolerance=70.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Door") bool bAutoClose=false;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Interaction") int32 DataIndex=-1;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Door") TObjectPtr<UStaticMeshComponent> DoorMesh;
 /** Uses the target from a validated player interaction. */
 UFUNCTION(BlueprintCallable,Category="Interaction") void Use(APlayerController* Controller);
 UFUNCTION(BlueprintPure,Category="Door") bool IsOpen()const{return bOpened;}
 FString Prompt()const;
 bool CanClose(const FVector& PlayerLocation)const;
 UFUNCTION(BlueprintPure,Category="Interaction")
 static AMareServiceTarget* FindFocused(APlayerController* Controller);
private:
 bool bOpened=false;
 bool bWasInside=false;
 float DoorAngle=0.f;
};
