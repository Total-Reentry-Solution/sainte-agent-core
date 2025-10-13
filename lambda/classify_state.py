# Basic NLP-style classifier (placeholder logic; can later use Bedrock)

def classify_user_state(text:str) -> str:
    text = text.lower()
    if any(word in text for word in ["panic", "cant", "hurt", "suicidal"]):
        return "Critical"
    
    elif any(word in text for word in ["missed", "late", "tired", "stresed"]):
        return "At-Risk"
    
    elif any(word in text for word in ["okay", "fine", "meh"]):
        return "Stirred"
    
    return "Stable"