#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Dom/JsonObject.h"
#include "MareSimulation.generated.h"

/** Summary of one save slot for the main menu (read straight from slotN.json). */
struct FMareSlotInfo
{
 bool bExists=false;
 int32 Day=0;
 double Money=0;
 FString Company;
 FDateTime SavedAt;
};

/** Native economy and progression. JSON retains fields from the original save format. */
UCLASS()
class MAREALTA_API UMareSimulation : public UGameInstanceSubsystem
{
 GENERATED_BODY()
public:
 virtual void Initialize(FSubsystemCollectionBase& Collection) override;
 TSharedPtr<FJsonObject> State;
 TSharedPtr<FJsonObject> Definitions;
 FString LastMessage;
 /** Separate test/import destination; blank uses this UE project Saved folder. */
 FString SaveDirectory;
 /** Creates the company without changing existing inventory or personal saves. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool CreateCompany(const FString& Name);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool SetOpen(bool bOpen);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool IsOpen() const;
 /** Expansion licences gate sale/pickup while keeping display props visible. */
 UFUNCTION(BlueprintPure,Category="Maré Alta")
 bool IsDishUnlocked(const FString& Dish) const;
 /** Previously accepted orders remain fulfillable after the licence migration. */
 UFUNCTION(BlueprintPure,Category="Maré Alta")
 bool CanSupplyDish(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 int32 Available(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 double RestockCost(const FString& Dish, int32 Quantity=10) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Restock(const FString& Dish, int32 Quantity=10);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Pickup(const FString& Dish,bool bStaff=false);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool ReturnCarry(bool bStaff=false);
 /** Checks customer demand, consumes carry and records payment once per delivered item. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Deliver(const FString& OrderId, const FString& Dish,bool bStaff=false);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 FString AddOrder(const FString& Customer, const TArray<FString>& Dishes);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool HireAttendant();
 /** Lets the attendant go: carried product returns to stock, no refund, no wage from the next night. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool DismissAttendant();
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool BuyExpansion(const FString& Id);
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool ClaimMission(const FString& Id, bool bSide=false);
 int32 MissionAmount(const TSharedPtr<FJsonObject>& Mission) const;
 /** Village chapters open in sequence and keep their step in prog.ch, as in the approved save. */
 TSharedPtr<FJsonObject> ChapterDefinition(const FString& Id) const;
 int32 ChapterStep(const FString& Id) const;
 bool IsChapterOpen(const FString& Id) const;
 bool IsChapterDone(const FString& Id) const{return ChapterStep(Id)>=3;}
 /** Current/required amount of the active step; deliver/pay consume only in AdvanceChapter. */
 int32 ChapterStepProgress(const FString& Id,int32& Goal) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool AdvanceChapter(const FString& Id);
 /** Market purchase of raw supplies, charged once and only when the full amount is affordable. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool BuySupply(const FString& Item,int32 Quantity);
 double SupplyCost(const FString& Item,int32 Quantity) const;
 /** Fame level 1..10 from prog.fame_xp using the original thresholds. */
 int32 FameLevel() const;
 FString FameName() const;
 void AddFame(int32 Xp);
 /** Average guest rating (1..5) over the saved ratings list. */
 double Stars() const;
 /** Grand Hotel occupancy 0.15..0.98 from rating and fame, as in the approved version. */
 double HotelOccupancy() const;
 /** Books one night of the Grand Hotel (suites, dining, staff) and stores prog.hotel. */
 void HotelNight();
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 void AdvanceMinutes(double Minutes);
 /** Closes the day: wages once per day, summary in ue_last_day, ledger totals reset. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 void Sleep();
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool Save();
 // ---- Save slots: slot1..3.json in the save folder, slots.json keeps the last used one.
 static constexpr int32 SlotCount=3;
 /** Slot read and written by Save(); chosen by -MareSlot=N, else the last used slot (1 for legacy profiles). */
 int32 ActiveSlot=1;
 /** Session flag: the main menu was already answered (survives level reloads, not the process). */
 bool bMainMenuDone=false;
 /** While the world reloads into another slot, the old world must not write its actors into the new state. */
 bool bHoldSaves=false;
 FString SaveFolder() const;
 FString SlotPath(int32 Slot) const;
 FMareSlotInfo SlotInfo(int32 Slot) const;
 bool HasAnySave() const;
 /** Last used slot from slots.json; a legacy folder with only slot1.json becomes slot 1 (index written). */
 int32 LastSlot() const;
 /** Replaces State with the slot (falls back to its .bak when the file is damaged) and makes it active. */
 bool LoadSlot(int32 Slot);
 /** Fresh profile (default_save + arrival intro) written to the slot; the previous file is kept as .bak. */
 bool NewGame(int32 Slot);
 /** Read-only legacy import; destination always belongs to the Unreal project. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 bool ImportLegacySave(const FString& Path);
 // ---- Customization (Content/Data/customization.json): 5 tiers per object, tier 1 is the starting look.
 /** Catalogue loaded on first use (also works in automation tests that skip Initialize). */
 TSharedPtr<FJsonObject> CustomDefs() const;
 TSharedPtr<FJsonObject> CustomSlot(const FString& Place,const FString& Slot) const;
 /** Selected tier 1..5 (state custom.<place>.<slot>.tier). */
 UFUNCTION(BlueprintPure,Category="Maré Alta") int32 CustomTier(const FString& Place,const FString& Slot) const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool OwnsCustomTier(const FString& Place,const FString& Slot,int32 Tier) const;
 /** Price of a tier: slot base_price x price_mult[tier-1]; tier 1 is free. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double CustomPrice(const FString& Place,const FString& Slot,int32 Tier) const;
 /** Buys the tier when not owned (charged once), then selects it. Owned tiers switch for free. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool BuyCustom(const FString& Place,const FString& Slot,int32 Tier);
 /** Comfort / beauty points of a place: sum over slots of weight x (tier-1). */
 double PlaceComfort(const FString& Place) const;
 double PlaceBeauty(const FString& Place) const;
 double CustomEffect(const FString& Key,double Fallback=0) const;
 /** Kiosk gameplay from the decor: customer arrival rate x, tip share, patience x, attendant speed x. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskArrivalFactor() const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskTipRate() const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskPatienceFactor() const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double KioskServiceSpeed() const;
 /** Recipe level 1..5 per dish (state recipes.<dish>): raises the sale price and the demand. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") int32 RecipeLevel(const FString& Dish) const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") double DishPrice(const FString& Dish) const;
 /** Price the player charges (phone, state prices.<dish>, 50%-200% of DishPrice); DishPrice stays the fair reference. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double SalePrice(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool SetSalePrice(const FString& Dish,double Price);
 /** SalePrice / DishPrice: 1 is fair, above sells less and earns smaller tips, below sells more. */
 double PriceRatio(const FString& Dish) const;
 /** Cost of the next recipe level (0 when maxed). */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double RecipeUpgradeCost(const FString& Dish) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool UpgradeRecipe(const FString& Dish);
 FString RecipeTitle(const FString& Dish,int32 Level=0) const;
 /** Relative chance a customer orders this dish (recipe level makes it more popular). */
 double DishDemand(const FString& Dish) const;
 // ---- Places beyond the kiosk (customization.json "places" + "operations").
 TSharedPtr<FJsonObject> PlaceDef(const FString& Place) const;
 /** Bought expansion / business behind a place (the home and the kiosk are always available). */
 bool IsPlaceAvailable(const FString& Place,FString* Reason=nullptr) const;
 double PlaceEffect(const FString& Place,const FString& Key,double Fallback=0) const;
 /** Sum over slots of Key x (tier-1), e.g. "rate", "income", "seats". */
 double SlotSum(const FString& Place,const FString& Key) const;
 /** Income multiplier of a place: 1 + income_per_point x (comfort+beauty) + service upgrades. */
 double PlaceIncomeFactor(const FString& Place) const;
 /** Extra occupancy from the pool (pousada and hotel) and from the four hotel areas. */
 double StayBonus() const;
 double HotelCustomBonus() const;
 int32 PousadaRooms() const;
 /** HUD reputation: pousada rooms plus Grand Hotel suites, how many were occupied last night, products sold today. */
 int32 RoomsTotal() const;
 int32 RoomsOccupied() const;
 int32 ServedToday() const;
 double PousadaRate() const;
 double PousadaOccupancy() const;
 /** Books one night of the pousada (rooms x rate x occupancy, plus tips); stores prog.pousada. */
 void PousadaNight();
 int32 TourSeats(const TSharedPtr<FJsonObject>& Tour) const;
 int32 TourPassengers(const TSharedPtr<FJsonObject>& Tour) const;
 /** Expected income of an hourly operation (bar, pool) or business for one open hour, before chance. */
 double HourlyIncome(const FString& Id) const;
 double BusinessRate(const FString& Id) const;
 /** Books the hour that just ended [Hour-1, Hour): bar, pool, tours and businesses. Once per game hour. */
 void OperateHour(int32 Hour);
 /** Income booked today by a place (bar, pool, passeios, biz_<id>). */
 double OpsToday(const FString& Place) const;
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool HasStaff(const FString& Role) const;
 /** Hires an expansion role (bartender, camareira, guia): needs its expansion; wage charged at night. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool HireStaff(const FString& Role);
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool DismissStaff(const FString& Role);
 UFUNCTION(BlueprintPure,Category="Maré Alta") bool OwnsBusiness(const FString& Id) const;
 /** Buys a village business (definitions.businesses): needs its chapter and fame level. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta") bool BuyBusiness(const FString& Id);
 bool CanBuyBusiness(const FString& Id,FString& Reason) const;
 /** Home comfort makes the player walk faster; home beauty brings fame every night. */
 UFUNCTION(BlueprintPure,Category="Maré Alta") double HomeSpeedFactor() const;
 /** One line with the current effect of a place's decor, for the phone. */
 FString PlaceSummary(const FString& Place) const;
 // --- Hands-on lodging (docs/ue58/GAMEPLAY_PLANO_2026-11-02.md, M2/M3; MareStays.cpp) ---
 // State "stays": rooms [{id, place, state free|occupied|dirty, guest, nights, rate, mood, tasks}],
 // queue [{id, name, profile, limit, offer, round, mood, nights}]. Everything lives in the save, not in actors.
 /** Room list of the pousada matches PousadaRooms() (new rooms start clean). */
 void SyncRooms();
 /** A guest joins the reception queue (max 3); returns the guest id or empty. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta|Stays") FString AddArrival(const FString& Place=TEXT("pousada"));
 /** Reference nightly rate and stay settings (customization.json operations.pousada / hotel_stays). */
 double StayRate(const FString& Place) const;
 TSharedPtr<FJsonObject> StayOps(const FString& Place) const;
 enum class EHaggle:uint8{Accepted,Countered,Left,Invalid};
 /** The player asks Price per night. Under the guest's secret limit it is accepted (sometimes after one counter),
  *  above it the guest refuses, loses mood and raises the offer a little; after 3 refusals or no mood, he leaves.
  *  OutOffer is the guest's offer afterwards. Accepted checks the guest in and charges all nights at once. */
 EHaggle Haggle(const FString& Guest,double Price,double& OutOffer);
 /** Takes the guest's current offer (no haggling) and checks him in. */
 bool AcceptOffer(const FString& Guest);
 /** One cleaning task of a dirty room ("bed", "towels", "trash"); the room is free when none is left. */
 bool CleanRoom(const FString& Room,const FString& Task);
 /** Night: stays lose a night; finished stays check out (rating from mood, comfort and cleanliness), room dirty. */
 void StaysNight();
 /** Hourly: arrivals during the day, the receptionist checks guests in at their offer, the maid cleans. */
 void StaysHour(int32 Hour);
 /** Next guest of Place who checked out last night and still has to walk out of the lobby (state stays.departures,
  *  filled by StaysNight for the hotel, cleared at 13:00); removed from the list. Null when nobody is left. */
 TSharedPtr<FJsonObject> TakeDeparture(const FString& Place);
 TSharedPtr<FJsonObject> Stays();
 // --- Grand Hotel restaurant, hands-on (MareRestaurant.cpp, Content/Data/restaurant.json) ---
 // State "restaurant": tables [{table, name, stage order|cooking|tray, dish, since, ready}], room [{suite, dish, stage,
 // since, ready}], event {id, day}, served, next.
 TSharedPtr<FJsonObject> RestaurantDefs() const;
 TSharedPtr<FJsonObject> Restaurant();
 double RestaurantNow() const;
 /** Hotel bought and inside a service (lunch or dinner). */
 bool IsRestaurantOpen() const;
 TSharedPtr<FJsonObject> MenuDish(const FString& Id) const;
 double MenuPrice(const FString& Id) const;
 TSharedPtr<FJsonObject> TableOrder(int32 Table) const;
 /** Seats a party at a free table while the restaurant is open; returns its name or empty. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta|Restaurant") FString SeatDiners(int32 Table);
 /** E on a table: takes the order (to the kitchen) or serves the dish on the tray (price + tip for speed). */
 bool UseTable(int32 Table);
 /** E at the kitchen pass: every cooked dish (tables and room service) goes on the tray; returns how many. */
 int32 PickUpPass();
 /** E at the lift: delivers the room service on the tray (price + room fee). */
 int32 DeliverRoomService();
 /** Books an event (restaurant.json "events") for tomorrow's event hour; pays the preparation now. */
 bool BookEvent(const FString& Id);
 /** Hourly: event of the day, crew serving long waits, new diners and room service while open. */
 void RestaurantHour(int32 Hour);
 // --- Tours, hands-on (MareTours.cpp, Content/Data/tours.json; the tours are customization.json operations.tours) ---
 // State "tours" (reset each day): queue {tour: buyers at the booth}, sold {tour: tickets}, done {tour: guided|guide|cancelled|empty}, rating.
 TSharedPtr<FJsonObject> ToursDefs() const;
 TSharedPtr<FJsonObject> Tours();
 TSharedPtr<FJsonObject> TourDef(const FString& Id) const;
 TArray<FString> TourIds() const;
 /** Today's count in "queue" or "sold" for a tour. */
 int32 TourCount(const FString& Field,const FString& Id) const;
 /** Today's outcome of a tour, empty while it has not left. */
 FString TourStatus(const FString& Id) const;
 /** Inside the departure hour and not left yet: the player can guide it. */
 bool IsTourBoarding(const FString& Id) const;
 double TicketPrice(const FString& Id) const;
 /** Sells a ticket to everyone waiting at the booth for this tour (up to the free seats); returns how many. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta|Tours") int32 SellTickets(const FString& Id);
 /** Guides the tour now: Choices per stop are 0 good, 1 acceptable, 2 bad. Books the tip minus the trip cost,
  *  rates the tour (stars) and gives fame; returns the rating, 0 when it cannot leave. */
 double GuideTour(const FString& Id,const TArray<int32>& Choices);
 /** Hourly: buyers before each departure (the guide sells), and at the end of the departure hour the guide's run
  *  or the cancellation with refund. */
 void ToursHour(int32 Hour);
 // --- Pool day use, hands-on (MarePool.cpp, Content/Data/pool.json) ---
 // State "pool": dirt 0..100 (leaves in the water), towels [lounger indices], popsicles (guests asking).
 TSharedPtr<FJsonObject> PoolDefs() const;
 TSharedPtr<FJsonObject> Pool();
 int32 PoolTowels() const;
 /** 0.3..1: leaves and towels lower it; multiplies the pool's hourly income and rates the pool at closing. */
 double PoolCleanliness() const;
 /** One sweep of the net: removes pool.json "scoop" of dirt. */
 bool ScoopPool();
 bool CollectPoolTowel(int32 Lounger);
 /** Sells every popsicle asked for (price x pool decor factor). */
 bool SellPopsicles();
 /** Hourly while the pool is open: leaves fall, towels are left on loungers, popsicles are asked; closing rates it. */
 void PoolHour(int32 Hour);
 // --- Village businesses at the counter (MareBusiness.cpp, Content/Data/business_games.json) ---
 TSharedPtr<FJsonObject> BusinessGames() const;
 /** Inside the business's opening hours (definitions.json businesses.<id>.open). */
 bool IsBusinessOpen(const FString& Id) const;
 /** Owned, open and nobody served at this counter during the current hour. */
 bool CanPlayBusiness(const FString& Id,FString& Reason) const;
 /** Result of the three-round counter task: books max(hourly rate, base) × rewards[Hits] and fame per hit. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta|Business") double PlayBusiness(const FString& Id,int32 Hits);
 /** Hourly: night tokens of the game room (business_games.json game_room), more players with the hotel full. */
 void GameRoomHour(int32 Hour);
 // --- Bar do Coqueiro (gameplay plan M8; MareBar.cpp, Content/Data/bar.json) ---
 // State "bar": stock {ingredient: n}, known [recipe ids], orders [{id, name, want (recipe id or "surpresa"), hint, since
 // (day*1440+minutes)}], next, served.
 TSharedPtr<FJsonObject> BarDefs() const;
 TSharedPtr<FJsonObject> Bar();
 TSharedPtr<FJsonObject> BarRecipe(const FString& Recipe) const;
 /** Recipe made of exactly these ingredients (any order, no repeats), or empty. */
 FString MixRecipe(const TArray<FString>& Ingredients) const;
 bool IsRecipeKnown(const FString& Recipe) const;
 /** Bar bought and inside its opening hours (bar.json "open"). */
 bool IsBarOpen() const;
 /** A guest sits at the bar and orders Want (empty = picks one); returns the order id, empty when closed or full. */
 UFUNCTION(BlueprintCallable,Category="Maré Alta|Bar") FString AddBarOrder(const FString& Want=TEXT(""));
 struct FBarResult{bool bServed=false;bool bDiscovered=false;FString Recipe;double Paid=0;};
 /** Shakes the ingredients (always used up) for an order: the drink asked for (or any recipe for a "surpresa") pays
  *  price plus a tip for speed; an unknown recipe is discovered (fame) even when it is not what was ordered. */
 FBarResult ServeBar(const FString& Order,const TArray<FString>& Ingredients);
 /** Buys every ingredient up to bar.json restock_qty; false without enough money. */
 bool RestockBar();
 double BarRestockCost() const;
 /** Menu price of a drink: recipe price × bar decor factor × fame. */
 double DrinkPrice(const FString& Recipe) const;
 /** Hourly: impatient guests leave, the bartender serves known drinks from the stock, new guests arrive. */
 void BarHour(int32 Hour);
 /** Bets and prizes from minigames (game room): books the amount with a label, like any other income or expense. */
 void SettleBet(double Amount,const FString& Label){Book(Amount,Label);}
 int32 FreeCleanRooms(const FString& Place=TEXT("pousada")) const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 double Money() const;
 UFUNCTION(BlueprintCallable,Category="Maré Alta")
 FString Carry(bool bStaff=false) const;
 static TSharedPtr<FJsonObject> Object(const TSharedPtr<FJsonObject>& Parent, const FString& Key);
 static double Number(const TSharedPtr<FJsonObject>& Parent, const FString& Key, double Fallback=0);
 static FString String(const TSharedPtr<FJsonObject>& Parent, const FString& Key);
private:
 bool ReadJson(const FString& Path,TSharedPtr<FJsonObject>& Target) const;
 void Book(double Amount,const FString& Label);
 bool Fail(const FString& Message);
 FString SavePath() const;
 /** Writes State to the active slot (previous file copied to .bak first), without capturing actors. */
 bool WriteState();
 bool ReadSave(const FString& Path,TSharedPtr<FJsonObject>& Target) const;
 void WriteSlotIndex(int32 Slot) const;
 mutable TSharedPtr<FJsonObject> CustomCatalog;
};
