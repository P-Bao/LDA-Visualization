/* ==========================================================================
   summarize-player.js
   Player "Tóm tắt dạng video": phát lại 11 cảnh từ đoạn văn tới bản tóm tắt.
   Thuần JS + SVG/HTML/CSS, không thư viện ngoài, namespace IIFE.
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------
     Hằng số
     ------------------------------------------------------------------ */
  // Màu chủ đề: dùng đậm hơn bảng ở Phần 1 để chip có nền nhạt vẫn đủ tương
  // phản; 4 màu phân biệt rõ nhau, khớp token Teal/Indigo của trang.
  var PALETTE = ['#0F766E', '#4338CA', '#B45309', '#BE185D'];

  var REDUCED = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  // Nhịp mặc định (ms) cho từng cảnh — cảnh Gibbs chi tiết phải nhanh hơn
  var BEAT = { default: 950, sweep: 280, accelerate: 190, out: 700 };

  // Biểu tượng SVG sắc nét cho các nút điều khiển
  var ICONS = {
    prevScene: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="19 20 9 12 19 4 19 20"></polygon><line x1="5" y1="19" x2="5" y2="5"></line></svg>',
    prevFrame: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="19 20 9 12 19 4 19 20"></polygon></svg>',
    play: '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"></polygon></svg>',
    pause: '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="4" width="4" height="16" rx="1"></rect><rect x="14" y="4" width="4" height="16" rx="1"></rect></svg>',
    nextFrame: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="5 4 15 12 5 20 5 4"></polygon></svg>',
    nextScene: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="5 4 15 12 5 20 5 4"></polygon><line x1="19" y1="5" x2="19" y2="19"></line></svg>'
  };

  // Nhãn + phụ đề cho 11 cảnh
  var SCENES = [
    { n: 1, title: 'Văn bản gốc', beat: 'default',
      sub: 'Bạn nhập một đoạn văn. Mọi thứ phía sau là cách máy hiểu nó thành chủ đề, rồi chọn ra bản tóm tắt.' },
    { n: 2, title: 'Tách câu', beat: 'default',
      sub: 'Mỗi câu trở thành một "văn bản nhỏ" (một document) cho mô hình LDA. Càng nhiều câu, chủ đề càng rõ.' },
    { n: 3, title: 'Tách từ & làm sạch', beat: 'default',
      sub: 'Từ ghép được gộp lại bằng từ điển; stopword bị bỏ vì chúng xuất hiện ở mọi câu và không mang chủ đề nào.' },
    { n: 4, title: 'Từ điển & ma trận câu × từ', beat: 'default',
      sub: 'Đếm số lần mỗi từ xuất hiện trong từng câu. Ô đậm = từ xuất hiện nhiều — đó là tín hiệu để LDA gom nhóm.' },
    { n: 5, title: 'Khởi tạo Gibbs', beat: 'default',
      sub: 'Máy gán NGẪU NHIÊN một chủ đề cho mỗi từ và đếm vào các bảng. Đây là điểm xuất phát hoàn toàn tùy ý — sẽ được sửa dần ở bước sau.' },
    { n: 6, title: 'Gibbs chi tiết — vòng 1, từng từ', beat: 'sweep',
      sub: 'Với từng từ: rút chủ đề cũ ra khỏi bộ đếm, tính xác suất có điều kiện, rồi lấy mẫu lại chủ đề mới.' },
    { n: 7, title: 'Gibbs tăng tốc — vòng 2 đến N', beat: 'accelerate',
      sub: 'Lặp lại hàng chục vòng, từng từ liên tục đổi chủ đề. Đường log-likelihood (ước lượng) cho thấy mô hình dần khớp với văn bản.' },
    { n: 8, title: 'Kết quả chủ đề', beat: 'default',
      sub: 'Sau khi hội tụ, mỗi chủ đề gom một nhóm từ. Nhãn chủ đề chính là vài từ đặc trưng đứng đầu.' },
    { n: 9, title: 'Chấm điểm từng câu', beat: 'default',
      sub: 'Câu nào giống chủ đề chung của cả đoạn và chứa từ dễ sinh ra sẽ được ưu tiên trong bản tóm tắt.' },
    { n: 10, title: 'Chọn câu bằng MMR', beat: 'default',
      sub: 'MMR vừa thưởng độ liên quan, vừa phạt câu trùng ý với những câu đã chọn — để bản tóm tắt có đủ nét khác nhau.' },
    { n: 11, title: 'Bản tóm tắt', beat: 'out',
      sub: 'Các câu được chọn được ghép lại theo ĐÚNG thứ tự gốc, không sắp xếp lại — đọc vẫn liền mạch.' }
  ];

  /* ------------------------------------------------------------------
     Tiện ích
     ------------------------------------------------------------------ */
  function $(sel, root) { return (root || document).querySelector(sel); }

  function esc(str) {
    return String(str === null || str === undefined ? '' : str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function fmt(n, digits) {
    var v = Number(n);
    if (!isFinite(v)) return '—';
    return v.toFixed(digits === undefined ? 3 : digits);
  }

  function pct(n, digits) {
    return fmt(Number(n) * 100, digits === undefined ? 1 : digits) + '%';
  }

  function topicColor(k) { return PALETTE[k % PALETTE.length]; }
  function topicClass(k) { return 'sum-tok--k' + (k % PALETTE.length); }

  function el(tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html !== undefined) n.innerHTML = html;
    return n;
  }

  /* ------------------------------------------------------------------
     Trạng thái
     ------------------------------------------------------------------ */
  var state = {
    data: null,
    frames: [],
    index: 0,
    playing: false,
    speed: 1,
    timer: null
  };

  var dom = {};

  /* ------------------------------------------------------------------
     Dựng danh sách frame (mỗi frame = 1 bước phát)
     ------------------------------------------------------------------ */
  function buildFrames(data) {
    var frames = [];
    var trace = data.traces && data.traces['1'] ? data.traces['1'] : [];
    var iters = Math.max(1, data.params.iterations);
    var mmrSteps = data.mmr.steps.length;
    var picked = data.summary.sentences.length;

    function push(scene, sub, extra) {
      var s = SCENES[scene - 1];
      var frame = {
        scene: scene, title: s.title, beat: s.beat,
        sub: sub || s.sub, data: extra || null
      };
      frames.push(frame);
    }

    push(1);
    push(2);

    // Cảnh 3: 4 bước — hiện tất gộp từ ghép → mờ stopword → ẩn stopword
    var stage3 = [
      'Các từ ghép trong từ điển ("xe điện", "ô nhiễm không khí", "trạm sạc") được gộp lại thành MỘT token — nếu tách rời, chúng sẽ thành những từ vựng rời rạc, mất nghĩa.',
      'Stopword (từ chức năng) bắt đầu mờ đi: chúng xuất hiện ở mọi câu nên không giúp phân biệt chủ đề.',
      'Stopword bị bỏ hẳn khỏi dữ liệu. Chỉ còn lại "ý nghĩa" của câu — đó là dữ liệu đưa vào mô hình LDA.',
      'Xong tiền xử lý: mỗi câu còn một danh sách token nội dung làm document cho Gibbs sampling.'
    ];
    for (var f = 0; f < 4; f++) push(3, stage3[f], { phase: f });

    // Cảnh 4: 2 bước — từ điển, rồi heatmap
    push(4, 'Từ điển là tập tất cả từ nội dung của cả đoạn. Mỗi từ được gán một mã để máy đếm.', { phase: 0 });
    push(4, 'Ma trận câu × từ: hàng là câu, cột là từ. Giá trị = số lần từ đó xuất hiện trong câu.', { phase: 1 });

    push(5);

    // Cảnh 6: mỗi token một frame
    for (var t = 0; t < trace.length; t++) {
      push(6, 'Xét từ thứ ' + (t + 1) + '/' + trace.length + ' — "' + trace[t].word + '". '
        + 'Vì sao từ này thuộc chủ đề này? Xác suất tính từ cả câu chứa nó lẫn tần suất từ đó toàn đoạn.', { traceIndex: t });
    }

    // Cảnh 7: mỗi vòng lặp một frame
    for (var it = 1; it <= iters; it++) {
      push(7, 'Vòng Gibbs ' + it + '/' + iters
        + ' — màu của từ vừa được cập nhật. log-likelihood ước lượng: '
        + fmt(data.history[it].log_likelihood, 2) + '.',
        { iteration: it });
    }

    push(8);
    push(9);

    // Cảnh 10: mỗi bước MMR một frame
    for (var m = 0; m < mmrSteps; m++) {
      push(10, data.mmr.steps[m].note, { stepIndex: m });
    }

    // Cảnh 11: 1 frame tổng quan + 1 frame cho mỗi câu được chọn
    push(11, 'Từ toàn bộ quá trình đã chọn ' + picked + '/' + data.summary.num_sentences_original
      + ' câu. Câu không được chọn mờ đi, câu được chọn chuyển sang khung tóm tắt.', { phase: 0 });
    for (var p = 0; p < picked; p++) {
      push(11, 'Câu ' + (data.summary.sentences[p].sentence_index + 1)
        + ' được chuyển vào bản tóm tắt — vẫn giữ nguyên vị trí so với câu gốc.', { phase: p + 1 });
    }

    return frames;
  }

  /* ------------------------------------------------------------------
     Dựng khung player (một lần)
     ------------------------------------------------------------------ */
  function buildShell() {
    var root = dom.player;
    root.innerHTML = '';
    root.className = 'sum-player';

    var head = el('div', 'sum-player-head');
    head.appendChild(el('span', 'sum-scene-num', 'Cảnh 1 / 11'));
    head.appendChild(el('h2', 'sum-scene-title', 'Văn bản gốc'));
    head.appendChild(el('span', 'sum-scene-step', ''));
    root.appendChild(head);

    root.appendChild(el('div', 'sum-stage'));

    root.appendChild(el('div', 'sum-subtitle', ''));

    var controls = el('div', 'sum-controls');
    var row = el('div', 'sum-controls-row');
    row.appendChild(btn('prevScene', ICONS.prevScene, 'Cảnh trước (Shift + ←)', 'sum-btn'));
    row.appendChild(btn('prevFrame', ICONS.prevFrame, 'Bước trước (←)', 'sum-btn'));
    row.appendChild(btn('play', ICONS.play + ' <span>Phát</span>', 'Phát hoặc tạm dừng (phím Space)', 'sum-btn sum-btn--play'));
    row.appendChild(btn('nextFrame', ICONS.nextFrame, 'Bước sau (→)', 'sum-btn'));
    row.appendChild(btn('nextScene', ICONS.nextScene, 'Cảnh sau (Shift + →)', 'sum-btn'));

    var speed = el('label', 'sum-speed');
    speed.appendChild(el('span', null, 'Tốc độ'));
    var sel = el('select');
    sel.id = 'sumSpeed';
    sel.setAttribute('aria-label', 'Tốc độ phát');
    [0.5, 1, 1.5, 2].forEach(function (v) {
      var o = document.createElement('option');
      o.value = String(v);
      o.textContent = v + '×';
      if (v === 1) o.selected = true;
      sel.appendChild(o);
    });
    speed.appendChild(sel);
    row.appendChild(speed);

    row.appendChild(el('span', 'sum-time', ''));
    controls.appendChild(row);

    var timeline = el('div', 'sum-timeline');
    timeline.id = 'sumTimeline';
    timeline.setAttribute('role', 'slider');
    timeline.setAttribute('tabindex', '0');
    timeline.setAttribute('aria-label', 'Thanh thời gian các bước');
    timeline.appendChild(el('div', 'sum-track'));
    timeline.appendChild(el('div', 'sum-track-fill'));
    timeline.appendChild(el('div', 'sum-track-head'));
    controls.appendChild(timeline);

    root.appendChild(controls);
    root.appendChild(el('ol', 'sum-chapters'));
  }

  function btn(id, label, title, cls) {
    var b = el('button', cls, label);
    b.id = 'sum' + id.charAt(0).toUpperCase() + id.slice(1);
    b.type = 'button';
    b.title = title + ' — phím tắt xem bên dưới';
    return b;
  }

  /* ------------------------------------------------------------------
     Các hàm render từng cảnh
     ------------------------------------------------------------------ */
  var RENDER = {};

  // --- Cảnh 1: văn bản gốc ---------------------------------------------
  RENDER[1] = function (data) {
    var wrap = el('div', 'sum-stage-inner');
    var s = data.stats;
    var paper = el('div', 'sum-sent');
    paper.appendChild(el('span', 'sum-sent-num', 'gốc'));
    var body = el('div', 'sum-sent-body');
    body.appendChild(el('div', 'sum-sent-text', esc(data.input.text)));
    paper.appendChild(body);
    wrap.appendChild(paper);

    wrap.appendChild(kpiRow([
      ['Số câu', s.num_sentences],
      ['Từ trong văn bản', s.num_raw_words],
      ['Sau khi bỏ stopword', s.num_kept_tokens + ' từ'],
      ['Từ vựng', s.vocab_size]
    ]));
    return wrap;
  };

  // --- Cảnh 2: tách câu --------------------------------------------------
  RENDER[2] = function (data) {
    var wrap = el('div', 'sum-stage-inner');
    data.sentences.forEach(function (s) {
      var row = el('div', 'sum-sent' + (s.is_empty ? ' is-empty' : ''));
      row.appendChild(el('span', 'sum-sent-num', 'Câu ' + (s.index + 1)));
      var body = el('div', 'sum-sent-body');
      body.appendChild(el('div', 'sum-sent-text', esc(s.text)));
      body.appendChild(el('span', 'sum-sent-note',
        s.is_empty
          ? 'Câu này không còn từ nội dung sau khi lọc — không tham gia mô hình'
          : s.num_tokens + ' token nội dung → document ' + (s.lda_doc + 1) + ' của LDA'));
      row.appendChild(body);
      wrap.appendChild(row);
    });
    return wrap;
  };

  // --- Cảnh 3: tách từ & làm sạch ---------------------------------------
  RENDER[3] = function (data, frame) {
    var phase = frame.data ? frame.data.phase : 0;
    var wrap = el('div', 'sum-stage-inner');

    data.sentences.forEach(function (s, si) {
      var row = el('div', 'sum-sent' + (s.is_empty ? ' is-empty' : ''));
      row.appendChild(el('span', 'sum-sent-num', 'Câu ' + (si + 1)));
      var body = el('div', 'sum-sent-body');

      var toks = el('div');
      (data.sentence_tokens[si] || []).forEach(function (tk) {
        var cls = 'sum-tok';
        if (tk.type === 'stopword') {
          cls += ' sum-tok--stop';
          if (phase === 2) cls += ' is-fading';
          if (phase >= 3) cls += ' is-gone';
        } else if (tk.type === 'number') {
          cls += ' sum-tok--num';
        } else if (tk.type === 'compound') {
          cls += ' sum-tok--dict';
        }
        var t = el('span', cls, esc(tk.text));
        if (tk.type === 'compound' && phase === 1) {
          t.style.boxShadow = '0 0 0 3px ' + PALETTE[0] + '33';
        }
        if (tk.type === 'stopword' && phase >= 3) {
          t.setAttribute('aria-hidden', 'true');
        }
        toks.appendChild(t);
      });
      body.appendChild(toks);
      row.appendChild(body);
      wrap.appendChild(row);
    });

    var key = el('div', 'sum-theta-key');
    key.appendChild(keyItem(PALETTE[0], 'từ ghép trong từ điển'));
    key.appendChild(keyItem('var(--color-text)', 'từ đơn (giữ nguyên)'));
    key.appendChild(keyItem('var(--color-text-subtle)', 'stopword / số (bị bỏ)'));
    wrap.appendChild(key);
    return wrap;
  };

  // --- Cảnh 4: từ điển + heatmap -----------------------------------------
  RENDER[4] = function (data, frame) {
    var phase = frame.data ? frame.data.phase : 0;
    var wrap = el('div', 'sum-stage-inner');

    if (phase === 0) {
      var V = data.heatmap.vocab;
      wrap.appendChild(el('h3', null, 'Từ điển (' + V.length + ' từ nội dung, đã loại trùng)'));
      var cloud = el('div');
      V.slice(0, 60).forEach(function (w) {
        cloud.appendChild(el('span', 'sum-tok sum-tok--dict', esc(w)));
      });
      wrap.appendChild(cloud);
      if (V.length > 60) {
        wrap.appendChild(el('p', 'sum-formula-note',
          '… và ' + (V.length - 60) + ' từ nữa. Mỗi từ được gán một mã số để máy đếm.'));
      }
      return wrap;
    }

    // heatmap
    var vocab = data.heatmap.vocab;
    var matrix = data.heatmap.matrix;
    var totals = vocab.map(function (_, j) {
      return matrix.reduce(function (a, row) { return a + row[j]; }, 0);
    });
    var order = vocab.map(function (_, j) { return j; })
      .sort(function (a, b) { return totals[b] - totals[a]; });
    var cols = order.slice(0, Math.min(40, vocab.length));
    var max = Math.max(1, data.heatmap.max_count);

    var scroll = el('div', 'sum-heatmap-scroll');
    var grid = el('div', 'sum-heatmap');
    grid.style.gridTemplateColumns = '26px repeat(' + cols.length + ', 15px)';

    // nhãn cột
    grid.appendChild(el('div'));
    cols.forEach(function (j) {
      grid.appendChild(el('div', 'sum-hm-axis', esc(vocab[j])));
    });

    // từng câu
    matrix.forEach(function (row, i) {
      grid.appendChild(el('div', 'sum-hm-rowlabel', 'C' + (i + 1)));
      cols.forEach(function (j) {
        var v = row[j] || 0;
        var cell = el('div', 'sum-hm-cell' + (v ? ' is-counted' : ''));
        if (v) {
          var ratio = v / max;
          cell.style.background = heatColor(ratio);
          cell.title = 'Câu ' + (i + 1) + ' · "' + vocab[j] + '": ' + v + ' lần';
        } else {
          cell.title = 'Câu ' + (i + 1) + ' · "' + vocab[j] + '": không có';
        }
        grid.appendChild(cell);
      });
    });

    scroll.appendChild(grid);
    wrap.appendChild(el('h3', null, 'Ma trận câu × từ — ' + cols.length + ' từ phổ biến nhất'
      + (vocab.length > 40 ? ' (trong tổng ' + vocab.length + ')' : '')));
    wrap.appendChild(scroll);

    var legend = el('div', 'sum-legend');
    legend.appendChild(el('span', null, 'Số lần xuất hiện'));
    var scale = el('div', 'sum-legend-scale');
    [0, 0.25, 0.5, 0.75, 1].forEach(function (r) {
      var st = el('div', 'sum-legend-step');
      st.style.background = heatColor(r);
      scale.appendChild(st);
    });
    legend.appendChild(scale);
    legend.appendChild(el('span', null, '0 → ' + max + ' lần'));
    wrap.appendChild(legend);
    return wrap;
  };

  function heatColor(ratio) {
    if (ratio <= 0) return 'var(--color-surface-muted)';
    // thang teal: nhạt -> đậm
    var steps = ['#CCFBF1', '#99F6E4', '#5EEAD4', '#2DD4BF', '#14B8A6', '#0D9488', '#115E59'];
    var idx = Math.min(steps.length - 1, Math.floor(ratio * steps.length));
    return steps[idx];
  }

  // --- Cảnh 5: khởi tạo Gibbs --------------------------------------------
  RENDER[5] = function (data) {
    var init = data.initial_counts;
    var K = data.params.num_topics;
    var wrap = el('div', 'sum-stage-inner');

    var cols = el('div');
    cols.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:var(--space-4)';

    // Cột 1: token tô màu chủ đề ngẫu nhiên + bảng n_k
    var leftBox = el('div');
    leftBox.appendChild(el('h3', null,
      'Gán chủ đề ngẫu nhiên cho ' + init.n_d.reduce(function (a, b) { return a + b; }, 0) + ' từ'));
    var rows = el('div');
    rows.style.maxHeight = '230px';
    rows.style.overflowY = 'auto';
    data.sentences.forEach(function (s, si) {
      if (s.is_empty) return;
      var r = el('div', 'sum-sent');
      r.appendChild(el('span', 'sum-sent-num', 'Câu ' + (si + 1)));
      var body = el('div', 'sum-sent-body');
      var line = el('div');
      init.assignments[s.lda_doc].forEach(function (k, ti) {
        var w = (data.sentence_tokens[si] || []).filter(function (t) {
          return t.type === 'compound' || t.type === 'word';
        })[ti];
        if (!w) return;
        line.appendChild(el('span', 'sum-tok ' + topicClass(k), esc(w.text)));
      });
      body.appendChild(line);
      r.appendChild(body);
      rows.appendChild(r);
    });
    leftBox.appendChild(rows);

    leftBox.appendChild(el('h3', null, 'Bảng đếm n(k) — tổng số từ của mỗi chủ đề', 'margin-top:var(--space-4)'));
    var kt = el('table', 'sum-table');
    kt.innerHTML = '<thead><tr><th>Chủ đề</th><th class="num">n(k)</th><th class="num">n(k)/tổng</th></tr></thead>';
    var tb = el('tbody');
    var totalK = init.n_k.reduce(function (a, b) { return a + b; }, 0) || 1;
    init.n_k.forEach(function (v, k) {
      var tr = el('tr');
      tr.innerHTML = '<td><span class="sum-topic-swatch" style="display:inline-block;background:'
        + topicColor(k) + '"></span> Chủ đề ' + (k + 1) + '</td><td class="num">' + v
        + '</td><td class="num">' + pct(v / totalK) + '</td>';
      tb.appendChild(tr);
    });
    kt.appendChild(tb);
    var twk = el('div', 'sum-table-wrap');
    twk.appendChild(kt);
    leftBox.appendChild(twk);
    cols.appendChild(leftBox);

    // Cột 2: bảng n_dk (câu × chủ đề) + bảng n_kw (từ × chủ đề)
    var rightBox = el('div');
    rightBox.appendChild(el('h3', null, 'Bảng đếm n(d, k) — số từ của mỗi câu theo chủ đề'));
    rightBox.appendChild(countTable(data, init.n_dk, K, 'd', 'Câu '));

    rightBox.appendChild(el('h3', null, 'Bảng đếm n(k, w) — số lần từ theo chủ đề (top từ)', 'margin-top:var(--space-4)'));
    rightBox.appendChild(wordTopicTable(data, init, K));
    cols.appendChild(rightBox);

    wrap.appendChild(cols);

    var note = el('p', 'sum-formula-note',
      'Mọi phân bố này là ngẫu nhiên ở thời điểm khởi tạo — chưa có chủ đề nào "đúng". '
      + 'Vòng Gibbs 1 và các vòng tiếp theo sẽ liên tục rút token và tính lại xác suất có điều kiện.');
    wrap.appendChild(note);
    return wrap;
  };

  function countTable(data, n_dk, K, rowLabel, prefix) {
    var wrap = el('div', 'sum-table-wrap');
    var t = el('table', 'sum-table');
    var head = '<thead><tr><th>' + prefix + '</th>';
    for (var k = 0; k < K; k++) head += '<th class="num">k=' + (k + 1) + '</th>';
    head += '<th class="num">Tổng</th></tr></thead>';
    t.innerHTML = head;
    var tb = el('tbody');
    n_dk.forEach(function (row, d) {
      var tr = el('tr');
      var cells = '<td>' + (rowLabel === 'd' ? 'Câu ' + (d + 1) : d) + '</td>';
      var sum = 0;
      row.forEach(function (v) { sum += v; });
      row.forEach(function (v, k) {
        cells += '<td class="num" style="color:' + topicColor(k) + '">' + v + '</td>';
      });
      cells += '<td class="num">' + sum + '</td>';
      tr.innerHTML = cells;
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    wrap.appendChild(t);
    return wrap;
  }

  function wordTopicTable(data, init, K) {
    var wrap = el('div', 'sum-table-wrap');
    var t = el('table', 'sum-table');
    var head = '<thead><tr><th>Từ nội dung</th>';
    for (var k = 0; k < K; k++) {
      head += '<th class="num" style="color:' + topicColor(k) + '">k=' + (k + 1) + '</th>';
    }
    head += '<th class="num">Tổng</th></tr></thead>';
    t.innerHTML = head;
    var tb = el('tbody');

    var rows = init.top_kw_table || [];
    if (!rows.length && init.n_kw && init.vocab) {
      var countsByWord = {};
      init.vocab.forEach(function (w) { countsByWord[w] = new Array(K).fill(0); });
      init.n_kw.forEach(function (topicList, k) {
        topicList.forEach(function (item) {
          if (countsByWord[item.word]) countsByWord[item.word][k] = item.count;
        });
      });
      rows = init.vocab.map(function (w) {
        var counts = countsByWord[w] || new Array(K).fill(0);
        return {
          word: w,
          counts: counts,
          total: counts.reduce(function (a, b) { return a + b; }, 0)
        };
      }).sort(function (a, b) { return b.total - a.total; });
    }

    rows.slice(0, 10).forEach(function (item) {
      var tr = el('tr');
      var cells = '<td><b>' + esc(item.word) + '</b></td>';
      item.counts.forEach(function (c, kk) {
        cells += '<td class="num" style="color:' + (c > 0 ? topicColor(kk) : 'var(--color-text-subtle)') + '">' + c + '</td>';
      });
      cells += '<td class="num">' + item.total + '</td>';
      tr.innerHTML = cells;
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    wrap.appendChild(t);
    return wrap;
  }

  // --- Cảnh 6: Gibbs chi tiết vòng 1 -------------------------------------
  RENDER[6] = function (data, frame) {
    var trace = data.traces['1'];
    var idx = frame.data ? frame.data.traceIndex : 0;
    var t = trace[Math.min(idx, trace.length - 1)];
    var K = data.params.num_topics;
    var alpha = data.params.alpha, beta = data.params.beta, V = data.vocab.length;
    var wrap = el('div', 'sum-stage-inner');

    // hàng câu, highlight token đang xét
    var sIdx = data.sentences.findIndex(function (s) { return s.lda_doc === t.d; });
    var row = el('div', 'sum-sent');
    row.appendChild(el('span', 'sum-sent-num', 'Câu ' + (sIdx + 1)));
    var body = el('div', 'sum-sent-body');
    var line = el('div');
    var kept = (data.sentence_tokens[sIdx] || []).filter(function (x) {
      return x.type === 'compound' || x.type === 'word';
    });
    kept.forEach(function (tk, ti) {
      var k = assignmentsBefore(data, t.d, ti);
      var cls = 'sum-tok ' + topicClass(k === null ? 0 : k);
      if (ti === t.i) cls += ' is-active';
      if (ti === t.i && k !== null && k !== t.k_new) cls += ' is-changed';
      line.appendChild(el('span', cls, esc(tk.text)));
    });
    body.appendChild(line);
    body.appendChild(el('span', 'sum-sent-note',
      'Vị trí ' + (t.i + 1) + ' trong câu — chủ đề cũ: ' + (t.k_old + 1)
      + ' → chủ đề mới: ' + (t.k_new + 1) + (t.changed ? ' (đổi)' : ' (giữ nguyên)')));
    row.appendChild(body);
    wrap.appendChild(row);

    var grid = el('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:var(--space-4)';

    // công thức
    var fx = el('div', 'sum-formula');
    var html = 'P(k) ∝ (n_dk + α) · (n_kw + β) / (n_k + V·β)<br>';
    for (var k = 0; k < K; k++) {
      html += '<span class="k' + k + '">k=' + (k + 1) + '</span>: ('
        + t.n_dk[k] + ' + ' + alpha + ') · ('
        + t.n_kw[k] + ' + ' + beta + ') / ('
        + t.n_k[k] + ' + ' + V + '·' + beta + ') = '
        + '<span class="num">' + fmt(t.raw[k], 5) + '</span>'
        + (k === t.k_new ? ' <span class="win">← chọn</span>' : '')
        + '<br>';
    }
    html += 'Tổng = ' + fmt(t.raw.reduce(function (a, b) { return a + b; }, 0), 5)
      + '  →  chuẩn hoá → r = ' + fmt(t.r, 4) + ' rơi vào k = ' + (t.k_new + 1);
    fx.innerHTML = html;
    grid.appendChild(fx);

    // thanh xác suất
    var bars = el('div');
    bars.appendChild(el('h3', null, 'Xác suất có điều kiện P(k | phần còn lại)'));
    var wrapBars = el('div', 'sum-bars');
    for (var k2 = 0; k2 < K; k2++) {
      var br = el('div', 'sum-bar-row');
      br.appendChild(el('span', 'sum-bar-label', 'Chủ đề ' + (k2 + 1) + (k2 === t.k_new ? ' ✓' : '')));
      var track = el('div', 'sum-bar-track');
      var fill = el('div', 'sum-bar-fill');
      fill.style.width = (t.probs[k2] * 100).toFixed(1) + '%';
      fill.style.background = topicColor(k2);
      track.appendChild(fill);
      br.appendChild(track);
      br.appendChild(el('span', 'sum-bar-value', fmt(t.probs[k2], 4)));
      wrapBars.appendChild(br);
    }
    bars.appendChild(wrapBars);
    bars.appendChild(el('p', 'sum-formula-note',
      'Rút chủ đề cũ khỏi bộ đếm trước khi tính — nếu không, từ đó sẽ "tự dành phiếu" cho chính nó.'));
    grid.appendChild(bars);
    wrap.appendChild(grid);

    // bảng bộ đếm sau khi rút
    var tbl = el('div');
    tbl.appendChild(el('h3', null, 'Bộ đếm sau khi rút token "' + esc(t.word) + '" (trước khi gán lại)'));
    var tw = el('div', 'sum-table-wrap');
    var tb2 = el('table', 'sum-table');
    var head = '<thead><tr><th>Đại lượng</th>';
    for (var k3 = 0; k3 < K; k3++) head += '<th class="num">k=' + (k3 + 1) + '</th>';
    head += '</tr></thead>';
    tb2.innerHTML = head;
    var body2 = el('tbody');
    [['n_dk', 'n(d, ·) — từ trong câu d'],
     ['n_kw', 'n(·, w) — số lần "' + esc(t.word) + '" toàn đoạn'],
     ['n_k', 'n(·) — tổng từ của chủ đề']].forEach(function (rowDef) {
      var tr = el('tr');
      var cells = '<td>' + rowDef[1] + '</td>';
      t[rowDef[0]].forEach(function (v, kk) {
        cells += '<td class="num" style="color:' + topicColor(kk) + '">' + v + '</td>';
      });
      tr.innerHTML = cells;
      body2.appendChild(tr);
    });
    tb2.appendChild(body2);
    tw.appendChild(tb2);
    tbl.appendChild(tw);
    wrap.appendChild(tbl);

    return wrap;
  };

  /**
   * Màu của token (d, i) TRƯỚC khi token đó được xét lại ở vòng 1.
   * Vì snapshot[0] chính là trạng thái khởi tạo và vòng 1 đi đúng thứ tự,
   * các token trước vị trí i đã đổi, các token sau vị trí i chưa đổi.
   */
  function assignmentsBefore(data, d, i) {
    var trace = data.traces['1'];
    for (var x = 0; x < trace.length; x++) {
      var t = trace[x];
      if (t.d === d && t.i === i) {
        // token này chưa bị xét lại -> dùng k_old
        return t.k_old;
      }
      if (t.d === d && t.i > i) break; // token phía sau chưa đổi
    }
    // nếu không tìm thấy (không có trace) -> dùng snapshot khởi tạo
    return data.initial.assignments[d][i];
  }

  function findFrameForIteration(it) {
    for (var i = 0; i < state.frames.length; i++) {
      var f = state.frames[i];
      if (f.scene === 7 && f.data && f.data.iteration === it) return i;
    }
    return -1;
  }

  // --- Cảnh 7: tăng tốc -------------------------------------------------
  RENDER[7] = function (data, frame) {
    var it = frame.data ? frame.data.iteration : 1;
    var snap = data.history[it];
    var K = data.params.num_topics;
    var wrap = el('div', 'sum-stage-inner');

    // Thanh trượt tua vòng lặp Gibbs (tái sử dụng ý tưởng UI của demo cũ Phần 1)
    var scrubberCard = el('div', 'sum-scrubber-card');
    var sHead = el('div', 'sum-scrubber-header');
    sHead.innerHTML = '<div><strong>Tua nhanh qua các vòng lặp Gibbs</strong> <span class="sum-formula-note">(kéo thanh trượt để quan sát cập nhật)</span></div>'
      + '<span class="sum-scrubber-badge">Vòng ' + it + ' / ' + data.params.iterations + '</span>';
    scrubberCard.appendChild(sHead);

    var sRow = el('div', 'sum-scrubber-row');
    var slider = el('input', 'sum-scrubber-slider');
    slider.type = 'range';
    slider.min = '1';
    slider.max = String(data.params.iterations);
    slider.value = String(it);
    slider.step = '1';
    slider.setAttribute('aria-label', 'Vòng lặp Gibbs');
    sRow.appendChild(slider);
    scrubberCard.appendChild(sRow);
    wrap.appendChild(scrubberCard);

    slider.addEventListener('input', function (e) {
      var targetIt = parseInt(e.target.value, 10);
      var targetIdx = findFrameForIteration(targetIt);
      if (targetIdx >= 0) {
        goTo(targetIdx);
      }
    });

    // token theo vòng (tô sáng token vừa đổi chủ đề so với vòng trước)
    var prev = data.history[it - 1];
    var rows = el('div');
    rows.style.cssText = 'display:flex;flex-direction:column;gap:2px';
    data.sentences.forEach(function (s, si) {
      if (s.is_empty) return;
      var r = el('div', 'sum-sent');
      r.appendChild(el('span', 'sum-sent-num', 'Câu ' + (si + 1)));
      var line = el('div');
      var kept = (data.sentence_tokens[si] || []).filter(function (x) {
        return x.type === 'compound' || x.type === 'word';
      });
      kept.forEach(function (tk, ti) {
        var k = snap.assignments[s.lda_doc][ti];
        var cls = 'sum-tok ' + topicClass(k);
        if (prev.assignments[s.lda_doc][ti] !== k) cls += ' is-changed';
        line.appendChild(el('span', cls, esc(tk.text)));
      });
      r.appendChild(line);
      rows.appendChild(r);
    });
    wrap.appendChild(rows);

    // đường log-likelihood
    wrap.appendChild(el('h3', null,
      'log-likelihood ước lượng (giá trị cao hơn = mô hình khớp văn bản hơn)'));
    wrap.appendChild(llChart(data, it));
    wrap.appendChild(el('p', 'sum-formula-note',
      'Đây là log-likelihood ước lượng từ θ và φ ở từng vòng, dùng để minh hoạ xu hướng hội tụ — '
      + 'không phải log-likelihood tuyệt đối của bài toán Bayes đầy đủ.'));

    return wrap;
  };

  function llChart(data, current) {
    var W = 640, H = 150, padL = 46, padR = 10, padT = 10, padB = 24;
    var lls = data.history.map(function (h) { return h.log_likelihood; });
    var min = Math.min.apply(null, lls), max = Math.max.apply(null, lls);
    var span = (max - min) || 1;

    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.cssText = 'width:100%;height:150px;display:block';
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'Đường cong log-likelihood theo số vòng Gibbs');

    function X(i) { return padL + (i / Math.max(1, lls.length - 1)) * (W - padL - padR); }
    function Y(v) { return padT + (1 - (v - min) / span) * (H - padT - padB); }

    // lưới ngang
    [0, 0.5, 1].forEach(function (f) {
      var v = min + f * span;
      var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', padL); line.setAttribute('x2', W - padR);
      line.setAttribute('y1', Y(v)); line.setAttribute('y2', Y(v));
      line.setAttribute('stroke', '#E5E7EB');
      line.setAttribute('stroke-width', '1');
      svg.appendChild(line);
      var txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      txt.setAttribute('x', 4); txt.setAttribute('y', Y(v) + 4);
      txt.setAttribute('font-size', '10');
      txt.setAttribute('fill', '#9CA3AF');
      txt.setAttribute('font-family', 'JetBrains Mono, monospace');
      txt.textContent = v.toFixed(0);
      svg.appendChild(txt);
    });

    // đường
    var d = lls.map(function (v, i) { return (i ? 'L' : 'M') + X(i) + ' ' + Y(v); }).join(' ');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', PALETTE[0]);
    path.setAttribute('stroke-width', '2');
    path.setAttribute('stroke-linejoin', 'round');
    svg.appendChild(path);

    // phần đã phát
    var dPast = lls.slice(0, current + 1)
      .map(function (v, i) { return (i ? 'L' : 'M') + X(i) + ' ' + Y(v); }).join(' ');
    var past = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    past.setAttribute('d', dPast);
    past.setAttribute('fill', 'none');
    past.setAttribute('stroke', PALETTE[1]);
    past.setAttribute('stroke-width', '2.5');
    svg.appendChild(past);

    // điểm hiện tại
    var dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    dot.setAttribute('cx', X(current));
    dot.setAttribute('cy', Y(lls[current]));
    dot.setAttribute('r', '4');
    dot.setAttribute('fill', PALETTE[1]);
    svg.appendChild(dot);

    var lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    lbl.setAttribute('x', Math.min(X(current) + 8, W - 60));
    lbl.setAttribute('y', Math.max(Y(lls[current]) - 8, 12));
    lbl.setAttribute('font-size', '10');
    lbl.setAttribute('font-weight', '600');
    lbl.setAttribute('fill', PALETTE[1]);
    lbl.setAttribute('font-family', 'JetBrains Mono, monospace');
    lbl.textContent = lls[current].toFixed(1);
    svg.appendChild(lbl);

    return svg;
  }

  // --- Cảnh 8: kết quả chủ đề -------------------------------------------
  RENDER[8] = function (data) {
    var K = data.params.num_topics;
    var wrap = el('div', 'sum-stage-inner');

    var cards = el('div', 'sum-topic-cards');
    for (var k = 0; k < K; k++) {
      var card = el('div', 'sum-topic-card');
      var head = el('div', 'sum-topic-head');
      var sw = el('span', 'sum-topic-swatch', '');
      sw.style.background = topicColor(k);
      head.appendChild(sw);
      head.appendChild(el('span', 'sum-topic-name', 'Chủ đề ' + (k + 1)));
      card.appendChild(head);
      card.appendChild(el('div', 'sum-formula-note', 'Nhãn: ' + esc(data.topics.labels[k])));

      var words = el('div', 'sum-topic-words');
      var top = data.topics.top_words[k].slice(0, 6);
      var maxP = top.length ? top[0][1] : 1;
      top.forEach(function (pair) {
        var w = el('div', 'sum-topic-word');
        w.appendChild(el('span', null, esc(pair[0])));
        w.appendChild(el('span', null, fmt(pair[1], 4)));
        var bar = el('div', 'sum-topic-word-bar');
        var fill = el('i');
        fill.style.width = ((pair[1] / (maxP || 1)) * 100).toFixed(1) + '%';
        fill.style.background = topicColor(k);
        bar.appendChild(fill);
        w.appendChild(bar);
        words.appendChild(w);
      });
      card.appendChild(words);
      cards.appendChild(card);
    }
    wrap.appendChild(cards);

    // theta từng câu + pi
    wrap.appendChild(el('h3', null, 'Phân bố chủ đề của từng câu θ (đã hội tụ)'));
    var list = el('div', 'sum-theta-list');
    data.scores.forEach(function (sc) {
      var s = data.sentences[sc.sentence_index];
      var r = el('div', 'sum-theta-row');
      r.appendChild(el('span', 'sum-hm-rowlabel', 'C' + (sc.sentence_index + 1)));
      var stack = el('div', 'sum-theta-stack');
      if (sc.eligible) {
        sc.theta.forEach(function (v, k) {
          var seg = el('i');
          seg.style.width = (v * 100).toFixed(1) + '%';
          seg.style.background = topicColor(k);
          seg.title = 'Chủ đề ' + (k + 1) + ': ' + pct(v);
          stack.appendChild(seg);
        });
      } else {
        stack.appendChild(el('i')).style.background = 'var(--color-surface-muted)';
      }
      r.appendChild(stack);
      list.appendChild(r);
    });
    wrap.appendChild(list);

    var key = el('div', 'sum-theta-key');
    for (var k2 = 0; k2 < K; k2++) {
      key.appendChild(keyItem(topicColor(k2), 'Chủ đề ' + (k2 + 1)));
    }
    key.appendChild(keyItem('var(--color-text-muted)',
      'π toàn đoạn = ' + data.topics.pi.map(function (v) { return fmt(v, 2); }).join(' / ')));
    wrap.appendChild(key);
    return wrap;
  };

  // --- Cảnh 9: chấm điểm câu --------------------------------------------
  RENDER[9] = function (data) {
    var wrap = el('div', 'sum-stage-inner');
    wrap.appendChild(el('h3', null,
      'Điểm = 0,6 × cos(θ câu, π toàn đoạn) + 0,4 × xác suất trung bình của các từ trong câu, '
      + 'rồi nhân hệ số độ dài'));

    var maxScore = Math.max.apply(null, data.scores.map(function (s) { return s.score; }));

    var list = el('div', 'sum-score-list');
    data.scores.forEach(function (sc) {
      var picked = data.mmr.selected.indexOf(sc.sentence_index) >= 0;
      var r = el('div', 'sum-score-row' + (picked ? ' is-picked' : ''));
      r.appendChild(el('span', 'sum-hm-rowlabel', 'C' + (sc.sentence_index + 1)));
      var bar = el('div', 'sum-score-bar');
      if (sc.eligible) {
        var w = (sc.score / (maxScore || 1)) * 100;
        var a = el('i');
        a.style.width = ((w * 0.6) / 1).toFixed(1) + '%';
        a.style.background = PALETTE[0];
        a.title = '0,6 × cos = ' + fmt(0.6 * sc.cosine, 3);
        var b = el('i');
        b.style.width = ((w * 0.4) / 1).toFixed(1) + '%';
        b.style.background = PALETTE[1];
        b.title = '0,4 × xác suất = ' + fmt(0.4 * sc.token_prob, 4);
        bar.appendChild(a);
        bar.appendChild(b);
        if (sc.length_factor < 1) {
          var c = el('i');
          c.style.width = '10px';
          c.style.background = PALETTE[2];
          c.title = 'Phạt độ dài: ×' + sc.length_factor + ' — ' + sc.reason;
          bar.appendChild(c);
        }
      } else {
        var d = el('i');
        d.style.width = '100%';
        d.style.background = 'var(--color-surface-muted)';
        bar.appendChild(d);
      }
      r.appendChild(bar);
      r.appendChild(el('span', 'sum-score-total', sc.eligible ? fmt(sc.score, 3) : '—'));
      list.appendChild(r);
    });
    wrap.appendChild(list);

    var key = el('div', 'sum-theta-key');
    key.appendChild(keyItem(PALETTE[0], '0,6 × cos(θ, π)'));
    key.appendChild(keyItem(PALETTE[1], '0,4 × xác suất từ'));
    key.appendChild(keyItem(PALETTE[2], 'phạt câu quá ngắn/dài'));
    wrap.appendChild(key);

    // bảng chi tiết
    var tw = el('div', 'sum-table-wrap');
    var t = el('table', 'sum-table');
    t.innerHTML = '<thead><tr><th>Câu</th><th class="num">cos(θ, π)</th>'
      + '<th class="num">0,6 × cos</th><th class="num">xác suất TB</th>'
      + '<th class="num">0,4 × p</th><th class="num">hệ số dài</th>'
      + '<th class="num">Điểm</th><th>Ghi chú</th></tr></thead>';
    var tb = el('tbody');
    data.scores.forEach(function (sc) {
      var picked = data.mmr.selected.indexOf(sc.sentence_index) >= 0;
      var tr = el('tr', picked ? 'is-picked' : '');
      tr.innerHTML = '<td>Câu ' + (sc.sentence_index + 1) + '</td>'
        + '<td class="num">' + (sc.eligible ? fmt(sc.cosine, 3) : '—') + '</td>'
        + '<td class="num">' + (sc.eligible ? fmt(0.6 * sc.cosine, 3) : '—') + '</td>'
        + '<td class="num">' + (sc.eligible ? fmt(sc.token_prob, 5) : '—') + '</td>'
        + '<td class="num">' + (sc.eligible ? fmt(0.4 * sc.token_prob, 4) : '—') + '</td>'
        + '<td class="num">' + (sc.eligible ? '×' + sc.length_factor : '—') + '</td>'
        + '<td class="num">' + (sc.eligible ? fmt(sc.score, 3) : '—') + '</td>'
        + '<td>' + esc(sc.reason || (picked ? 'được chọn' : '')) + '</td>';
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    tw.appendChild(t);
    wrap.appendChild(tw);
    return wrap;
  };

  // --- Cảnh 10: MMR -----------------------------------------------------
  RENDER[10] = function (data, frame) {
    var stepIdx = frame.data ? frame.data.stepIndex : 0;
    var wrap = el('div', 'sum-stage-inner');
    wrap.appendChild(el('h3', null,
      'MMR: chọn câu có điểm cao, nhưng bị trừ điểm nếu ý nói giống câu đã chọn (λ = '
      + data.mmr.lambda + ')'));

    data.mmr.steps.forEach(function (st, i) {
      var card = el('div', 'sum-mmr-step');
      if (i === stepIdx) card.style.borderColor = PALETTE[0];
      var head = el('div', 'sum-mmr-head');
      head.appendChild(el('span', 'sum-mmr-badge', 'Bước ' + st.step));
      head.appendChild(el('b', null, 'Chọn câu ' + (st.chosen + 1)
        + ' (điểm ' + fmt(st.chosen_score, 3) + ')'));
      card.appendChild(head);
      card.appendChild(el('p', 'sum-mmr-note', esc(st.note)));

      if (st.candidates && st.candidates.length) {
        var tw = el('div', 'sum-table-wrap');
        var t = el('table', 'sum-table');
        t.innerHTML = '<thead><tr><th>Câu</th><th class="num">độ liên quan</th>'
          + '<th class="num">trùng ý (cos)</th><th class="num">MMR</th><th>Kết quả</th></tr></thead>';
        var tb = el('tbody');
        st.candidates.slice(0, 6).forEach(function (c) {
          var won = c.sentence_index === st.chosen;
          var tr = el('tr', won ? 'is-picked' : '');
          tr.innerHTML = '<td>Câu ' + (c.sentence_index + 1) + '</td>'
            + '<td class="num">' + fmt(c.relevance, 3) + '</td>'
            + '<td class="num">' + fmt(c.redundancy, 3)
            + (c.redundant_with !== null ? ' (với câu ' + (c.redundant_with + 1) + ')' : '') + '</td>'
            + '<td class="num">' + fmt(c.mmr, 3) + '</td>'
            + '<td>' + (won ? 'được chọn' : 'giữ lại dự phòng') + '</td>';
          tb.appendChild(tr);
        });
        t.appendChild(tb);
        tw.appendChild(t);
        card.appendChild(tw);
      }
      wrap.appendChild(card);
    });

    // các câu bị loại
    wrap.appendChild(el('h3', null, 'Vì sao các câu còn lại không được chọn'));
    var reasons = el('ul');
    reasons.style.cssText = 'margin:0;padding-left:18px;font-size:var(--text-xs);color:var(--color-text-secondary);line-height:1.8';
    data.mmr.rejected.forEach(function (r) {
      var li = el('li', null, 'Câu ' + (r.sentence_index + 1) + ': ' + esc(r.reason));
      reasons.appendChild(li);
    });
    wrap.appendChild(reasons);
    return wrap;
  };

  // --- Cảnh 11: bản tóm tắt --------------------------------------------
  RENDER[11] = function (data, frame) {
    var phase = frame.data ? frame.data.phase : 0;
    var pickedSoFar = data.mmr.selected.slice(0, Math.max(0, phase));
    var wrap = el('div', 'sum-stage-inner');

    var grid = el('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:var(--space-4);align-items:start;';

    // 1. Văn bản gốc
    var src = el('div', 'sum-source');
    src.appendChild(el('h3', null, 'Văn bản gốc (câu không chọn mờ dần)'));
    var srcList = el('div');
    srcList.style.cssText = 'display:flex;flex-direction:column;gap:6px;';
    data.sentences.forEach(function (s) {
      var isPicked = pickedSoFar.indexOf(s.index) >= 0;
      var rowCls = 'sum-sent' + (s.is_empty ? ' is-empty' : '');
      if (phase > 0) {
        if (isPicked) rowCls += ' is-picked-source';
        else rowCls += ' is-dim';
      }
      var row = el('div', rowCls);
      row.appendChild(el('span', 'sum-sent-num', 'Câu ' + (s.index + 1) + (isPicked ? ' ✓' : '')));
      var body = el('div', 'sum-sent-body');
      body.appendChild(el('div', 'sum-sent-text', esc(s.text)));
      row.appendChild(body);
      srcList.appendChild(row);
    });
    src.appendChild(srcList);
    grid.appendChild(src);

    // 2. Khung tóm tắt
    var box = el('div', 'sum-summary-box');
    box.appendChild(el('h3', null, 'Bản tóm tắt theo thứ tự gốc (' + pickedSoFar.length
      + '/' + data.summary.num_sentences_original + ' câu)'));
    if (phase === 0) {
      box.appendChild(el('div', 'sum-summary-empty',
        'Các câu được chọn qua thuật toán MMR sẽ lần lượt bay vào đây theo đúng thứ tự gốc…'));
    } else {
      var linesWrap = el('div', 'sum-summary-lines');
      pickedSoFar.forEach(function (idx, orderIdx) {
        var s = data.sentences[idx];
        var isNewest = (orderIdx === pickedSoFar.length - 1);
        var line = el('div', 'sum-summary-line' + (isNewest ? ' is-entering' : ''));
        line.innerHTML = '<span class="sum-summary-badge">Câu ' + (s.index + 1) + '</span> '
          + '<span class="sum-summary-text">' + esc(s.text) + '</span>';
        linesWrap.appendChild(line);
      });
      box.appendChild(linesWrap);
    }
    grid.appendChild(box);
    wrap.appendChild(grid);

    // 3. KPI tỉ lệ nén
    var savingsPct = Math.round((1 - data.summary.num_words_summary / Math.max(1, data.summary.num_words_original)) * 100);
    wrap.appendChild(kpiRow([
      ['Từ gốc', data.summary.num_words_original + ' từ'],
      ['Từ tóm tắt', data.summary.num_words_summary + ' từ'],
      ['Số câu chọn', data.summary.num_sentences_summary + ' / ' + data.summary.num_sentences_original + ' câu'],
      ['Tỉ lệ nén', data.summary.compression_ratio + '× (Giảm ' + savingsPct + '%)']
    ]));

    return wrap;
  };

  /* ------------------------------------------------------------------
     Khối dùng chung
     ------------------------------------------------------------------ */
  function kpiRow(pairs) {
    var g = el('div');
    g.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:var(--space-3)';
    pairs.forEach(function (p) {
      var c = el('div');
      c.style.cssText = 'border:1px solid var(--color-border);border-radius:10px;padding:10px 12px';
      c.innerHTML = '<div style="font-size:11px;color:var(--color-text-muted)">'
        + esc(p[0]) + '</div><div style="font-family:var(--font-mono);font-size:20px;'
        + 'font-weight:600">'
        + esc(String(p[1])) + '</div>';
      g.appendChild(c);
    });
    return g;
  }

  function keyItem(color, label) {
    var s = el('span', 'sum-key-item');
    s.innerHTML = '<span class="sum-key-dot" style="background:' + color + '"></span>' + esc(label);
    return s;
  }

  /* ------------------------------------------------------------------
     Render một frame
     ------------------------------------------------------------------ */
  function render() {
    var frame = state.frames[state.index];
    var data = state.data;
    if (!frame) return;

    var scene = SCENES[frame.scene - 1];

    // đầu player
    var numEl = $('.sum-scene-num', dom.player);
    var titleEl = $('.sum-scene-title', dom.player);
    var stepEl = $('.sum-scene-step', dom.player);
    var sceneStart = indexOfScene(frame.scene);
    var sceneEnd = indexOfScene(frame.scene + 1) - 1;
    numEl.textContent = 'Cảnh ' + scene.n + ' / 11';
    titleEl.textContent = scene.title;
    var multiFrame = sceneEnd > sceneStart;
    stepEl.textContent = multiFrame
      ? 'Bước ' + (state.index - sceneStart + 1) + ' / ' + (sceneEnd - sceneStart + 1)
      : '';

    // nội dung
    var stage = $('.sum-stage', dom.player);
    stage.innerHTML = '';
    stage.appendChild(RENDER[frame.scene](data, frame));

    // phụ đề
    var sub = $('.sum-subtitle', dom.player);
    sub.innerHTML = '<strong>' + esc(scene.title) + ':</strong> ' + esc(frame.sub);

    // thanh thời gian
    var total = state.frames.length;
    var pctDone = ((state.index + 1) / total) * 100;
    $('.sum-track-fill', dom.player).style.width = pctDone + '%';
    $('.sum-track-head', dom.player).style.left = pctDone + '%';
    $('.sum-time', dom.player).textContent = (state.index + 1) + ' / ' + total;

    // nút cảnh trước/sau
    $('#sumPrevScene', dom.player).disabled = sceneStart === state.index && frame.scene === 1;
    $('#sumNextScene', dom.player).disabled = state.index === total - 1;

    // chương
    var chapters = $('.sum-chapters', dom.player).querySelectorAll('.sum-chapter');
    for (var i = 0; i < chapters.length; i++) {
      var c = chapters[i];
      var sceneIdx = parseInt(c.getAttribute('data-index'), 10);
      var isCur = state.frames[sceneIdx].scene === frame.scene;
      c.className = 'sum-chapter' + (isCur ? ' is-current' : (sceneIdx < state.index ? ' is-done' : ''));
      c.setAttribute('aria-current', isCur ? 'step' : 'false');
    }

    // trạng thái aria của timeline
    var tl = $('#sumTimeline', dom.player);
    tl.setAttribute('aria-valuemin', '0');
    tl.setAttribute('aria-valuemax', String(total - 1));
    tl.setAttribute('aria-valuenow', String(state.index));
    tl.setAttribute('aria-valuetext', 'Cảnh ' + frame.scene + ' — ' + frame.title);
  }

  function indexOfScene(sceneN) {
    for (var i = 0; i < state.frames.length; i++) {
      if (state.frames[i].scene === sceneN) return i;
    }
    return state.frames.length;
  }

  /* ------------------------------------------------------------------
     Điều khiển
     ------------------------------------------------------------------ */
  function goTo(index, keepPlaying) {
    var total = state.frames.length;
    if (!total) return;
    state.index = Math.max(0, Math.min(total - 1, index));
    render();
    if (keepPlaying) schedule();
    else pause();
  }

  function currentBeat() {
    var f = state.frames[state.index];
    return (BEAT[f ? f.beat : 'default'] || BEAT.default);
  }

  function schedule() {
    clearTimeout(state.timer);
    if (!state.playing) return;
    state.timer = setTimeout(function () {
      if (state.index >= state.frames.length - 1) {
        pause();
        return;
      }
      goTo(state.index + 1, true);
    }, currentBeat() / state.speed);
  }

  function play() {
    if (state.index >= state.frames.length - 1) state.index = 0;
    state.playing = true;
    var b = $('#sumPlay', dom.player);
    if (b) {
      b.innerHTML = ICONS.pause + ' <span>Tạm dừng</span>';
      b.classList.add('is-playing');
      b.setAttribute('aria-pressed', 'true');
    }
    render();
    schedule();
  }

  function pause() {
    state.playing = false;
    clearTimeout(state.timer);
    var b = $('#sumPlay', dom.player);
    if (!b) return;
    b.innerHTML = ICONS.play + ' <span>Phát</span>';
    b.classList.remove('is-playing');
    b.setAttribute('aria-pressed', 'false');
  }

  function toggle() { state.playing ? pause() : play(); }

  function stepScene(dir) {
    var f = state.frames[state.index];
    var target = dir > 0 ? indexOfScene(f.scene + 1) : indexOfScene(f.scene) - 1;
    if (target < 0) target = 0;
    if (target >= state.frames.length) target = state.frames.length - 1;
    goTo(target);
  }

  function bindControls() {
    $('#sumPlay', dom.player).addEventListener('click', toggle);
    $('#sumNextFrame', dom.player).addEventListener('click', function () { goTo(state.index + 1); });
    $('#sumPrevFrame', dom.player).addEventListener('click', function () { goTo(state.index - 1); });
    $('#sumNextScene', dom.player).addEventListener('click', function () { stepScene(1); });
    $('#sumPrevScene', dom.player).addEventListener('click', function () { stepScene(-1); });

    $('#sumSpeed', dom.player).addEventListener('change', function (e) {
      state.speed = parseFloat(e.target.value) || 1;
      if (state.playing) schedule();
    });

    // thanh thời gian: bấm để nhảy
    var tl = $('#sumTimeline', dom.player);
    function seekFromEvent(e) {
      var rect = tl.getBoundingClientRect();
      var x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
      var ratio = Math.max(0, Math.min(1, x / rect.width));
      goTo(Math.round(ratio * (state.frames.length - 1)));
    }
    tl.addEventListener('click', seekFromEvent);
    tl.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { goTo(state.index + 1); e.preventDefault(); }
      if (e.key === 'ArrowLeft') { goTo(state.index - 1); e.preventDefault(); }
    });

    // chương
    $('.sum-chapters', dom.player).addEventListener('click', function (e) {
      var li = e.target.closest('.sum-chapter');
      if (!li) return;
      goTo(parseInt(li.getAttribute('data-index'), 10));
    });
  }

  function buildChapters() {
    var list = $('.sum-chapters', dom.player);
    list.innerHTML = '';
    var firstOfScene = {};
    state.frames.forEach(function (f, i) {
      if (!(f.scene in firstOfScene)) firstOfScene[f.scene] = i;
    });
    Object.keys(firstOfScene).forEach(function (sceneN) {
      var s = SCENES[sceneN - 1];
      var li = document.createElement('li');
      var b = el('button', 'sum-chapter',
        '<span class="sum-chapter-num">' + s.n + '</span><span>' + esc(s.title) + '</span>');
      b.type = 'button';
      b.setAttribute('data-index', String(firstOfScene[sceneN]));
      li.appendChild(b);
      list.appendChild(li);
    });

    // vạch ranh giới cảnh trên thanh thời gian
    var timeline = $('#sumTimeline', dom.player);
    timeline.querySelectorAll('.sum-tick, .sum-tick-label').forEach(function (n) { n.remove(); });
    var total = state.frames.length;
    Object.keys(firstOfScene).forEach(function (sceneN) {
      if (sceneN === '1') return;
      var pos = (firstOfScene[sceneN] / total) * 100;
      var tick = el('div', 'sum-tick');
      tick.style.left = pos + '%';
      tick.style.height = '16px';
      tick.style.top = '8px';
      timeline.appendChild(tick);
      var lab = el('div', 'sum-tick-label', String(SCENES[sceneN - 1].n));
      lab.style.left = pos + '%';
      timeline.appendChild(lab);
    });
  }

  /* ------------------------------------------------------------------
     Phím tắt
     ------------------------------------------------------------------ */
  function bindKeys() {
    document.addEventListener('keydown', function (e) {
      if (!state.data) return;
      var tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === ' ' || e.code === 'Space') { toggle(); e.preventDefault(); }
      else if (e.key === 'ArrowRight') {
        if (e.shiftKey) stepScene(1); else goTo(state.index + 1);
        e.preventDefault();
      } else if (e.key === 'ArrowLeft') {
        if (e.shiftKey) stepScene(-1); else goTo(state.index - 1);
        e.preventDefault();
      } else if (e.key === 'Home') { goTo(0); e.preventDefault(); }
      else if (e.key === 'End') { goTo(state.frames.length - 1); e.preventDefault(); }
    });
  }

  /* ------------------------------------------------------------------
     Gọi API
     ------------------------------------------------------------------ */
  function showStatus(html, isError) {
    var box = $('#sumStatus');
    box.innerHTML = '';
    box.className = 'sum-status' + (isError ? ' sum-status--error' : '');
    if (!isError) box.appendChild(el('span', 'sum-spinner'));
    box.appendChild(el('span', null, html));
    box.hidden = false;
  }

  function runAnalysis() {
    var text = $('#sumText').value.trim();
    var body = {
      text: text,
      K: parseInt($('#sumK').value, 10),
      iterations: parseInt($('#sumIterations').value, 10),
      alpha: parseFloat($('#sumAlpha').value),
      beta: parseFloat($('#sumBeta').value),
      seed: parseInt($('#sumSeed').value, 10),
      n_sentences: parseInt($('#sumNSentences').value, 10)
    };

    showStatus('Đang tách câu, chạy ' + body.iterations + ' vòng Gibbs và chấm điểm…');
    $('#sumSubmit').disabled = true;

    fetch('/api/summarize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, data: data };
        });
      })
      .then(function (res) {
        $('#sumSubmit').disabled = false;
        if (!res.ok) {
          showStatus(res.data.error || 'Không phân tích được đoạn văn.', true);
          return;
        }
        $('#sumStatus').hidden = true;
        load(res.data);
      })
      .catch(function (err) {
        $('#sumSubmit').disabled = false;
        showStatus('Lỗi kết nối tới máy chủ: ' + err.message, true);
      });
  }

  function load(data) {
    state.data = data;
    state.index = 0;
    state.playing = false;

    buildShell();
    state.frames = buildFrames(data);
    buildChapters();
    bindControls();
    render();

    $('#sumPlayerSection').hidden = false;
    $('#sumPlayerSection').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
    $('#sumShortcutHint').hidden = false;
  }

  /* ------------------------------------------------------------------
     Khởi tạo
     ------------------------------------------------------------------ */
  function init() {
    dom.player = $('#sumPlayer');
    if (!dom.player) return;

    $('#sumForm').addEventListener('submit', function (e) {
      e.preventDefault();
      runAnalysis();
    });

    $('#sumSampleBtn').addEventListener('click', function () {
      $('#sumText').value = window.SAMPLE_TEXT_SUMMARIZE || $('#sumText').value;
      updateCounter();
    });

    var ta = $('#sumText');
    ta.addEventListener('input', updateCounter);
    updateCounter();

    bindKeys();
  }

  function updateCounter() {
    var ta = $('#sumText');
    var words = ta.value.trim() ? ta.value.trim().split(/\s+/).length : 0;
    var c = $('#sumCounter');
    c.textContent = words + ' từ' + (words > 300 ? ' — vượt giới hạn 300 từ' : '');
    c.className = 'sum-counter' + (words > 300 ? ' sum-counter--over' : '');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
