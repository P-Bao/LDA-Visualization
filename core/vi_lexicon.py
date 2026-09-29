# -*- coding: utf-8 -*-
"""
vi_lexicon.py
-------------
Từ điển nhỏ + danh sách stopword tiếng Việt, dùng cho pipeline TÓM TẮT
có giao diện "video" (mô phỏng Gibbs trên đoạn văn do người dùng nhập).

Bản chất: dữ liệu thuần, KHÔNG phụ thuộc thư viện ngoài (không underthesea,
không pyvi, không NLTK) — đúng tinh thần "tự cài đặt" của dự án.

  - COMPOUND_WORDS: các từ ghép tiếng Việt cần GIỮ NGUYÊN khi tách từ
    (thay vì tách rời thành 2-3 âm tiết rời rạc làm từ vựng loãng).
  - STOPWORDS: từ chức năng, không mang chủ đề → bỏ để phân bố chủ đề
    không bị "loãng" vì những từ xuất hiện ở mọi câu.

Ghép từ được thực hiện bằng thuật toán LONGEST MATCH (thử từ dài nhất
trước) trong summarizer_preprocess.py.
"""

# ---------------------------------------------------------------------------
# TỪ GHÉP — nhóm theo chủ đề để dễ đọc và dễ bổ sung
# ---------------------------------------------------------------------------

# Năng lượng & môi trường
ENERGY_COMPOUNDS = [
    "năng lượng mặt trời",
    "năng lượng tái tạo",
    "năng lượng gió",
    "năng lượng",
    "ô nhiễm không khí",
    "khí thải",
    "khí độc",
    "môi trường",
    "bền vững",
    "giao thông xanh",
    "tái tạo",
    "tiết kiệm",
]

# Phương tiện giao thông
TRANSPORT_COMPOUNDS = [
    "phương tiện giao thông",
    "ô tô điện",
    "xe điện",
    "động cơ điện",
    "động cơ",
    "pin lithium",
    "trạm sạc công cộng",
    "trạm sạc",
    "giao thông",
    "giá xe",
    "giá thành",
    "giá bán",
    "đường",
    "xe",
    "lái",
    "quãng đường",
    "quãng",
    "tốc độ",
    "xăng dầu",
    "nhiên liệu",
    "thành phố",
    "đô thị",
    "hạ tầng",
]

# Công nghệ & sản xuất
TECH_COMPOUNDS = [
    "công nghệ pin",
    "công nghệ",
    "dung lượng",
    "số lượng",
    "nhà sản xuất",
    "sản xuất",
    "nghiên cứu",
    "cung cấp",
    "kỹ thuật",
    "tiến bộ",
    "phát triển",
    "xu hướng",
    "ứng dụng",
    "hệ thống",
    "kỳ vọng",
    "e ngại",
    "lo lắng",
    "phân bố",
    "phần lớn",
    "kéo dài",
]

# Kinh tế & xã hội
ECONOMY_COMPOUNDS = [
    "người tiêu dùng",
    "người mua",
    "thị trường",
    "chi phí",
    "kinh tế",
    "việc làm",
    "chính sách",
    "hỗ trợ",
    "ưu đãi thuế",
    "thuế",
    "lợi ích",
    "chính phủ",
    "nhà nước",
    "dân",
    "cộng đồng",
]

COMPOUND_WORDS = sorted(
    set(
        ENERGY_COMPOUNDS
        + TRANSPORT_COMPOUNDS
        + TECH_COMPOUNDS
        + ECONOMY_COMPOUNDS
    ),
    key=len,
    reverse=True,  # longest first -> cho thuật toán longest match
)

# Từ ghép có trong từ điển (dùng để đánh dấu cho giao diện hiển thị)
COMPOUND_SET = set(COMPOUND_WORDS)

# Số âm tiết tối đa cho một từ ghép — dùng để sinh nhanh các "từ mới"
# (từ ngoài từ điển) trong cảnh 3 của giao diện.
MAX_COMPOUND_SYLLABLES = 4


# ---------------------------------------------------------------------------
# STOPWORD — từ chức năng / từ dính, không mang thông tin chủ đề
# ---------------------------------------------------------------------------

STOPWORDS = set(
    """
    là của các những một để cho có được này vẫn thì ở và với từ như về mà
    nhưng hoặc hay nào gì ai đâu sao bị bởi tại
    ra vào lên xuống dưới trên quanh trong ngoài bên cạnh
    cả chỉ cùng còn lại sau trước khi đang sẽ vừa mới thường nên chứ vì do
    bởi vậy nữa rồi ấy ạ nữa
    loại nhiều ít mọi mỗi vài số
    đây đó kia nọ
    thế này thế kia thế
    rất quá lắm hơn nhất
    có thể cần phải
    theo tại
    """.split()
)

# Stopword dạng cụm (nhiều từ) — sẽ được so khớp như một đơn vị.
STOPWORD_PHRASES = [
    "nhờ vậy",
    "tuy nhiên",
    "bên cạnh đó",
    "vì vậy",
    "ngoài ra",
    "mặt khác",
    "điển hình",
    "nói cách khác",
    "thứ nhất",
    "thứ hai",
    "thứ ba",
    "nói chung",
    "nhìn chung",
    "tóm lại",
    "cuối cùng",
    "trên thực tế",
    "về cơ bản",
    "cụ thể là",
    "ví dụ",
    "tức là",
    "có thể nói",
    "điều đó",
    "vấn đề này",
    "khi nào",
    "bao giờ",
    "tại sao",
    "thế nào",
    "ai là",
]

# ---------------------------------------------------------------------------
# VIẾT TẮT CẦN BẢO VỆ khi tách câu: KHÔNG cắt sau dấu chấm của chúng.
# Chỉ liệt kê viết tắt THỰC SỰ kết thúc bằng dấu chấm — những viết tắt
# không có dấu chấm không gây lỗi tách câu nên không cần liệt kê.
# ---------------------------------------------------------------------------
ABBREVIATIONS = [
    "v.v.",
    "v.d.",
    "tp.",
    "tt.",
    "ts.",
    "bs.",
    "gs.",
    "pgs.",
    "kg.",
    "km.",
    "cm.",
]


# ---------------------------------------------------------------------------
# STOPWORD TỪ ĐƯỢC CHUẨN HOÁ (lowercase + bỏ dấu phụ kiện)
# ---------------------------------------------------------------------------

def _strip_marks(word: str) -> str:
    """Bỏ dấu tiếng Việt + hạ chữ thường (dùng cho tra cứu bỏ qua dấu)."""
    import unicodedata

    decomposed = unicodedata.normalize("NFD", word.lower())
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return plain.replace("đ", "d")


def _has_marks(word: str) -> bool:
    """
    True nếu chuỗi chứa ký tự tiếng Việt (mọi chữ có dấu đều có mã > 127,
    kể cả dạng dựng sẵn 'á' lẫn dạng kết hợp 'a' + dấu).

    Dùng để phân biệt: người dùng gõ CÓ dấu -> so khớp chính xác;
    gõ KHÔNG dấu ("cung") -> mới cho phép so khớp bản không dấu.
    """
    return any(ord(ch) > 127 for ch in word)


# Bản tra cứu không dấu, CHỈ dùng khi người dùng gõ thiếu dấu
# (mọi từ trong STOPWORDS đều có dấu) -> tránh lo nhầm từ có dấu
# giống từ không dấu (vd "cung" bị lo oan vì "cùng" là stopword).
STOPWORDS_LOOSE = {_strip_marks(w) for w in STOPWORDS}
STOPWORD_PHRASES_LOOSE = {_strip_marks(p) for p in STOPWORD_PHRASES}
STOPWORDS_EXACT = set(STOPWORDS)
STOPWORD_PHRASES_EXACT = set(STOPWORD_PHRASES)


# Ngưỡng an toàn cho việc so khớp không dấu: chỉ áp dụng với từ dài từ 4
# ký tự trở lên. Từ tiếng Việt ngắn 3 ký tự rất dễ trùng khi mất dấu
# (vd "lại" -> "lai" sẽ lo nhầm "lai" trong "tương lai").
LOOSE_MATCH_MIN_LEN = 4


def is_stopword(word: str) -> bool:
    """
    Kiểm tra 1 từ có phải stopword không.

    - Có dấu -> so khớp CHÍNH XÁC trong danh sách stopword.
    - Không dấu, đủ dài -> so khớp bản không dấu, giúp lọc đúng cả khi
      người dùng gõ thiếu dấu.
    """
    w = word.lower().strip()
    if w in STOPWORDS_EXACT:
        return True
    if len(w) >= LOOSE_MATCH_MIN_LEN and not _has_marks(w):
        return _strip_marks(w) in STOPWORDS_LOOSE
    return False


def is_stopword_phrase(phrase: str) -> bool:
    """Kiểm tra 1 cụm có phải stopword cụm không (vd 'tuy nhiên')."""
    p = phrase.lower().strip()
    if p in STOPWORD_PHRASES_EXACT:
        return True
    if not _has_marks(p):
        return _strip_marks(p) in STOPWORD_PHRASES_LOOSE
    return False
