#!/usr/bin/env python3
"""숏폼 교육 PPT 빌더.

references/design-reference.md 의 디자인 토큰(바이올렛 단일 액센트, 웜그레이 캔버스,
큰 라운드 카드, 걸침 배지/이모지, 라벤더 그라데이션)을 구현한다.

사용법:
    pip install python-pptx
    python build_pptx.py deck.json out.pptx

deck.json 형식:
{
  "aspect": "9:16",                # 또는 "16:9"
  "slides": [
    {"type": "cover",   "eyebrow": "SCIENCE SHORTS", "title": "광합성,\n3분 정리", "sub": "설명", "emoji": "🌱"},
    {"type": "concept", "eyebrow": "STEP 1", "title": "제목", "lead": "리드 문장",
     "card": {"badge": "핵심", "title": "카드 제목", "body": "본문", "emoji": "☀️"}},
    {"type": "cards",   "eyebrow": "STEP 2", "title": "제목", "lead": "리드",
     "cards": [{"badge": "1", "title": "...", "body": "...", "emoji": "💧"}, ...]},
    {"type": "quiz",    "eyebrow": "CHECK", "title": "점검 질문", "question": "질문?",
     "options": ["보기1", "보기2", "보기3"], "answer": 1},
    {"type": "summary", "label": "Summary", "title": "결론 한 문장", "recall": "인출연습 문구"}
  ]
}
"""
import json
import sys
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---- 디자인 토큰 (design-reference.md §1) ----
PRIMARY = RGBColor(0x7C, 0x3A, 0xED)
PRIMARY_DEEP = RGBColor(0x5B, 0x21, 0xB6)
LAVENDER_100 = RGBColor(0xED, 0xE9, 0xFE)
LAVENDER_300 = RGBColor(0xC4, 0xB5, 0xFD)
GRAD_A = RGBColor(0xC7, 0xC2, 0xF5)
GRAD_B = RGBColor(0x9F, 0x8D, 0xF2)
BG_CANVAS = RGBColor(0xF5, 0xF4, 0xF7)
CARD_GRAY = RGBColor(0xE9, 0xE7, 0xEE)
DIVIDER = RGBColor(0xD9, 0xD6, 0xE0)
INK = RGBColor(0x1A, 0x1A, 0x1E)
INK_SUB = RGBColor(0x5C, 0x5C, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FONT = "Pretendard"  # 미설치 시 뷰어가 자동 대체 (맑은 고딕 등)


def _set_font(run, size, bold=False, color=INK, spacing=None):
    f = run.font
    f.name = FONT
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    # 한글(East Asian) 폰트도 동일하게 지정
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT)
    if spacing is not None:
        rPr.set("spc", str(spacing))  # 자간 (1/100 pt)


def _set_alpha(shape, pct):
    """solid fill 에 투명도 적용 (pct=60 이면 60% 불투명). design-reference §7 글래스 근사."""
    sPr = shape.fill._xPr.find(qn("a:solidFill"))
    clr = sPr[0]
    alpha = clr.makeelement(qn("a:alpha"), {"val": str(int(pct * 1000))})
    clr.append(alpha)


def _soft_shadow(shape):
    """부드러운 확산 그림자 (blur 30px 상당, 10% 검정)."""
    spPr = shape._element.spPr
    el = spPr.makeelement(qn("a:effectLst"), {})
    sh = spPr.makeelement(qn("a:outerShdw"), {
        "blurRad": "381000", "dist": "76200", "dir": "5400000", "rotWithShape": "0"})
    c = spPr.makeelement(qn("a:srgbClr"), {"val": "1A1A1E"})
    a = spPr.makeelement(qn("a:alpha"), {"val": "10000"})
    c.append(a)
    sh.append(c)
    el.append(sh)
    spPr.append(el)


def _rounded(slide, x, y, w, h, fill, radius=0.08, line=False):
    sp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sp.adjustments[0] = radius
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if not line:
        sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def _gradient_bg(slide, W, H):
    """라벤더 대각선 그라데이션 배경 (design-reference §5)."""
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    sp.line.fill.background()
    sp.shadow.inherit = False
    sp.fill.gradient()
    stops = sp.fill.gradient_stops
    stops[0].position = 0.0
    stops[0].color.rgb = GRAD_A
    stops[1].position = 1.0
    stops[1].color.rgb = GRAD_B
    try:
        sp.fill.gradient_angle = 45.0
    except Exception:
        pass
    return sp


def _canvas_bg(slide, W, H, color=BG_CANVAS):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    sp.fill.solid()
    sp.fill.fore_color.rgb = color
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def _text(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
          line_spacing=1.0):
    """runs: [(text, size, bold, color, spacing), ...] — 줄바꿈은 text 내 \n."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for text, size, bold, color, spacing in runs:
        for i, line in enumerate(text.split("\n")):
            if first:
                p = tf.paragraphs[0]
                first = False
            else:
                p = tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line_spacing
            r = p.add_run()
            r.text = line
            _set_font(r, size, bold, color, spacing)
    return tb


def _badge(slide, x, y, text, scale=1.0):
    """카드 상단 변에 걸치는 primary 배지 (design-reference §3-1)."""
    w = Emu(int(Emu(Pt(12).emu * len(text) * 0.9)) + Pt(28).emu)
    h = Emu(int(Pt(24).emu * scale))
    b = _rounded(slide, x, y, w, h, PRIMARY, radius=0.3)
    tf = b.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _set_font(r, 11 * scale, True, WHITE)
    return b


def _emoji(slide, x, y, ch, size=54):
    """카드 모서리에 걸치는 대형 이모지 (design-reference §4)."""
    box = Emu(int(Pt(size * 1.6).emu))
    return _text(slide, x, y, box, box, [(ch, size, False, INK, None)],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def _chip(slide, x, y, text):
    """라벤더 해시태그 칩."""
    w = Emu(Pt(11).emu * len(text) + Pt(24).emu)
    h = Emu(Pt(22).emu)
    c = _rounded(slide, x, y, w, h, LAVENDER_100, radius=0.5)
    p = c.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _set_font(r, 10, True, PRIMARY)
    return c, w


class Deck:
    def __init__(self, aspect="9:16"):
        self.prs = Presentation()
        if aspect == "9:16":
            self.prs.slide_width = Emu(6858000)    # 7.5in
            self.prs.slide_height = Emu(12192000)  # 13.33in
        else:
            self.prs.slide_width = Emu(12192000)
            self.prs.slide_height = Emu(6858000)
        self.W = self.prs.slide_width
        self.H = self.prs.slide_height
        self.vertical = aspect == "9:16"
        self.M = int(min(self.W, self.H) * 0.08)  # 바깥 마진: 짧은 변의 8%

    def _blank(self):
        return self.prs.slides.add_slide(self.prs.slide_layouts[6])

    # ---- 슬라이드 타입 ----
    def cover(self, s):
        sl = self._blank()
        _gradient_bg(sl, self.W, self.H)
        W, H, M = self.W, self.H, self.M
        cy = int(H * 0.30)
        if s.get("emoji"):
            _emoji(sl, int(W / 2 - Pt(60).emu), int(H * 0.16), s["emoji"], 72)
        _text(sl, M, cy, W - 2 * M, Pt(30).emu,
              [(s.get("eyebrow", ""), 14, True, WHITE, 800)],
              align=PP_ALIGN.CENTER)
        _text(sl, M, cy + int(H * 0.05), W - 2 * M, int(H * 0.3),
              [(s["title"], 44 if self.vertical else 40, True, WHITE, None)],
              align=PP_ALIGN.CENTER, line_spacing=1.15)
        if s.get("sub"):
            _text(sl, M, cy + int(H * 0.28), W - 2 * M, int(H * 0.12),
                  [(s["sub"], 15, False, WHITE, None)],
                  align=PP_ALIGN.CENTER, line_spacing=1.5)

    def _header(self, sl, s):
        M = self.M
        _text(sl, M, M, self.W - 2 * M, Pt(24).emu,
              [(s.get("eyebrow", ""), 13, True, PRIMARY, 800)])
        _text(sl, M, M + Pt(26).emu, self.W - 2 * M, Pt(80).emu,
              [(s["title"], 27 if self.vertical else 30, True, INK, None)],
              line_spacing=1.2)
        y = M + Pt(26).emu + Pt(44).emu * (2 if "\n" in s["title"] else 1)
        if s.get("lead"):
            _text(sl, M, y, self.W - 2 * M, Pt(60).emu,
                  [(s["lead"], 13, False, INK_SUB, None)], line_spacing=1.6)
            y += Pt(58).emu
        return y + Pt(20).emu

    def _card(self, sl, x, y, w, h, c, glass=False):
        card = _rounded(sl, x, y, w, h, WHITE if glass else CARD_GRAY, radius=0.10)
        if glass:
            _set_alpha(card, 55)
        else:
            _soft_shadow(card)
        pad = int(w * 0.10)
        if c.get("badge"):
            _badge(sl, x + pad, y - Pt(12).emu, c["badge"])
        if c.get("emoji"):
            _emoji(sl, x + w - Pt(60).emu, y - Pt(40).emu, c["emoji"], 40)
        ty = y + pad if not c.get("badge") else y + pad + Pt(6).emu
        _text(sl, x + pad, ty, w - 2 * pad, Pt(30).emu,
              [(c["title"], 17, True, PRIMARY, None)])
        ln = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, x + pad, ty + Pt(34).emu,
                                 w - 2 * pad, Pt(1).emu)
        ln.fill.solid()
        ln.fill.fore_color.rgb = DIVIDER
        ln.line.fill.background()
        ln.shadow.inherit = False
        _text(sl, x + pad, ty + Pt(46).emu, w - 2 * pad, h - (ty - y) - Pt(50).emu,
              [(c["body"], 12, False, INK_SUB, None)], line_spacing=1.55)

    def concept(self, s):
        sl = self._blank()
        _canvas_bg(sl, self.W, self.H)
        y = self._header(sl, s)
        M = self.M
        c = s["card"]
        h = int(self.H * (0.34 if self.vertical else 0.5))
        self._card(sl, M, y + Pt(30).emu, self.W - 2 * M, h, c)

    def cards(self, s):
        sl = self._blank()
        _canvas_bg(sl, self.W, self.H)
        y = self._header(sl, s) + Pt(30).emu
        M = self.M
        items = s["cards"]
        n = len(items)
        if self.vertical:
            gap = Pt(34).emu
            h = int((self.H - y - M - gap * (n - 1)) / n)
            h = min(h, int(self.H * 0.22))
            for i, c in enumerate(items):
                self._card(sl, M, y + i * (h + gap), self.W - 2 * M, h, c)
        else:
            gap = int((self.W - 2 * M) * 0.06)
            w = int((self.W - 2 * M - gap * (n - 1)) / n)
            h = int(self.H * 0.42)
            for i, c in enumerate(items):
                self._card(sl, M + i * (w + gap), y, w, h, c)

    def quiz(self, s):
        sl = self._blank()
        _gradient_bg(sl, self.W, self.H)
        M = self.M
        _text(sl, M, int(self.H * 0.10), self.W - 2 * M, Pt(24).emu,
              [(s.get("eyebrow", "CHECK"), 13, True, WHITE, 800)],
              align=PP_ALIGN.CENTER)
        _text(sl, M, int(self.H * 0.15), self.W - 2 * M, int(self.H * 0.14),
              [(s["question"], 24, True, WHITE, None)],
              align=PP_ALIGN.CENTER, line_spacing=1.3)
        y = int(self.H * 0.34)
        oh = int(Pt(52).emu)
        gap = Pt(18).emu
        labels = "ABCD"
        for i, opt in enumerate(s.get("options", [])):
            g = _rounded(sl, M, y + i * (oh + gap), self.W - 2 * M, oh, WHITE, radius=0.5)
            _set_alpha(g, 60)
            tf = g.text_frame
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = f"{labels[i]}.  {opt}"
            _set_font(r, 14, True, PRIMARY_DEEP)
        if "answer" in s and s.get("options"):
            _text(sl, M, y + len(s["options"]) * (oh + gap) + Pt(12).emu,
                  self.W - 2 * M, Pt(26).emu,
                  [("정답은 다음 슬라이드에서 👆 화면을 멈추고 먼저 골라보세요",
                    11, False, WHITE, None)], align=PP_ALIGN.CENTER)

    def summary(self, s):
        """primary 강조 밴드 결론 슬라이드 (design-reference §3-4)."""
        sl = self._blank()
        _canvas_bg(sl, self.W, self.H)
        M = self.M
        bh = int(self.H * (0.42 if self.vertical else 0.55))
        by = int(self.H * (0.30 if self.vertical else 0.22))
        band = _rounded(sl, int(M * 0.5), by, self.W - M, bh, PRIMARY, radius=0.09)
        _soft_shadow(band)
        _text(sl, M, by + int(bh * 0.16), self.W - 2 * M, Pt(24).emu,
              [(s.get("label", "Summary"), 13, True, WHITE, 600)],
              align=PP_ALIGN.CENTER)
        _text(sl, M, by + int(bh * 0.30), self.W - 2 * M, int(bh * 0.4),
              [(s["title"], 22, True, WHITE, None)],
              align=PP_ALIGN.CENTER, line_spacing=1.4)
        if s.get("recall"):
            _text(sl, M, by + bh + Pt(24).emu, self.W - 2 * M, Pt(60).emu,
                  [("🧠 " + s["recall"], 13, True, PRIMARY_DEEP, None)],
                  align=PP_ALIGN.CENTER, line_spacing=1.5)

    def build(self, slides):
        for s in slides:
            getattr(self, s["type"])(s)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    deck = Deck(spec.get("aspect", "9:16"))
    deck.build(spec["slides"])
    deck.prs.save(sys.argv[2])
    print(f"saved: {sys.argv[2]} ({len(spec['slides'])} slides, {spec.get('aspect', '9:16')})")


if __name__ == "__main__":
    main()
