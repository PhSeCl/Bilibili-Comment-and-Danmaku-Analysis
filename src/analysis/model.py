from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# 添加設備設定
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 標籤映射字典
label_mapping = {
    0: "平淡語氣",
    1: "關切語調",
    2: "開心語調",
    3: "憤怒語調",
    4: "悲傷語調",
    5: "疑問語調",
    6: "驚奇語調",
    7: "厭惡語調"
}


def predict_emotion(text, model_path="Johnson8187/Chinese-Emotion-Small"):
    # 載入模型和分詞器
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)  # 移動模型到設備

    # 將文本轉換為模型輸入格式
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)  # 移動輸入到設備

    # 進行預測
    with torch.no_grad():
        outputs = model(**inputs)

    # 取得預測結果
    predicted_class = torch.argmax(outputs.logits).item()
    predicted_emotion = label_mapping[predicted_class]

    return predicted_emotion


if __name__ == "__main__":
    # 使用範例
    test_texts = [
        "雖然我努力了很久，但似乎總是做不到，我感到自己一無是處。",
        "你說的那些話真的讓我很困惑，完全不知道該怎麼反應。",
        "這世界真的是無情，為什麼每次都要給我這樣的考驗？",
        "有時候，我只希望能有一點安靜，不要再聽到這些無聊的話題。",
        "每次想起那段過去，我的心還是會痛，真的無法釋懷。",
        "我從來沒有想過會有這麼大的改變，現在我覺得自己完全失控了。",
        "我完全沒想到你會這麼做，這讓我驚訝到無法言喻。",
        "我知道我應該更堅強，但有些時候，這種情緒真的讓我快要崩潰了。"
    ]

    for text in test_texts:
        emotion = predict_emotion(text)
        print(f"文本: {text}")
        print(f"預測情緒: {emotion}\n")