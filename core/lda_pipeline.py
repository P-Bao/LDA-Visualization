# -*- coding: utf-8 -*-
"""
lda_pipeline.py
---------------
Cài đặt LDA "thực chiến" bằng gensim (variational Bayes, tối ưu cho tập dữ liệu
lớn hơn nhiều so với bản Gibbs sampling tự viết ở Phần 1). Đây là CÙNG MỘT
THUẬT TOÁN LDA (Latent Dirichlet Allocation) đã được mô phỏng từng bước ở
core/gibbs_lda.py — chỉ khác cách suy luận tham số (Gibbs sampling so với
biến phân/variational inference) để chạy được trên dữ liệu thật.

Module này phục vụ:
  - Phần 2: tóm tắt trích xuất 1 văn bản đơn (mỗi CÂU là 1 "document" trong corpus)
  - Phần 3: phân tích 1 tập nhiều văn bản (mỗi VĂN BẢN là 1 "document" trong corpus)
"""

import numpy as np
from gensim import corpora, models

from core.nlp_utils import split_sentences, tokenize_and_clean


# ---------------------------------------------------------------------------
# Xây dựng corpus & huấn luyện LDA (dùng chung)
# ---------------------------------------------------------------------------

def build_corpus(list_of_token_lists):
    dictionary = corpora.Dictionary(list_of_token_lists)
    dictionary.filter_extremes(no_below=1, no_above=0.9)
    corpus = [dictionary.doc2bow(toks) for toks in list_of_token_lists]
    return dictionary, corpus


def train_lda(corpus, dictionary, num_topics=5, passes=20, seed=42):
    return models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        passes=passes,
        random_state=seed,
        alpha="auto",
        eta="auto",
    )


def topic_distribution(lda_model, bow, num_topics):
    dist = np.zeros(num_topics)
    for topic_id, prob in lda_model.get_document_topics(bow, minimum_probability=0):
        dist[topic_id] = prob
    return dist


def top_words_per_topic(lda_model, num_topics, topn=10):
    return {t: lda_model.show_topic(t, topn=topn) for t in range(num_topics)}


# ---------------------------------------------------------------------------
# PHẦN 2 — Tóm tắt trích xuất 1 văn bản, dựa trên phân bố chủ đề
# ---------------------------------------------------------------------------

def summarize_extractive(text: str, num_topics: int = 4, top_k: int = 3, passes: int = 20):
    """
    Coi mỗi CÂU trong văn bản là một "document" để huấn luyện LDA, từ đó suy ra
    phân bố chủ đề của từng câu và của toàn văn bản, rồi chấm điểm mỗi câu bằng

        score(câu) = phân_bố_chủ_đề(câu) · phân_bố_chủ_đề(toàn_văn_bản)

    Chọn top_k câu điểm cao nhất, giữ nguyên thứ tự xuất hiện gốc -> bản tóm tắt.
    """
    sentences = split_sentences(text)
    if len(sentences) < 2:
        raise ValueError("Văn bản quá ngắn, cần ít nhất 2 câu để phân tích LDA.")

    sentence_tokens = [tokenize_and_clean(s) for s in sentences]
    keep = [i for i, toks in enumerate(sentence_tokens) if len(toks) > 0]
    sentences = [sentences[i] for i in keep]
    sentence_tokens = [sentence_tokens[i] for i in keep]

    dictionary, corpus = build_corpus(sentence_tokens)
    num_topics = max(2, min(num_topics, len(sentences) - 1, 20))
    lda_model = train_lda(corpus, dictionary, num_topics=num_topics, passes=passes)

    full_bow = dictionary.doc2bow([tok for toks in sentence_tokens for tok in toks])
    doc_dist = topic_distribution(lda_model, full_bow, num_topics)
    words_per_topic = top_words_per_topic(lda_model, num_topics, topn=10)

    scores = []
    for idx, bow in enumerate(corpus):
        sent_dist = topic_distribution(lda_model, bow, num_topics)
        score = float(np.dot(sent_dist, doc_dist))
        scores.append((idx, score, sent_dist))

    ranked = sorted(scores, key=lambda x: x[1], reverse=True)
    top_k = min(top_k, len(sentences))
    chosen_idx = sorted(i for i, _, _ in ranked[:top_k])
    summary = " ".join(sentences[i] for i in chosen_idx)

    sentence_detail = [
        {
            "sentence": sentences[i],
            "score": round(score, 4),
            "topic_distribution": [round(float(p), 4) for p in dist],
            "selected": i in chosen_idx,
        }
        for i, score, dist in scores
    ]

    return {
        "sentences": sentences,
        "num_topics": num_topics,
        "doc_dist": doc_dist.tolist(),
        "topic_words": {str(k): v for k, v in words_per_topic.items()},
        "summary": summary,
        "sentence_detail": sentence_detail,
    }


# ---------------------------------------------------------------------------
# PHẦN 3 — Phân tích một TẬP văn bản (mỗi văn bản = 1 document trong corpus)
# ---------------------------------------------------------------------------

def train_corpus_level_lda(documents: list, num_topics: int = 5, passes: int = 30):
    """
    documents: list các văn bản (mỗi phần tử là toàn bộ nội dung 1 bài).
    Trả về dictionary, corpus, lda_model, và ma trận phân bố chủ đề của
    từng văn bản trong tập — dùng để đánh giá & trực quan hoá ở Phần 3.
    """
    doc_tokens = [tokenize_and_clean(doc) for doc in documents]
    dictionary, corpus = build_corpus(doc_tokens)
    num_topics = max(2, min(num_topics, len(documents) - 1, 20))
    lda_model = train_lda(corpus, dictionary, num_topics=num_topics, passes=passes)

    doc_topic_matrix = [
        topic_distribution(lda_model, bow, num_topics).tolist() for bow in corpus
    ]
    words_per_topic = top_words_per_topic(lda_model, num_topics, topn=10)

    return {
        "dictionary": dictionary,
        "corpus": corpus,
        "lda_model": lda_model,
        "num_topics": num_topics,
        "doc_topic_matrix": doc_topic_matrix,
        "topic_words": {str(k): v for k, v in words_per_topic.items()},
        "doc_tokens": doc_tokens,
    }


def compute_coherence(lda_model, doc_tokens, dictionary, corpus, coherence="u_mass"):
    """
    u_mass: chỉ dùng chính corpus huấn luyện (không cần dữ liệu tham chiếu ngoài),
    phù hợp để chạy offline. Giá trị càng gần 0 (ít âm) thì các từ trong cùng
    1 chủ đề càng hay xuất hiện cùng nhau trong corpus -> chủ đề càng "mạch lạc".
    """
    from gensim.models import CoherenceModel

    cm = CoherenceModel(
        model=lda_model, texts=doc_tokens, corpus=corpus, dictionary=dictionary,
        coherence=coherence,
    )
    return cm.get_coherence()
