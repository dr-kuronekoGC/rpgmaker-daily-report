# ==========================================
# Official
# ==========================================

def classify_official(title):

    title = title.lower()

    if "unite" in title:
        return "UNITE"

    return "本体ニュース"
