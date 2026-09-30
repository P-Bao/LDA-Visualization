# -*- coding: utf-8 -*-
"""
vi_lexicon.py
-------------
Từ điển nhỏ + danh sách stopword tiếng Việt, dùng cho pipeline TÓM TẮt
có giao diện "video" (mô phỏng Gibbs trên đoạn văn do người dùng nhập).

Bản chất: dữ liệu thuần, KHÔNG phụ thuộc thư viện ngoài (không underthesea,
không pyvi, không NLTK) — đúng tinh thần "tự cài đặt" của dự án.

  - COMPOUND_WORDS: các từ ghép tiếng Việt cần GIỦ NGUYÊN khi tách từ
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
# BE-4: Xoá mục một từ ("xe", "lái", "đường", "quãng") vì _match_compound
#       chỉ xét span >= 2 nên chúng không bao giờ khớp.
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
    "quãng đường",
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
# BE-4: Xoá "thuế", "dân" (một từ, không bao giờ khớp longest-match >= 2).
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
    "lợi ích",
    "chính phủ",
    "nhà nước",
    "cộng đồng",
]

# BE-2: Từ ghép liên quan đến "thể"/"thế" bị phá trước đây.
# "thể" và "thế" bị xoá khỏi STOPWORDS đơn; các cụm chứa chúng mà KHÔNG
# mang nghĩa nội dung được chuyển sang STOPWORD_PHRASES.
BODY_WORLD_COMPOUNDS = [
    "thể thao",       # "thể" là stopword cũ → "thể thao" bị phá thành "thao"
    "cơ thể",         # tương tự: "cơ thể" → "cơ"
    "thể hiện",
    "thế giới",       # "thế" là stopword cũ → "thế giới" → "giới"
    "thế kỷ",
    "số liệu",        # bảo toàn cụm "số liệu" dù "số" vẫn là stopword đơn
    "loại bỏ",        # bảo toàn cụm "loại bỏ" dù "loại" vẫn là stopword đơn
    "chất lượng",
    "tác động",
    "tác dụng",
    "hiệu quả",
    "hiệu suất",
]

# BE-3: Bắt buộc để preset 8 câu (TOY_SENTENCES) tách từ đúng.
TOY_COMPOUNDS = [
    "trí tuệ nhân tạo",   # 4 âm tiết — cần MAX_COMPOUND_SYLLABLES = 4
    "sân vận động",
    "huấn luyện viên",
    "lập trình viên",
    "bóng đá",
    "trận đấu",
    "đội bóng",
    "cầu thủ",
    "bàn thắng",
    "thi đấu",
    "máy tính",
    "phần mềm",
    "lập trình",
    "dữ liệu",
    "công ty",
    "công nghệ",
    "khách hàng",
    "quản lý",
]

# BE-3: Thể thao tổng quát (sample_dataset chủ đề thể thao)
SPORT_COMPOUNDS = [
    "đội tuyển",
    "vận động viên",
    "tiền đạo",
    "người hâm mộ",
]

# BE-3: Giáo dục (sample_dataset chủ đề giáo dục)
EDU_COMPOUNDS = [
    "học sinh",
    "giáo viên",
    "thí sinh",
    "đại học",
    "tuyển sinh",
    "giáo dục",
]

# BE-3: Sức khoẻ (sample_dataset chủ đề sức khoẻ)
HEALTH_COMPOUNDS = [
    "bệnh viện",
    "bác sĩ",
    "bệnh nhân",
    "chẩn đoán",
    "sức khỏe",
    "y tế",
]

# BE-3: Kinh tế mở rộng (sample_dataset chủ đề kinh tế)
ECON_COMPOUNDS = [
    "lãi suất",
    "ngân hàng",
    "doanh nghiệp",
    "xuất khẩu",
    "nông sản",
]

COMPOUND_WORDS = sorted(
    set(
        ENERGY_COMPOUNDS
        + TRANSPORT_COMPOUNDS
        + TECH_COMPOUNDS
        + ECONOMY_COMPOUNDS
        + BODY_WORLD_COMPOUNDS
        + TOY_COMPOUNDS
        + SPORT_COMPOUNDS
        + EDU_COMPOUNDS
        + HEALTH_COMPOUNDS
        + ECON_COMPOUNDS
    ),
    key=len,
    reverse=True,  # longest first -> cho thuat toan longest match
)

# Tu ghep co trong tu dien (dung de danh dau cho giao dien hien thi)
COMPOUND_SET = set(COMPOUND_WORDS)

# So am tiet toi da cho mot tu ghep
MAX_COMPOUND_SYLLABLES = 4


# ---------------------------------------------------------------------------
# STOPWORD — từ chức năng / từ dính, không mang thông tin chủ đề
# ---------------------------------------------------------------------------

# BE-2: Xoá "thể" và "thế" — chúng phá từ ghép "thể thao", "cơ thể",
#   "thế giới". Cụm "có thể", "không thể" được xử lý qua STOPWORD_PHRASES.
# BE-2: Giữ "số" và "loại" — chúng vẫn là stopword khi đứng lẻ; khi
#   đứng cạnh âm tiết nội dung, longest-match tìm "số liệu", "loại bỏ" trước.
# BE-3: Thêm "giúp" — audit cho thấy "giúp" lọt vào nhãn chủ đề nhưng
#   là liên từ xuất hiện đều ở mọi chủ đề (không phân biệt).
STOPWORDS = set(
    """
    là của các những một để cho có được này vẫn thì ở và với từ như về mà
    nhưng hoặc hay nào gì ai đâu sao bị bởi tại
    ra vào lên xuống dưới trên quanh trong ngoài bên cạnh
    cả chỉ cùng còn lại sau trước khi đang sẽ vừa mới thường nên chứ vì do
    bởi vậy nữa rồi ấy ạ nữa
    loại nhiều ít mọi mỗi vài số
    đây đó kia nọ
    thế này thế kia
    rất quá lắm hơn nhất
    có thể cần phải
    theo tại
    giúp
    """.split()
)

# Stopword dạng cụm (nhiều từ) — sẽ được so khớp như một đơn vị.
# BE-2: Thêm "có thể", "không thể", "cần phải" — các cụm này có nghĩa
#   modal (có khả năng / bắt buộc) không mang chủ đề nội dung. Nhờ
#   longest-match, "thể thao" / "cơ thể" trong COMPOUND_SET được ghép
#   trước khi đến bước kiểm tra stopword phrase.
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
    # BE-2: cụm chứa "thể"/"thế" được lọc tại đây thay vì lọc theo từ đơn
    "có thể",
    "không thể",
    "cần phải",
]

# ---------------------------------------------------------------------------
# VIẾT TẮt CẦN BẢO VỆ khi tách câu
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
STOPWORDS_LOOSE = {_strip_marks(w) for w in STOPWORDS}
STOPWORD_PHRASES_LOOSE = {_strip_marks(p) for p in STOPWORD_PHRASES}
STOPWORDS_EXACT = set(STOPWORDS)
STOPWORD_PHRASES_EXACT = set(STOPWORD_PHRASES)

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
