#include "RuntimeEditor/OntoTwinLocalModelRefresh.h"
#include "TwinInstance.h"
#include "TwinSceneManager.h"
#include "Misc/SecureHash.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace {
struct FChangedFile {
    FString Digest;
    TArray<TWeakObjectPtr<ATwinInstance>> Users;
};
class SLocalModelRefresh : public SCompoundWidget {
public:
    SLATE_BEGIN_ARGS(SLocalModelRefresh) {}
        SLATE_ARGUMENT(TFunction<ATwinSceneManager*()>, GetManager)
    SLATE_END_ARGS()
    void Construct(const FArguments& Args) {
        Manager = Args._GetManager;
        ChildSlot[SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight()[SNew(SButton).Text(FText::FromString(TEXT("检查已放置模型的更新"))).OnClicked(this,&SLocalModelRefresh::Scan)]
            + SVerticalBox::Slot().AutoHeight()[SNew(STextBlock).AutoWrapText(true).Text_Lambda([this]{return FText::FromString(Message);})]
            + SVerticalBox::Slot().AutoHeight()[SNew(SHorizontalBox)
                .Visibility_Lambda([this]{return Pending.IsEmpty()?EVisibility::Collapsed:EVisibility::Visible;})
                + SHorizontalBox::Slot()[SNew(SButton).Text(FText::FromString(TEXT("确认重载"))).OnClicked(this,&SLocalModelRefresh::Apply)]
                + SHorizontalBox::Slot()[SNew(SButton).Text(FText::FromString(TEXT("取消"))).OnClicked_Lambda([this]{
                    Pending.Reset(); Message.Empty(); return FReply::Handled();
                })]]];
    }
private:
    TFunction<ATwinSceneManager*()> Manager;
    TMap<FString,FChangedFile> Pending;
    FString Message;
    FReply Scan() {
        Pending.Empty();
        if (!Manager()) return FReply::Handled();
        TArray<ATwinInstance*> Objects;
        Manager()->GetManagedInstances(Objects);
        TMap<FString,FString> Digests;
        for (ATwinInstance* Object : Objects) {
            if (!IsValid(Object) || Object->GetLocalModelPath().IsEmpty()) continue;
            const FString& Path = Object->GetLocalModelPath();
            if (!Digests.Contains(Path)) Digests.Add(Path, LexToString(FMD5Hash::HashFile(*Path)));
            const FString& Digest = Digests[Path];
            if (Digest == Object->GetLocalModelDigest()) continue;
            FChangedFile& Changed = Pending.FindOrAdd(Path);
            Changed.Digest = Digest;
            Changed.Users.Add(Object);
        }
        TArray<FString> Lines;
        for (const auto& Pair : Pending)
            Lines.Add(FString::Printf(TEXT("%s · %d 个对象"), *FPaths::GetCleanFilename(Pair.Key), Pair.Value.Users.Num()));
        Message = Lines.IsEmpty() ? TEXT("当前关卡的本地模型均为最新") : FString::Join(Lines,TEXT("\n"));
        return FReply::Handled();
    }
    FReply Apply() {
        for (const auto& Pair : Pending) {
            if (LexToString(FMD5Hash::HashFile(*Pair.Key)) != Pair.Value.Digest) {
                Scan(); Message = TEXT("文件再次变化，请重新确认\n") + Message; return FReply::Handled();
            }
        }
        int32 Updated = 0;
        TArray<FString> Errors;
        for (const auto& Pair : Pending) {
            for (auto Weak : Pair.Value.Users) {
                auto* Object = Weak.Get();
                if (!Object || Object->GetLocalModelPath() != Pair.Key) continue;
                if (Object->ReloadLocalModel()) ++Updated;
                else Errors.AddUnique(FPaths::GetCleanFilename(Pair.Key));
            }
        }
        Pending.Empty();
        Message = FString::Printf(TEXT("已重载 %d 个对象"),Updated);
        if (!Errors.IsEmpty()) Message += TEXT("；文件缺失或网格解析失败，保留原模型：") + FString::Join(Errors,TEXT("、"));
        return FReply::Handled();
    }
};
}
TSharedRef<SWidget> MakeLocalModelRefresh(TFunction<ATwinSceneManager*()> GetManager)
{
    return SNew(SLocalModelRefresh).GetManager(MoveTemp(GetManager));
}
