# ==========================================
# Resource Intent Classification
# ==========================================

from asset_metadata_engine import _normalize_text


# ==========================================
# Classification guards
# ==========================================

def _is_non_asset_category(category):
    text = _normalize_text(category)

    non_asset_keywords = (
        "質問",
        "相談",
        "tips",
        "tip",
        "help",
        "question",
        "questions",
        "discussion",
        "news",
        "情報",
        "公式情報",
        "サイト更新",
        "site update",
        "sourcecheck",
    )

    return any(
        keyword in text
        for keyword in non_asset_keywords
    )


def _is_non_asset_title(title):
    text = _normalize_text(title)

    # 質問・解説・作品紹介を素材として誤登録しないための保護。
    # これらは「音楽」「sound」等の単語を含んでも、
    # 素材そのものとは限らない。
    non_asset_keywords = (
        "question",
        "questions",
        "need help",
        "help",
        "how do",
        "study",
        "audiobook",
        "showcase",
        "showcasing",
        "my project",
        "project showcase",
        "compatibility",
        "compatible",
        # "engine" alone is common in actual plugin/resource titles
        # (e.g. "ABS Engine Pro"), so it must not be a blanket exclusion.
        # Likewise, "video" alone can refer to a plugin demo/release page.
        # Keep only explicit gameplay/process media signals.
        "gameplay video",
        "making-of video",
        "process video",
        "trailer",
        "ゲーム",
        "エンジン",
        "プロジェクト",
        "互換",
        "について手伝",
        "手伝って",
    )

    if any(keyword in text for keyword in non_asset_keywords):
        return True

    # Forum backfills often have no body text. Explicit request/question
    # phrasing in the title is useful negative evidence in that case.
    # classify_resource_intent checks concrete release/download evidence
    # before calling this guard, so explicit releases are not discarded.
    request_phrases = (
        "plugin request",
        "request:",
        "request -",
        "need ",
        "looking for",
        "seeking ",
        "wanted:",
        "help me",
        "can someone",
        "could someone",
        "anyone have",
        "anyone know",
        "how do i",
        "how can i",
        "how to ",
        "where can i find",
        "not working",
        "does not work",
        "doesn't work",
        "cerco ",
        "cercasi",
        "richiesta",
        "mi serve",
        "mi servono",
        "aiuto",
        "non funziona",
        "come posso",
        "come fare",
        "suche ",
        "ich brauche",
        "hilfe",
        "funktioniert nicht",
        # Russian text and common transliterations used in forum URL slugs.
        "ищу",
        "ищем",
        "помогите найти",
        "помогите",
        "нужен",
        "нужна",
        "нужны",
        "нужно",
        "где найти",
        "ищется",
        "вопрос",
        "как сделать",
        "как написать",
        "как создать",
        "ishchu",
        "pomogite",
        "nuzhen",
        "nuzhna",
        "nuzhny",
        "gde-najti",
        "kak-sdelat",
        "vopros",
        "je cherche",
        "recherche",
        "besoin de",
        "aidez-moi",
        "探しています",
        "探してます",
        "求む",
        "作り方",
        "動かない",
        "できません",
        "質問です",
    )
    return any(phrase in text for phrase in request_phrases)


def _is_explicit_plugin_category(category):
    text = _normalize_text(category)

    return (
        text in ("plugin", "plugins", "プラグイン")
        or "プラグイン" in text
    )


def _is_explicit_game_category(category):
    text = _normalize_text(category)

    return (
        text in ("game", "games", "ゲーム")
        or "ゲーム" in text
    )


def classify_resource_intent(item, detected_category=None):
    """
    Resource-intent triage, deliberately separate from detailed taxonomy.

    Returns (intent, confidence, evidence), where intent is:
      - resource_candidate: concrete release/distribution or a clear asset signal
      - not_resource: clear question/showcase/news context without a deliverable
      - uncertain: insufficient evidence to decide safely

    Price, paid status, or an external storefront are never negative signals.
    """
    title = str(item.get("title") or "")
    category = str(item.get("category") or "")
    url = str(item.get("url") or "").lower()

    # Forum last-comment URLs are collector metadata, not independent resources.
    if "do=getlastcomment" in url:
        return ("not_resource", "high", [{"field": "url", "signal": "last_comment_metadata"}])

    # Paginated forum URLs whose extracted title is only the page number are
    # duplicate collector records, not independent resource posts.
    if "/page/" in url:
        page_suffix = url.split("/page/", 1)[1].strip("/")
        page_number = page_suffix.split("/", 1)[0]
        if page_number.isdigit() and title.strip() == page_number:
            return ("not_resource", "high", [{"field": "url", "signal": "pagination_metadata"}])

    # Forum user-profile pages are author metadata, not downloadable resources.
    if "/forum/user/" in url:
        return ("not_resource", "high", [{"field": "url", "signal": "user_profile_page"}])
    source_tags = item.get("source_tags", [])
    tags = item.get("tags", [])
    if not isinstance(source_tags, list):
        source_tags = []
    if not isinstance(tags, list):
        tags = []

    body_parts = []
    for field in ("description", "body_text", "post_body", "body", "content_text", "content", "text"):
        value = item.get(field)
        if isinstance(value, str) and value.strip():
            body_parts.append(value.strip())

    combined = " ".join(
        [title, category, str(item.get("url") or "")]
        + [str(x) for x in source_tags + tags]
        + body_parts
    ).lower()

    # Only concrete distribution/release wording is a strong positive signal.
    distribution_signals = (
        "download here",
        "download link",
        "available for download",
        "download the plugin",
        "download the resource",
        "downloadable resource",
        "downloadable asset",
        "free to use",
        "asset pack",
        "resource pack",
        "plugin release",
        "released",
        "release available",
        "get it here",
        "配布中",
        "ダウンロードはこちら",
        "ダウンロードリンク",
        "素材配布",
        "公開しました",
        "配布ページ",
    )
    distribution_hits = [word for word in distribution_signals if word in combined]

    # Explicitly identified games, official notices and source-update entries
    # are not resource records by themselves; a linked release can still qualify.
    category_text = category.lower()
    is_game = _is_explicit_game_category(category)
    is_site_notice = _is_non_asset_category(category)

    title_guard = _is_non_asset_title(title)
    # Some forums expose a generic title (e.g. "Последнее") while the URL slug
    # contains the actual request. Use the slug as supporting negative evidence.
    url_guard = _is_non_asset_title(url)
    category_guard = is_site_notice
    guarded_context = title_guard or url_guard or category_guard

    if distribution_hits:
        return (
            "resource_candidate",
            "medium",
            [{"field": "body_or_metadata", "signal": signal} for signal in distribution_hits[:5]],
        )

    if is_game:
        return ("not_resource", "high", [{"field": "category", "signal": "explicit_game"}])

    # Question/showcase/discussion terms are negative only when no concrete
    # distribution evidence was found. This does not exclude paid resources.
    if guarded_context:
        if title_guard:
            field, signal = "title", "question_or_showcase_title"
        elif url_guard:
            field, signal = "url", "request_or_question_slug"
        else:
            field, signal = "category", "non_resource_category"
        return ("not_resource", "medium", [{"field": field, "signal": signal}])

    if detected_category:
        return (
            "resource_candidate",
            "medium",
            [{"field": "title_url_or_tags", "signal": "asset_classifier_match", "category": detected_category}],
        )

    resource_tags = ("asset", "assets", "resource", "resources", "plugin", "plugins", "素材", "プラグイン")
    tag_hits = [str(tag) for tag in source_tags + tags if any(word in str(tag).lower() for word in resource_tags)]
    if tag_hits:
        return (
            "uncertain",
            "low",
            [{"field": "source_tags_or_tags", "signal": tag} for tag in tag_hits[:5]],
        )

    return ("uncertain", "unknown", [])
