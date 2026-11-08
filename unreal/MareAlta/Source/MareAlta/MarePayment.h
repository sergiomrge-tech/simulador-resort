#pragma once
#include "CoreMinimal.h"
class AMareController;
class SWidget;

/** Kiosk payment (07/11, Sergio: "sistema de pagamento assim", like the reference game): cash change from the drawer or
 *  the card terminal, after the player completes an order at the counter. Rules in UMareSimulation (MarePayment.cpp),
 *  values in Content/Data/payment.json. All money in cents. */
struct FMarePay
{
 FString Customer;
 int64 Total=0;     // what the order cost
 int64 Given=0;     // cash handed over (0 for a card)
 bool bCard=false;
 int64 ChangeDue()const{return bCard?0:FMath::Max<int64>(0,Given-Total);}
};

namespace MarePayment
{
 TSharedRef<SWidget> Make(AMareController* Owner,const FMarePay& Pay);
 bool IsOpen();
 /** QA over the open screen: "give:<cents>" adds a note/coin, "undo", "type:<digits>", "ok", "skip", "state". */
 FString QA(const FString& Cmd);
}
