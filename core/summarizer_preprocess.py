# -*- coding: utf-8 -*-
"""
summarizer_preprocess.py
------------------------
Tiền xử lý văn bản tiếng Việt cho trang "Tóm tắt dạng video" (Phần 1 mở rộng).

Toàn bộ xử lý dùng PYTHON CHUẨN (re, unicodedata, collections) — không dùng
underthesea / pyvi / NLTK / sklearn. Nguyên tắc:

  1. TÁCH CÂU: theo dấu . ! ? … và xuống dòng, nhưng KHÔNG cắt nhầm số thập
     phân (3.5) hay chữ viết tắt (tp., v.v.). Văn bản xuống dòng kiểu "hard
     wrap" (một câu tràn nhiều dòng) vẫn được nối lại đúng một câu.
  2. TÁCH TỪ + LÀM SẠCH: chuyển chữ thường, bỏ dấu câu, GHÉP TỪ GHÉP tiếng
     Việt bằng LONGEST MATCH với từ điển nhỏ trong core/vi_lexicon.py, bỏ
     stopword. Từ không có trong từ điển thì giữ nguyên ở mức từ đơn.
  3. Ma trận đếm câu × từ để dựng heatmap ở giao diện.

Mỗi câu = 1 "document" của LDA. Câu nào bị lọc sạch (không còn token nội
dung) sẽ bị loại khỏi LDA nhưng vẫn giữ lại để hiển thị ở các cảnh 1–3.
"""

import re
import unicodedata
from collections import Counter

from core.vi_lexicon import (
    ABBREVIATIONS,
    COMPOUND_SET,
    MAX_COMPOUND_SYLLABLES,
    is_stopword,
    is_stopword_phrase,
)

# ---------------------------------------------------------------------------
# Giới hạn đầu vào
# ---------------------------------------------------------------------------
MIN_SENTENCES = 5
MAX_WORDS = 300
MIN_WORD_LEN = 2

# Ký tự được coi là "chữ" (gồm chữ tiếng Việt có dấu và không dấu)
NON_LETTER_RE = re.compile(r"[^0-9a-zA-ZÀ-ỹĐđ_]")
TOKEN_SPLIT_RE = re.compile(r"[0-9a-zA-ZÀ-ỹĐđ]+", re.UNICODE)

# Bảo vệ số thập phân: 3.5 -> 3<DOT>5 (đánh dấu riêng, không còn là dấu chấm)
DECIMAL_RE = re.compile(r"(\d)\.(\d)")

# Ký tự đánh dấu tạm (vùng dùng riêng của Unicode, không xuất hiện trong văn bản)
DOT_MARK = "\ue000"

# Dấu kết thúc câu
TERMINALS = ".!?…"
_TERM_CLASS = "[" + re.escape(TERMINALS) + "]"


# ---------------------------------------------------------------------------
# TIỀN XỬ LÝ CẤP KÝ TỰ
# ---------------------------------------------------------------------------

def _fold_marks(text: str) -> str:
    """Bỏ dấu tiếng Việt (dùng để so khớp stopword khi người dùng thiếu dấu)."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c)).replace(
        "đ", "d"
    )


def normalize_whitespace(text: str) -> str:
    """Gộp khoảng trắng, giữ xuống dòng làm ranh giới mềm."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace(" ", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


# ---------------------------------------------------------------------------
# 1. TÁCH CÂU
# ---------------------------------------------------------------------------

def split_sentences(text: str) -> list:
    """
    Tách văn bản thành danh sách câu, giữ nguyên thứ tự gốc.

    Cách làm:
      1. Bảo vệ số thập phân và chữ viết tắt có dấu chấm.
      2. Cắt theo: dấu kết thúc câu + khoảng trắng, HOẶC xuống dòng.
      3. Nối lại các mảnh bị vỡ: nếu một mảnh KHÔNG kết thúc bằng dấu
         câu thì nó nối tiếp với mảnh sau (xử lý "hard wrap").
    """
    text = normalize_whitespace(text)
    if not text:
        return []

    protected = text

    # 1a. Bảo vệ số thập phân: "3.5" -> "3<DOT>5"
    protected = DECIMAL_RE.sub(lambda m: m.group(1) + DOT_MARK + m.group(2), protected)

    # 1b. Bảo vệ chữ viết tắt: "tp." -> "tp<DOT>"
    for abbr in ABBREVIATIONS:
        if abbr.endswith("."):
            protected = protected.replace(
                abbr + " ", abbr[:-1] + DOT_MARK + " "
            )

    # 2. Cắt: sau dấu kết thúc câu, hoặc tại mỗi xuống dòng
    pattern = r"(?<=[" + re.escape(TERMINALS) + r"])\s+|\n+"
    pieces = re.split(pattern, protected)

    # 3. Nối mảnh bị vỡ (mảnh không kết thúc bằng dấu câu nối tiếp mảnh sau)
    merged = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if merged and not merged[-1].rstrip().endswith(tuple(TERMINALS)):
            # mảnh trước chưa kết thúc câu -> nối tiếp
            merged[-1] = merged[-1] + " " + piece
        else:
            merged.append(piece)

    # Khôi phục ký tự đã bảo vệ
    sentences = [p.replace(DOT_MARK, ".").strip() for p in merged]

    return [s for s in sentences if s]


# ---------------------------------------------------------------------------
# 2. TÁCH TỪ + LÀM SẠCH (longest match với từ điển từ ghép)
# ---------------------------------------------------------------------------

def _match_compound(words, i):
    """
    Thử ghép từ tại vị trí i trong list `words` (đã lowercase, đã tách nhãn).

    Trả về (số_từ_đã_ghép, chuỗi_ghép) theo nguyên tắc LONGEST MATCH:
    thử cụm dài nhất (tối đa MAX_COMPOUND_SYLLABLES từ) trước; nếu không
    khớp từ điển thì trả về (0, None) — từ đó giữ ở mức từ đơn.
    """
    max_span = min(MAX_COMPOUND_SYLLABLES, len(words) - i)
    for span in range(max_span, 1, -1):
        candidate = " ".join(words[i:i + span])
        if candidate in COMPOUND_SET:
            return span, candidate
    return 0, None


def _match_stopword_phrase(words, i):
    """Tương tự _match_compound nhưng cho cụm stopword (vd 'tuy nhiên')."""
    for span in range(min(4, len(words) - i), 1, -1):
        candidate = " ".join(words[i:i + span])
        if is_stopword_phrase(candidate):
            return span, candidate
    return 0, None


def tokenize_sentence(sentence: str) -> list:
    """
    Tách 1 câu thành danh sách token có nhãn, phục vụ cả LDA lẫn giao diện.

    Mỗi token là dict:
        {
          "text": str,        # dạng đã lowercase + bỏ ký tự đặc biệt (dùng cho LDA)
          "surface": str,     # như trên (hiển thị)
          "type": "compound" | "word" | "stopword" | "number" | "short",
          "parts": [str, ...] # các âm tiết gộp lại (chỉ với type="compound")
        }

    type="stopword" -> bị loại khỏi LDA nhưng vẫn hiển thị (giao diện cần
    thấy từ biến mất dần ở cảnh 3).
    type="number"   -> bị loại (số không mang chủ đề).
    type="short"    -> bị loại (token < MIN_WORD_LEN ký tự sau làm sạch,
                       không đủ ý nghĩa ngữ nghĩa). Trước đây nhãn sai "number".
    """
    lowered = sentence.lower()
    # Tách mảng "từ" (chữ/số) và các ký tự xen kẽ
    raw_words = TOKEN_SPLIT_RE.findall(lowered)

    tokens = []
    i = 0
    n = len(raw_words)
    while i < n:
        # --- số thập phân dạng "3\x005" đã được bảo vệ, xử lý ở đây ---
        word = raw_words[i]

        # 1) thử GHÉP TỪ (ưu tiên dài nhất)
        span, phrase = _match_compound(raw_words, i)
        if span:
            tokens.append(
                {
                    "text": phrase,
                    "surface": phrase,
                    "type": "compound",
                    "parts": raw_words[i:i + span],
                }
            )
            i += span
            continue

        # 2) thử cụm stopword
        span, phrase = _match_stopword_phrase(raw_words, i)
        if span:
            tokens.append(
                {
                    "text": phrase,
                    "surface": phrase,
                    "type": "stopword",
                    "parts": raw_words[i:i + span],
                }
            )
            i += span
            continue

        # 3) từ đơn: số, stopword, từ nội dung
        cleaned = NON_LETTER_RE.sub("", word).strip("_")
        if not cleaned:
            i += 1
            continue
        if cleaned.isdigit():
            tokens.append(
                {"text": cleaned, "surface": cleaned, "type": "number", "parts": [word]}
            )
        elif is_stopword(cleaned):
            tokens.append(
                {"text": cleaned, "surface": cleaned, "type": "stopword", "parts": [word]}
            )
        elif len(cleaned) >= MIN_WORD_LEN:
            tokens.append(
                {"text": cleaned, "surface": cleaned, "type": "word", "parts": [word]}
            )
        # len < MIN_WORD_LEN -> đánh nhãn "short" (không đủ ý nghĩa ngữ nghĩa)
        else:
            tokens.append(
                {"text": cleaned, "surface": cleaned, "type": "short", "parts": [word]}
            )
        i += 1

    return tokens


def kept_tokens(tokens: list) -> list:
    """Lọc ra danh sách token nội dung đưa vào LDA."""
    return [t["text"] for t in tokens if t["type"] in ("compound", "word")]


# ---------------------------------------------------------------------------
# 3. MA TRẬN ĐẾM CÂU × TỪ (heatmap)
# ---------------------------------------------------------------------------

def build_count_matrix(docs_tokens: list, min_count: int = 1) -> dict:
    """
    Dựng ma trận đếm số lần xuất hiện của mỗi từ trong mỗi câu.

    Trả về: {vocab: [w...], matrix: [[count,...], ...], max_count: int}
    Chỉ giữ từ xuất hiện >= min_count lần trong corpus để heatmap gọn.
    """
    corpus_count = Counter()
    for doc in docs_tokens:
        corpus_count.update(doc)

    vocab = sorted(w for w, c in corpus_count.items() if c >= min_count)
    w2i = {w: i for i, w in enumerate(vocab)}

    matrix = [[0] * len(vocab) for _ in docs_tokens]
    for d, doc in enumerate(docs_tokens):
        for w in doc:
            j = w2i.get(w)
            if j is not None:
                matrix[d][j] += 1

    max_count = max((max(row) for row in matrix), default=0)
    return {"vocab": vocab, "matrix": matrix, "max_count": max_count}


# ---------------------------------------------------------------------------
# HÀM CHÍNH: tiền xử lý 1 đoạn văn
# ---------------------------------------------------------------------------

class PreprocessError(ValueError):
    """Lỗi tiền xử lý kèm thông báo tiếng Việt thân thiện cho giao diện."""


def preprocess_document(text: str) -> dict:
    """
    Tiền xử lý một đoạn văn để đưa vào LDA.

    Trả về dict chứa:
      sentences        : list[str]                  — câu gốc (giữ thứ tự)
      sentence_tokens  : list[list[token dict]]     — token có nhãn từng câu
      docs_tokens      : list[list[str]]            — token nội dung (đưa vào LDA)
      lda_index_map    : list[int]                  — ánh xạ câu -> doc trong LDA
                                                          (-1 nếu câu rỗng)
      empty_sentences  : list[int]                  — chỉ số câu không còn token
      vocab / matrix   : heatmap câu × từ
      stats            : số câu, số từ gốc, số từ nội dung, số stopword bị bỏ
    """
    raw = (text or "").strip()
    if not raw:
        raise PreprocessError("Vui lòng nhập một đoạn văn để phân tích.")

    sentences = split_sentences(raw)
    if len(sentences) < MIN_SENTENCES:
        raise PreprocessError(
            f"Đoạn văn quá ngắn: cần ít nhất {MIN_SENTENCES} câu để chạy LDA, "
            f"hiện chỉ tách được {len(sentences)} câu."
        )

    # Giới hạn độ dài đầu vào (~300 từ)
    word_tokens = TOKEN_SPLIT_RE.findall(raw.lower())
    if len(word_tokens) > MAX_WORDS:
        raise PreprocessError(
            f"Đoạn văn quá dài: tối đa {MAX_WORDS} từ, "
            f"đoạn của bạn có {len(word_tokens)} từ. Vui lòng rút gọn lại."
        )

    sentence_tokens = [tokenize_sentence(s) for s in sentences]

    docs_tokens = []
    lda_index_map = []
    empty_sentences = []
    total_kept = 0
    total_stop = 0
    total_num = 0
    total_short = 0

    for idx, toks in enumerate(sentence_tokens):
        kept = kept_tokens(toks)
        total_stop += sum(1 for t in toks if t["type"] == "stopword")
        total_num += sum(1 for t in toks if t["type"] == "number")
        total_short += sum(1 for t in toks if t["type"] == "short")
        if kept:
            lda_index_map.append(len(docs_tokens))
            docs_tokens.append(kept)
            total_kept += len(kept)
        else:
            lda_index_map.append(-1)
            empty_sentences.append(idx)

    if not docs_tokens:
        raise PreprocessError(
            "Không còn từ nội dung nào sau khi loại stopword. "
            "Vui lòng nhập đoạn văn dài hơn hoặc ít stopword hơn."
        )

    heatmap = build_count_matrix(docs_tokens)

    return {
        "sentences": sentences,
        "sentence_tokens": sentence_tokens,
        "docs_tokens": docs_tokens,
        "lda_index_map": lda_index_map,
        "empty_sentences": empty_sentences,
        "vocab": heatmap["vocab"],
        "matrix": heatmap["matrix"],
        "max_count": heatmap["max_count"],
        "stats": {
            "num_sentences": len(sentences),
            "num_docs": len(docs_tokens),
            "num_raw_words": len(word_tokens),
            "num_kept_tokens": total_kept,
            "num_stopwords_removed": total_stop,
            "num_numbers_removed": total_num,
            "num_short_removed": total_short,
            "vocab_size": len(heatmap["vocab"]),
        },
    }
