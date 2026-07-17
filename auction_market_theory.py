"""
Auction Market Theory — a self-contained Manim Community explainer.

Target: Manim Community v0.20.1 (also compatible with recent 0.19.x releases)
Render preview:  manim -pql auction_market_theory.py AuctionMarketTheoryExplainer
Render 1080p:    manim -pqh auction_market_theory.py AuctionMarketTheoryExplainer
Render 4K:       manim -pqk auction_market_theory.py AuctionMarketTheoryExplainer

The video intentionally uses no external images, fonts, data, or plugins.
Every visual is generated with Manim, so the file can run in Google Colab.
The captions double as a concise voice-over script. Set SHOW_CAPTIONS=False
if you intend to record narration separately.

Educational only — not financial advice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from manim import *


# -----------------------------------------------------------------------------
# Production settings
# -----------------------------------------------------------------------------
config.background_color = "#070B14"
config.frame_width = 16
config.frame_height = 9
# Resolution and frame rate are selected by Manim's -ql/-qm/-qh/-qk flags.

SHOW_CAPTIONS = True
PACE = 1.0  # Raise to 1.2–1.4 for a slower narration-friendly cut.
# Generic Pango families are available in both Google Colab and local installs.
FONT = "Sans"
MONO = "Monospace"

BG = "#070B14"
PANEL = "#101827"
PANEL_2 = "#151F32"
GRID = "#28364D"
WHITE = "#F7FAFF"
MUTED = "#93A4BD"
CYAN = "#37D9FF"
BLUE = "#4C7DFF"
GREEN = "#3BE38F"
RED = "#FF5F6D"
ORANGE = "#FFB547"
PURPLE = "#AE7CFF"
YELLOW = "#FFE66D"


@dataclass(frozen=True)
class CandleData:
    open: float
    high: float
    low: float
    close: float
    volume: float


# Edit these lines to match your preferred delivery. They are also rendered as
# subtitles, making the output understandable even before narration is added.
NARRATION = {
    "hook_1": "Most traders watch price move. Auction Market Theory asks a deeper question: why did the market choose that price?",
    "hook_2": "Every tick is an auction — buyers bid, sellers offer, and price searches for agreement.",
    "auction_1": "When buyers and sellers agree, business gets done. Repeated trade creates acceptance.",
    "auction_2": "When one side becomes more aggressive, price must advertise higher or lower to find the next willing counterparty.",
    "profile_1": "Market Profile reorganizes time by price. Each letter marks a time period in which that price traded.",
    "profile_2": "Wide rows show acceptance. Thin tails show rejection. The shape reveals where the auction found — or failed to find — value.",
    "value_1": "The Point of Control, or POC, is the price with the most activity. It is the auction's fairest price for that session.",
    "value_2": "The Value Area contains roughly seventy percent of activity. Its upper and lower boundaries become important reference prices.",
    "balance_1": "In balance, the market rotates around fair value. Responsive buyers act low, and responsive sellers act high.",
    "balance_2": "In imbalance, value migrates. Initiative activity accepts prices outside the old range and starts a new search for value.",
    "context_1": "A move outside value is not enough. The key distinction is acceptance versus rejection.",
    "context_2": "Time and volume building outside value suggest acceptance. A fast return into value suggests a failed auction.",
    "trade_1": "A practical plan starts with context, waits for location, and requires confirmation before risking capital.",
    "trade_2": "Define invalidation first. Then size the trade so one wrong idea cannot damage the account.",
    "recap": "Auction Market Theory is not a prediction machine. It is a framework for reading value, participation, and the market's ongoing search for agreement.",
}


class AuctionMarketTheoryExplainer(MovingCameraScene):
    """A polished, chapter-based Auction Market Theory explainer."""

    def construct(self):
        self.caption_mob = None
        self.add(self.make_background())
        self.hook()
        self.auction_mechanism()
        self.market_profile()
        self.value_area()
        self.balance_and_imbalance()
        self.acceptance_and_rejection()
        self.trade_framework()
        self.recap()

    # ------------------------------------------------------------------
    #

    # Shared design helpers
    # ------------------------------------------------------------------
    def make_background(self) -> VGroup:
        base = Rectangle(width=16, height=9, stroke_width=0, fill_color=BG, fill_opacity=1)
        lines = VGroup()
        for x in np.arange(-8, 8.01, 0.8):
            lines.add(Line([x, -4.5, 0], [x, 4.5, 0], stroke_color=GRID, stroke_opacity=0.12, stroke_width=1))
        for y in np.arange(-4.5, 4.51, 0.8):
            lines.add(Line([-8, y, 0], [8, y, 0], stroke_color=GRID, stroke_opacity=0.12, stroke_width=1))
        vignette = Rectangle(width=15.6, height=8.6, stroke_color=BLUE, stroke_opacity=0.12, stroke_width=2)
        return VGroup(base, lines, vignette)

    def txt(self, value: str, size: float = 36, color=WHITE, weight=NORMAL, font=FONT) -> Text:
        return Text(value, font=font, font_size=size, color=color, weight=weight)

    def fit(self, mob: Mobject, width: float) -> Mobject:
        if mob.width > width:
            mob.scale_to_fit_width(width)
        return mob

    def label_chip(self, value: str, color=CYAN) -> VGroup:
        label = self.txt(value.upper(), 20, color, BOLD).set_z_index(3)
        box = RoundedRectangle(corner_radius=0.12, width=label.width + 0.42, height=0.48,
                               stroke_color=color, stroke_width=1.4, fill_color=color, fill_opacity=0.10)
        return VGroup(box, label)

    def chapter_title(self, number: str, title: str, kicker: str) -> VGroup:
        index = self.txt(number, 20, CYAN, BOLD)
        index_box = RoundedRectangle(corner_radius=0.12, width=0.58, height=0.48,
                                     stroke_width=0, fill_color=CYAN, fill_opacity=0.16)
        index.move_to(index_box)
        heading = self.txt(title, 38, WHITE, BOLD)
        top = VGroup(VGroup(index_box, index), heading).arrange(RIGHT, buff=0.25)
        sub = self.txt(kicker, 20, MUTED)
        group = VGroup(top, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.12).to_edge(UP, buff=0.38).to_edge(LEFT, buff=0.62)
        return group

    def panel(self, width: float, height: float, color=PANEL) -> RoundedRectangle:
        return RoundedRectangle(corner_radius=0.22, width=width, height=height,
                                stroke_color=GRID, stroke_width=1.2,
                                fill_color=color, fill_opacity=0.96)

    def show_caption(self, words: str, hold: float = 2.1) -> None:
        if not SHOW_CAPTIONS:
            self.wait(hold * PACE)
            return
        line = self.fit(self.txt(words, 22, WHITE), 13.6)
        box = RoundedRectangle(corner_radius=0.14, width=max(line.width + 0.65, 7.0), height=0.64,
                               stroke_width=0, fill_color="#03060C", fill_opacity=0.88)
        group = VGroup(box, line).move_to(DOWN * 4.03).set_z_index(50)
        if self.caption_mob is None:
            self.caption_mob = group
            self.play(FadeIn(group, shift=UP * 0.08), run_time=0.32)
        else:
            old = self.caption_mob
            self.caption_mob = group
            self.play(FadeOut(old, shift=UP * 0.05), FadeIn(group, shift=UP * 0.05), run_time=0.25)
        self.wait(hold * PACE)

    def hide_caption(self) -> None:
        if self.caption_mob is not None:
            self.play(FadeOut(self.caption_mob), run_time=0.2)
            self.caption_mob = None

    def wipe(self, *mobjects: Mobject) -> None:
        self.hide_caption()
        if mobjects:
            self.play(LaggedStart(*[FadeOut(m, shift=LEFT * 0.15) for m in mobjects], lag_ratio=0.03), run_time=0.6)
        sweep = Rectangle(width=18, height=0.05, fill_color=CYAN, fill_opacity=0.8, stroke_width=0)
        sweep.move_to(UP * 4.48)
        self.play(sweep.animate.shift(DOWN * 8.96), run_time=0.35, rate_func=linear)
        self.remove(sweep)

    def axis_labels(self, low: int, high: int, x: float, y0: float, step: float) -> VGroup:
        labels = VGroup()
        for price in range(low, high + 1):
            label = self.txt(str(price), 15, MUTED, font=MONO).move_to([x, y0 + (price - low) * step, 0])
            labels.add(label)
        return labels

    def candle(self, x: float, data: CandleData, y_map, width=0.22) -> VGroup:
        up = data.close >= data.open
        color = GREEN if up else RED
        wick = Line([x, y_map(data.low), 0], [x, y_map(data.high), 0], stroke_color=color, stroke_width=2)
        body_height = max(abs(y_map(data.close) - y_map(data.open)), 0.05)
        body = Rectangle(width=width, height=body_height, stroke_color=color, stroke_width=1.3,
                         fill_color=color, fill_opacity=0.82)
        body.move_to([x, (y_map(data.open) + y_map(data.close)) / 2, 0])
        return VGroup(wick, body)

    # ------------------------------------------------------------------
    # 00 — Cold open
    # ------------------------------------------------------------------
    def hook(self) -> None:
        eyebrow = self.label_chip("Market structure, visualized", CYAN).move_to(UP * 2.75)
        title_a = self.txt("AUCTION", 82, WHITE, BOLD)
        title_b = self.txt("MARKET THEORY", 82, CYAN, BOLD)
        title = VGroup(title_a, title_b).arrange(DOWN, buff=0.02).move_to(UP * 1.25)
        underline = Line(LEFT * 3.6, RIGHT * 3.6, color=BLUE, stroke_width=3).next_to(title, DOWN, buff=0.25)
        underline_glow = underline.copy().set_stroke(BLUE, width=14, opacity=0.16)

        prices = [0.0, 0.25, 0.05, 0.48, 0.32, 0.85, 0.62, 1.1, 0.96, 1.35, 1.15, 1.52]
        points = [[-5.7 + i * 1.04, -2.35 + p * 0.65, 0] for i, p in enumerate(prices)]
        graph = VMobject(stroke_color=CYAN, stroke_width=3).set_points_as_corners(points)
        glow = graph.copy().set_stroke(CYAN, width=14, opacity=0.12)
        dots = VGroup(*[Dot(p, radius=0.045, color=WHITE) for p in points])
        bid = self.txt("BID", 16, GREEN, BOLD).next_to(points[2], DOWN, buff=0.18)
        offer = self.txt("OFFER", 16, RED, BOLD).next_to(points[7], UP, buff=0.18)

        self.play(FadeIn(eyebrow, shift=DOWN * 0.15), run_time=0.5)
        self.play(LaggedStart(FadeIn(title_a, shift=UP * 0.25), FadeIn(title_b, shift=UP * 0.25), lag_ratio=0.18), run_time=1.0)
        self.play(Create(underline_glow), Create(underline), run_time=0.5)
        self.show_caption(NARRATION["hook_1"], 2.2)
        self.play(Create(glow), Create(graph), LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.04), run_time=1.5)
        self.play(FadeIn(bid), FadeIn(offer), run_time=0.4)
        self.show_caption(NARRATION["hook_2"], 2.2)

        tag = self.txt("VALUE  •  ACCEPTANCE  •  IMBALANCE", 20, MUTED, BOLD).move_to(DOWN * 3.23)
        self.play(FadeIn(tag, shift=UP * 0.12), run_time=0.5)
        self.wait(0.7 * PACE)
        self.wipe(eyebrow, title, underline, underline_glow, graph, glow, dots, bid, offer, tag)

    # ------------------------------------------------------------------
    # 01 — How the auction works
    # ------------------------------------------------------------------
    def auction_mechanism(self) -> None:
        header = self.chapter_title("01", "THE CONTINUOUS AUCTION", "Price is a discovery mechanism — not just a number")
        self.play(FadeIn(header, shift=DOWN * 0.15))

        left_panel = self.panel(3.55, 4.9).move_to(LEFT * 5.15 + DOWN * 0.25)
        right_panel = self.panel(3.55, 4.9).move_to(RIGHT * 5.15 + DOWN * 0.25)
        center_panel = self.panel(5.9, 4.9, PANEL_2).move_to(DOWN * 0.25)
        panels = VGroup(left_panel, right_panel, center_panel)
        self.play(LaggedStart(*[FadeIn(p, scale=0.96) for p in panels], lag_ratio=0.08), run_time=0.8)

        buyer_icon = Circle(radius=0.42, color=GREEN, fill_color=GREEN, fill_opacity=0.12)
        buyer_icon.add(self.txt("B", 27, GREEN, BOLD).move_to(buyer_icon))
        buyer_title = self.txt("BUYERS", 28, GREEN, BOLD)
        buyer_sub = self.txt("bid for inventory", 18, MUTED)
        buyers = VGroup(buyer_icon, buyer_title, buyer_sub).arrange(DOWN, buff=0.16).move_to(left_panel.get_top() + DOWN * 1.0)
        seller_icon = Circle(radius=0.42, color=RED, fill_color=RED, fill_opacity=0.12)
        seller_icon.add(self.txt("S", 27, RED, BOLD).move_to(seller_icon))
        seller_title = self.txt("SELLERS", 28, RED, BOLD)
        seller_sub = self.txt("offer inventory", 18, MUTED)
        sellers = VGroup(seller_icon, seller_title, seller_sub).arrange(DOWN, buff=0.16).move_to(right_panel.get_top() + DOWN * 1.0)

        ladder_title = self.txt("ORDER BOOK", 19, WHITE, BOLD).move_to(center_panel.get_top() + DOWN * 0.42)
        spread = self.label_chip("spread", ORANGE).scale(0.78).move_to([0, -0.1, 0])
        rows = VGroup()
        prices = [103, 102, 101, 100, 99, 98, 97]
        for i, price in enumerate(prices):
            y = 1.2 - i * 0.48
            line = Line([-2.35, y, 0], [2.35, y, 0], color=GRID, stroke_width=1)
            price_t = self.txt(str(price), 18, WHITE if price == 100 else MUTED, BOLD if price == 100 else NORMAL, MONO).move_to([0, y, 0])
            if price > 100:
                depth = Rectangle(width=(price - 99) * 0.42, height=0.22, fill_color=RED, fill_opacity=0.38, stroke_width=0).next_to(price_t, RIGHT, buff=0.28)
            elif price < 100:
                depth = Rectangle(width=(101 - price) * 0.42, height=0.22, fill_color=GREEN, fill_opacity=0.38, stroke_width=0).next_to(price_t, LEFT, buff=0.28)
            else:
                depth = Dot([0, y, 0], radius=0.08, color=ORANGE)
            rows.add(VGroup(line, price_t, depth))

        self.play(FadeIn(buyers), FadeIn(sellers), Write(ladder_title), LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.06), run_time=1.2)
        self.play(FadeIn(spread, scale=0.8))
        self.show_caption(NARRATION["auction_1"], 2.0)

        buy_orders = VGroup(*[Dot(left_panel.get_center() + RIGHT * 0.6 + DOWN * (i - 2) * 0.37, radius=0.07, color=GREEN) for i in range(5)])
        sell_orders = VGroup(*[Dot(right_panel.get_center() + LEFT * 0.6 + DOWN * (i - 2) * 0.37, radius=0.07, color=RED) for i in range(5)])
        self.play(LaggedStart(*[FadeIn(d) for d in buy_orders], lag_ratio=0.05), LaggedStart(*[FadeIn(d) for d in sell_orders], lag_ratio=0.05))
        trades = VGroup(*[Dot([0, 1.2 - i * 0.48, 0], radius=0.075, color=YELLOW) for i in [2, 3, 4]])
        self.play(
            LaggedStart(*[d.animate.move_to([-0.12, 1.2 - (3 + i % 2) * 0.48, 0]) for i, d in enumerate(buy_orders)], lag_ratio=0.08),
            LaggedStart(*[d.animate.move_to([0.12, 1.2 - (2 + i % 2) * 0.48, 0]) for i, d in enumerate(sell_orders)], lag_ratio=0.08),
            run_time=1.25,
        )
        self.play(LaggedStart(*[Flash(t.get_center(), color=YELLOW, flash_radius=0.22) for t in trades], lag_ratio=0.18), run_time=0.9)

        arrow_up = Arrow([1.8, -1.75, 0], [1.8, 1.1, 0], color=GREEN, stroke_width=5)
        aggressive = self.txt("AGGRESSIVE BUYING", 18, GREEN, BOLD).rotate(PI / 2).next_to(arrow_up, RIGHT, buff=0.18)
        self.play(GrowArrow(arrow_up), FadeIn(aggressive), run_time=0.8)
        self.show_caption(NARRATION["auction_2"], 2.2)

        equation = VGroup(
            self.label_chip("agreement", CYAN),
            self.txt("→", 25, MUTED),
            self.label_chip("trade", YELLOW),
            self.txt("→", 25, MUTED),
            self.label_chip("value", PURPLE),
        ).arrange(RIGHT, buff=0.2).move_to(DOWN * 3.25)
        self.play(FadeIn(equation, shift=UP * 0.12))
        self.wait(0.8 * PACE)
        self.wipe(header, panels, buyers, sellers, ladder_title, rows, spread, buy_orders, sell_orders, arrow_up, aggressive, equation)

    # ------------------------------------------------------------------
    # 02 — Market Profile / TPO construction
    # ------------------------------------------------------------------
    def market_profile(self) -> None:
        header = self.chapter_title("02", "MARKET PROFILE", "Turn the trading session sideways to expose value")
        self.play(FadeIn(header, shift=DOWN * 0.15))

        timeline_panel = self.panel(7.0, 5.55).move_to(LEFT * 4.15 + DOWN * 0.25)
        profile_panel = self.panel(7.0, 5.55).move_to(RIGHT * 4.15 + DOWN * 0.25)
        self.play(FadeIn(timeline_panel), FadeIn(profile_panel))
        left_title = self.txt("TIME-ORDERED PRICE", 18, MUTED, BOLD).move_to(timeline_panel.get_top() + DOWN * 0.38)
        right_title = self.txt("TIME AT PRICE (TPO)", 18, CYAN, BOLD).move_to(profile_panel.get_top() + DOWN * 0.38)
        self.play(Write(left_title), Write(right_title))

        low, high, step = 96, 106, 0.38
        y0 = -2.05
        labels_l = self.axis_labels(low, high, -6.65, y0, step)
        labels_r = self.axis_labels(low, high, 0.85, y0, step)
        guides = VGroup()
        for price in range(low, high + 1):
            y = y0 + (price - low) * step
            guides.add(Line([-6.25, y, 0], [-0.75, y, 0], color=GRID, stroke_width=1, stroke_opacity=0.45))
            guides.add(Line([1.25, y, 0], [7.15, y, 0], color=GRID, stroke_width=1, stroke_opacity=0.45))
        self.play(FadeIn(labels_l), FadeIn(labels_r), FadeIn(guides), run_time=0.7)

        periods = {
            "A": (99, 103), "B": (98, 104), "C": (99, 105), "D": (100, 106),
            "E": (99, 104), "F": (98, 102), "G": (97, 101), "H": (96, 100),
        }
        period_colors = [CYAN, BLUE, PURPLE, ORANGE, YELLOW, GREEN, CYAN, BLUE]
        columns = VGroup()
        tpo_targets: list[tuple[Text, np.ndarray]] = []
        row_counts = {p: 0 for p in range(low, high + 1)}
        for i, (letter, (p_low, p_high)) in enumerate(periods.items()):
            x = -5.78 + i * 0.66
            period_group = VGroup()
            for price in range(p_low, p_high + 1):
                glyph = self.txt(letter, 18, period_colors[i], BOLD, MONO).move_to([x, y0 + (price - low) * step, 0])
                period_group.add(glyph)
                target = np.array([1.55 + row_counts[price] * 0.31, y0 + (price - low) * step, 0])
                tpo_targets.append((glyph, target))
                row_counts[price] += 1
            time_label = self.txt(letter, 15, period_colors[i], BOLD, MONO).move_to([x, -2.52, 0])
            period_group.add(time_label)
            columns.add(period_group)

        self.play(LaggedStart(*[FadeIn(col, shift=UP * 0.1) for col in columns], lag_ratio=0.1), run_time=1.5)
        self.show_caption(NARRATION["profile_1"], 2.0)

        profile_letters = VGroup()
        animations = []
        for source, target in tpo_targets:
            clone = source.copy()
            profile_letters.add(clone)
            self.add(clone)
            animations.append(clone.animate.move_to(target))
        self.play(LaggedStart(*animations, lag_ratio=0.015), run_time=2.0, rate_func=smooth)

        widest_price = max(row_counts, key=row_counts.get)
        widest_y = y0 + (widest_price - low) * step
        highlight = RoundedRectangle(corner_radius=0.08, width=row_counts[widest_price] * 0.31 + 0.3, height=0.32,
                                     stroke_color=YELLOW, stroke_width=1.5, fill_color=YELLOW, fill_opacity=0.08)
        highlight.move_to([1.42 + row_counts[widest_price] * 0.155, widest_y, 0])
        acceptance = self.label_chip("acceptance", YELLOW).scale(0.8).next_to(highlight, RIGHT, buff=0.25)
        tail = self.label_chip("rejection tail", RED).scale(0.8).move_to([5.7, y0, 0])
        tail_arrow = Arrow(tail.get_left(), [1.58, y0, 0], color=RED, stroke_width=2.5, buff=0.08, max_tip_length_to_length_ratio=0.15)
        self.play(Create(highlight), FadeIn(acceptance), GrowArrow(tail_arrow), FadeIn(tail), run_time=0.9)
        self.show_caption(NARRATION["profile_2"], 2.3)

        footer = VGroup(
            self.txt("WIDTH", 17, CYAN, BOLD), self.txt("=", 17, MUTED), self.txt("TIME + PARTICIPATION", 17, WHITE, BOLD)
        ).arrange(RIGHT, buff=0.15).move_to(DOWN * 3.35)
        self.play(FadeIn(footer, shift=UP * 0.1))
        self.wait(0.8 * PACE)
        self.wipe(header, timeline_panel, profile_panel, left_title, right_title, labels_l, labels_r, guides, columns,
                  profile_letters, highlight, acceptance, tail, tail_arrow, footer)

    # ------------------------------------------------------------------
    # 03 — POC and value area
    # ------------------------------------------------------------------
    def value_area(self) -> None:
        header = self.chapter_title("03", "THE MAP OF VALUE", "POC, Value Area High, and Value Area Low")
        self.play(FadeIn(header, shift=DOWN * 0.15))

        profile_box = self.panel(8.4, 5.6, PANEL_2).move_to(LEFT * 2.65 + DOWN * 0.2)
        metrics_box = self.panel(4.8, 5.6).move_to(RIGHT * 5.35 + DOWN * 0.2)
        self.play(FadeIn(profile_box), FadeIn(metrics_box))

        counts = [1, 2, 3, 5, 7, 9, 11, 10, 8, 6, 4, 2, 1]
        prices = list(range(94, 107))
        y0, step = -2.22, 0.36
        bars = VGroup()
        price_labels = VGroup()
        total = sum(counts)
        poc_i = int(np.argmax(counts))
        # A compact approximation of the standard 70% value-area expansion.
        included = {poc_i}
        running = counts[poc_i]
        lo_i = hi_i = poc_i
        while running / total < 0.70:
            up = counts[hi_i + 1] if hi_i + 1 < len(counts) else -1
            down = counts[lo_i - 1] if lo_i - 1 >= 0 else -1
            if up >= down:
                hi_i += 1
                running += counts[hi_i]
                included.add(hi_i)
            else:
                lo_i -= 1
                running += counts[lo_i]
                included.add(lo_i)

        for i, (price, count) in enumerate(zip(prices, counts)):
            y = y0 + i * step
            in_value = i in included
            color = PURPLE if in_value else GRID
            opacity = 0.72 if in_value else 0.35
            bar = RoundedRectangle(corner_radius=0.05, width=count * 0.38, height=0.25,
                                   stroke_width=0, fill_color=color, fill_opacity=opacity)
            bar.align_to([-0.2, y, 0], LEFT).move_to([-0.2 + bar.width / 2, y, 0])
            bars.add(bar)
            price_labels.add(self.txt(str(price), 15, WHITE if i == poc_i else MUTED, BOLD if i == poc_i else NORMAL, MONO).move_to([-1.05, y, 0]))

        self.play(FadeIn(price_labels), LaggedStart(*[GrowFromEdge(bar, LEFT) for bar in bars], lag_ratio=0.06), run_time=1.4)
        poc_y = y0 + poc_i * step
        val_y = y0 + lo_i * step
        vah_y = y0 + hi_i * step
        poc_line = Line([-1.35, poc_y, 0], [4.0, poc_y, 0], color=YELLOW, stroke_width=3)
        vah_line = DashedLine([-1.35, vah_y + 0.18, 0], [4.0, vah_y + 0.18, 0], color=CYAN, stroke_width=2, dash_length=0.12)
        val_line = DashedLine([-1.35, val_y - 0.18, 0], [4.0, val_y - 0.18, 0], color=CYAN, stroke_width=2, dash_length=0.12)
        poc_tag = self.label_chip("POC", YELLOW).scale(0.78).next_to(poc_line, RIGHT, buff=0.12)
        vah_tag = self.label_chip("VAH", CYAN).scale(0.78).next_to(vah_line, RIGHT, buff=0.12)
        val_tag = self.label_chip("VAL", CYAN).scale(0.78).next_to(val_line, RIGHT, buff=0.12)
        value_fill = Rectangle(width=5.3, height=(hi_i - lo_i + 1) * step,
                               fill_color=PURPLE, fill_opacity=0.06, stroke_width=0).move_to([1.32, (vah_y + val_y) / 2, 0])
        self.play(FadeIn(value_fill), Create(poc_line), FadeIn(poc_tag))
        self.show_caption(NARRATION["value_1"], 2.1)
        self.play(Create(vah_line), Create(val_line), FadeIn(vah_tag), FadeIn(val_tag))

        metric_title = self.txt("SESSION REFERENCES", 18, MUTED, BOLD).move_to(metrics_box.get_top() + DOWN * 0.42)
        metrics = VGroup()
        metric_data = [
            ("POC", str(prices[poc_i]), "most activity", YELLOW),
            ("VAH", str(prices[hi_i]), "upper value edge", CYAN),
            ("VAL", str(prices[lo_i]), "lower value edge", CYAN),
            ("VALUE", f"{running / total:.0%}", "of all TPOs", PURPLE),
        ]
        for key, value, meaning, color in metric_data:
            key_t = self.txt(key, 17, color, BOLD)
            value_t = self.txt(value, 29, WHITE, BOLD, MONO)
            meaning_t = self.txt(meaning, 15, MUTED)
            row = VGroup(key_t, value_t, meaning_t).arrange(RIGHT, buff=0.25)
            row_bg = RoundedRectangle(corner_radius=0.12, width=4.2, height=0.75, stroke_color=GRID, stroke_width=1,
                                      fill_color=PANEL_2, fill_opacity=0.9)
            row.move_to(row_bg)
            metrics.add(VGroup(row_bg, row))
        metrics.arrange(DOWN, buff=0.22).move_to(metrics_box.get_center() + DOWN * 0.15)
        self.play(Write(metric_title), LaggedStart(*[FadeIn(m, shift=LEFT * 0.12) for m in metrics], lag_ratio=0.12), run_time=1.2)
        self.show_caption(NARRATION["value_2"], 2.3)
        self.wait(0.6 * PACE)
        self.wipe(header, profile_box, metrics_box, price_labels, bars, value_fill, poc_line, vah_line, val_line,
                  poc_tag, vah_tag, val_tag, metric_title, metrics)

    # ------------------------------------------------------------------
    # 04 — Balance versus imbalance
    # ------------------------------------------------------------------
    def balance_and_imbalance(self) -> None:
        header = self.chapter_title("04", "MARKET CONDITION", "First classify the auction: balanced or imbalanced?")
        self.play(FadeIn(header, shift=DOWN * 0.15))

        left = self.panel(7.25, 5.65).move_to(LEFT * 3.85 + DOWN * 0.18)
        right = self.panel(7.25, 5.65).move_to(RIGHT * 3.85 + DOWN * 0.18)
        divider = Line([0, -3.0, 0], [0, 2.4, 0], color=GRID, stroke_width=1.2)
        self.play(FadeIn(left), FadeIn(right), Create(divider))
        bal_title = VGroup(self.txt("BALANCE", 28, PURPLE, BOLD), self.label_chip("rotation", PURPLE).scale(0.75)).arrange(RIGHT, buff=0.25).move_to(left.get_top() + DOWN * 0.52)
        imb_title = VGroup(self.txt("IMBALANCE", 28, GREEN, BOLD), self.label_chip("discovery", GREEN).scale(0.75)).arrange(RIGHT, buff=0.25).move_to(right.get_top() + DOWN * 0.52)
        self.play(FadeIn(bal_title), FadeIn(imb_title))

        # Balanced rotation around a fixed POC.
        bal_center = np.array([-3.85, -0.25, 0])
        value_band = Rectangle(width=5.8, height=2.4, fill_color=PURPLE, fill_opacity=0.08,
                               stroke_color=PURPLE, stroke_opacity=0.35).move_to(bal_center)
        poc = DashedLine([-6.75, -0.25, 0], [-0.95, -0.25, 0], color=YELLOW, stroke_width=2)
        bal_points = []
        for i in range(70):
            x = -6.55 + i * 0.078
            y = -0.25 + math.sin(i * 0.37) * (0.82 + 0.12 * math.sin(i * 0.11))
            bal_points.append([x, y, 0])
        bal_path = VMobject(color=PURPLE, stroke_width=3).set_points_smoothly(bal_points)
        bal_dot = Dot(bal_points[0], color=WHITE, radius=0.06)
        self.play(FadeIn(value_band), Create(poc), Create(bal_path), MoveAlongPath(bal_dot, bal_path), run_time=1.6)
        bal_notes = VGroup(self.txt("responsive buying at VAL", 16, GREEN), self.txt("responsive selling at VAH", 16, RED)).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([-3.85, -2.25, 0])
        self.play(FadeIn(bal_notes))
        self.show_caption(NARRATION["balance_1"], 2.0)

        # Imbalance: rising value zones and directional candles.
        zones = VGroup()
        for i, y in enumerate([-1.65, -0.55, 0.7]):
            zone = RoundedRectangle(corner_radius=0.08, width=2.0 + i * 0.3, height=0.62,
                                    stroke_color=GREEN, stroke_opacity=0.35, fill_color=GREEN, fill_opacity=0.08)
            zone.move_to([2.3 + i * 1.28, y, 0])
            zones.add(zone)
        migration = Arrow([1.45, -2.05, 0], [6.55, 1.8, 0], color=GREEN, stroke_width=4, max_tip_length_to_length_ratio=0.08)
        samples = [
            CandleData(98, 100, 97.5, 99.5, 1), CandleData(99.4, 101.2, 99.0, 100.8, 1),
            CandleData(100.7, 102.0, 100.1, 101.7, 1), CandleData(101.6, 103.0, 101.2, 102.5, 1),
            CandleData(102.4, 104.0, 102.0, 103.7, 1), CandleData(103.6, 104.8, 103.0, 104.3, 1),
        ]
        y_map = lambda p: -1.65 + (p - 98) * 0.6
        candles = VGroup(*[self.candle(1.65 + i * 0.83, d, y_map, 0.3) for i, d in enumerate(samples)])
        self.play(LaggedStart(*[FadeIn(z, scale=0.9) for z in zones], lag_ratio=0.16), GrowArrow(migration),
                  LaggedStart(*[Create(c) for c in candles], lag_ratio=0.12), run_time=1.6)
        migration_note = self.txt("VALUE MIGRATES HIGHER", 17, GREEN, BOLD).move_to([4.1, -2.28, 0])
        self.play(FadeIn(migration_note))
        self.show_caption(NARRATION["balance_2"], 2.2)

        question = VGroup(self.txt("Ask first:", 18, MUTED), self.txt("ROTATION OR DISCOVERY?", 20, WHITE, BOLD)).arrange(RIGHT, buff=0.16).move_to(DOWN * 3.35)
        self.play(FadeIn(question, shift=UP * 0.1))
        self.wait(0.7 * PACE)
        self.wipe(header, left, right, divider, bal_title, imb_title, value_band, poc, bal_path, bal_dot, bal_notes,
                  zones, migration, candles, migration_note, question)

    # ------------------------------------------------------------------
    # 05 — Acceptance and rejection
    # ------------------------------------------------------------------
    def acceptance_and_rejection(self) -> None:
        header = self.chapter_title("05", "BREAKOUT OR FAILED AUCTION?", "Location matters. The response to location matters more.")
        self.play(FadeIn(header, shift=DOWN * 0.15))

        chart = self.panel(10.0, 5.55, PANEL_2).move_to(LEFT * 2.5 + DOWN * 0.2)
        checklist = self.panel(4.25, 5.55).move_to(RIGHT * 5.55 + DOWN * 0.2)
        self.play(FadeIn(chart), FadeIn(checklist))
        value_zone = Rectangle(width=8.8, height=2.15, fill_color=PURPLE, fill_opacity=0.09,
                               stroke_color=PURPLE, stroke_opacity=0.35).move_to([-2.5, -0.7, 0])
        vah = DashedLine([-6.9, 0.38, 0], [1.9, 0.38, 0], color=CYAN, stroke_width=2)
        val = DashedLine([-6.9, -1.78, 0], [1.9, -1.78, 0], color=CYAN, stroke_width=2)
        vah_label = self.label_chip("VAH", CYAN).scale(0.7).next_to(vah, LEFT, buff=0.08)
        val_label = self.label_chip("VAL", CYAN).scale(0.7).next_to(val, LEFT, buff=0.08)
        self.play(FadeIn(value_zone), Create(vah), Create(val), FadeIn(vah_label), FadeIn(val_label))

        path_points = [(-6.3, -0.8), (-5.5, -0.2), (-4.8, -1.1), (-4.0, -0.25), (-3.3, 0.2),
                       (-2.7, 0.85), (-2.0, 1.35), (-1.3, 1.1), (-0.6, 1.55), (0.2, 1.25), (1.2, 1.72)]
        accept_path = VMobject(color=GREEN, stroke_width=3).set_points_smoothly([[x, y, 0] for x, y in path_points])
        build_area = RoundedRectangle(corner_radius=0.1, width=3.5, height=1.45, stroke_color=GREEN,
                                      stroke_width=1.5, fill_color=GREEN, fill_opacity=0.08).move_to([-0.25, 1.3, 0])
        self.play(Create(accept_path), run_time=1.4)
        self.play(FadeIn(build_area), run_time=0.5)
        accept_tag = self.label_chip("ACCEPTANCE", GREEN).move_to([-2.2, 2.15, 0])
        self.play(FadeIn(accept_tag, scale=0.85))
        self.show_caption(NARRATION["context_1"], 2.0)

        list_title = self.txt("LOOK FOR", 18, MUTED, BOLD).move_to(checklist.get_top() + DOWN * 0.45)
        accepts = VGroup()
        for label in ["time outside value", "volume expands", "pullback holds", "POC migrates"]:
            icon = Circle(radius=0.12, fill_color=GREEN, fill_opacity=0.18, stroke_color=GREEN, stroke_width=1.2)
            tick = self.txt("✓", 13, GREEN, BOLD).move_to(icon)
            text = self.txt(label, 17, WHITE)
            accepts.add(VGroup(VGroup(icon, tick), text).arrange(RIGHT, buff=0.18))
        accepts.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(checklist.get_center() + UP * 0.35)
        self.play(Write(list_title), LaggedStart(*[FadeIn(a, shift=LEFT * 0.12) for a in accepts], lag_ratio=0.13), run_time=1.1)
        accept_result = self.label_chip("continuation favored", GREEN).scale(0.85).move_to(checklist.get_bottom() + UP * 0.5)
        self.play(FadeIn(accept_result))
        self.show_caption(NARRATION["context_2"], 2.1)

        # Morph into rejection / failed auction.
        reject_points = [(-6.3, -0.8), (-5.4, -0.2), (-4.5, -0.9), (-3.7, -0.1), (-2.9, 0.25),
                         (-2.1, 1.45), (-1.5, 1.8), (-0.9, 0.55), (-0.2, 0.05), (0.6, -0.55), (1.3, -0.95)]
        reject_path = VMobject(color=RED, stroke_width=3).set_points_smoothly([[x, y, 0] for x, y in reject_points])
        reject_tag = self.label_chip("REJECTION", RED).move_to([-2.2, 2.15, 0])
        reject_items = VGroup()
        for label in ["brief excursion", "low participation", "fast return", "trapped traders"]:
            icon = Circle(radius=0.12, fill_color=RED, fill_opacity=0.18, stroke_color=RED, stroke_width=1.2)
            cross = self.txt("×", 14, RED, BOLD).move_to(icon)
            text = self.txt(label, 17, WHITE)
            reject_items.add(VGroup(VGroup(icon, cross), text).arrange(RIGHT, buff=0.18))
        reject_items.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(accepts)
        reject_result = self.label_chip("rotation favored", RED).scale(0.85).move_to(accept_result)
        self.play(Transform(accept_path, reject_path), FadeOut(build_area), Transform(accept_tag, reject_tag),
                  Transform(accepts, reject_items), Transform(accept_result, reject_result), run_time=1.25)
        failure_arrow = Arrow([-1.4, 1.72, 0], [-0.15, 0.1, 0], color=RED, stroke_width=4)
        self.play(GrowArrow(failure_arrow), Flash([-1.4, 1.72, 0], color=RED, flash_radius=0.35))
        distinction = self.txt("OUTSIDE VALUE  ≠  ACCEPTED OUTSIDE VALUE", 19, ORANGE, BOLD).move_to(DOWN * 3.35)
        self.play(FadeIn(distinction, shift=UP * 0.1))
        self.wait(1.2 * PACE)
        self.wipe(header, chart, checklist, value_zone, vah, val, vah_label, val_label, accept_path, accept_tag,
                  list_title, accepts, accept_result, failure_arrow, distinction)

    # ------------------------------------------------------------------
    # 06 — A practical decision process and risk
    # ------------------------------------------------------------------
    def trade_framework(self) -> None:
        header = self.chapter_title("06", "FROM THEORY TO A PLAN", "Context → Location → Confirmation → Risk")
        self.play(FadeIn(header, shift=DOWN * 0.15))

        steps = VGroup()
        step_data = [
            ("01", "CONTEXT", "Balance or imbalance?", PURPLE),
            ("02", "LOCATION", "POC, VAH, VAL, excess", CYAN),
            ("03", "CONFIRM", "Acceptance or rejection?", GREEN),
            ("04", "RISK", "Where is the idea wrong?", ORANGE),
        ]
        for number, title, body, color in step_data:
            bg = self.panel(3.55, 1.55, PANEL_2)
            num = self.txt(number, 18, color, BOLD, MONO).move_to(bg.get_left() + RIGHT * 0.43 + UP * 0.42)
            title_t = self.txt(title, 21, WHITE, BOLD).next_to(num, RIGHT, buff=0.22)
            body_t = self.fit(self.txt(body, 15, MUTED), 2.9).move_to(bg.get_center() + DOWN * 0.34)
            accent = Line(bg.get_corner(DL) + RIGHT * 0.15, bg.get_corner(DR) + LEFT * 0.15, color=color, stroke_width=3)
            steps.add(VGroup(bg, num, title_t, body_t, accent))
        steps.arrange(RIGHT, buff=0.25).move_to(UP * 1.55)
        arrows = VGroup(*[
            Arrow(steps[i].get_right() + RIGHT * 0.02, steps[i + 1].get_left() + LEFT * 0.02,
                  color=MUTED, stroke_width=2, buff=0.06, max_tip_length_to_length_ratio=0.35)
            for i in range(3)
        ])
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.15) for s in steps], lag_ratio=0.12),
                  LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.15), run_time=1.4)
        self.show_caption(NARRATION["trade_1"], 2.1)

        chart_panel = self.panel(9.4, 3.5).move_to(LEFT * 2.65 + DOWN * 1.25)
        risk_panel = self.panel(4.6, 3.5).move_to(RIGHT * 5.45 + DOWN * 1.25)
        self.play(FadeIn(chart_panel), FadeIn(risk_panel))
        entry_y, stop_y, target_y = -1.05, -2.15, 0.35
        entry = DashedLine([-6.85, entry_y, 0], [1.65, entry_y, 0], color=CYAN, stroke_width=2)
        stop = DashedLine([-6.85, stop_y, 0], [1.65, stop_y, 0], color=RED, stroke_width=2)
        target = DashedLine([-6.85, target_y, 0], [1.65, target_y, 0], color=GREEN, stroke_width=2)
        entry_t = self.label_chip("ENTRY: rejection at VAL", CYAN).scale(0.72).move_to([-5.45, entry_y + 0.25, 0])
        stop_t = self.label_chip("INVALIDATION", RED).scale(0.72).move_to([-5.8, stop_y + 0.25, 0])
        target_t = self.label_chip("TARGET: POC", GREEN).scale(0.72).move_to([-5.8, target_y + 0.25, 0])
        risk_rect = Rectangle(width=2.3, height=abs(entry_y - stop_y), fill_color=RED, fill_opacity=0.10, stroke_width=0).move_to([-1.1, (entry_y + stop_y) / 2, 0])
        reward_rect = Rectangle(width=2.3, height=abs(target_y - entry_y), fill_color=GREEN, fill_opacity=0.10, stroke_width=0).move_to([-1.1, (entry_y + target_y) / 2, 0])
        self.play(Create(entry), Create(stop), Create(target), FadeIn(entry_t), FadeIn(stop_t), FadeIn(target_t), FadeIn(risk_rect), FadeIn(reward_rect))

        formula_title = self.txt("POSITION SIZE", 18, ORANGE, BOLD).move_to(risk_panel.get_top() + DOWN * 0.4)
        formula = VGroup(
            self.txt("account risk", 18, WHITE),
            Line(LEFT * 1.25, RIGHT * 1.25, color=MUTED, stroke_width=1.5),
            self.txt("stop distance", 18, WHITE),
        ).arrange(DOWN, buff=0.1).move_to(risk_panel.get_center() + UP * 0.25)
        equals = self.txt("= units to trade", 17, MUTED).next_to(formula, DOWN, buff=0.28)
        rule = self.label_chip("risk small • stay consistent", ORANGE).scale(0.77).move_to(risk_panel.get_bottom() + UP * 0.46)
        self.play(Write(formula_title), FadeIn(formula), FadeIn(equals), FadeIn(rule))
        self.show_caption(NARRATION["trade_2"], 2.2)

        disclaimer = self.txt("Educational framework only — not financial advice", 15, MUTED).move_to(DOWN * 3.38)
        self.play(FadeIn(disclaimer))
        self.wait(0.8 * PACE)
        self.wipe(header, steps, arrows, chart_panel, risk_panel, entry, stop, target, entry_t, stop_t, target_t,
                  risk_rect, reward_rect, formula_title, formula, equals, rule, disclaimer)

    # ------------------------------------------------------------------
    # 07 — Recap and outro
    # ------------------------------------------------------------------
    def recap(self) -> None:
        top_chip = self.label_chip("The auction never stops", CYAN).move_to(UP * 3.25)
        heading = self.txt("READ THE AUCTION", 54, WHITE, BOLD).move_to(UP * 2.45)
        self.play(FadeIn(top_chip, shift=DOWN * 0.1), FadeIn(heading, shift=UP * 0.15))

        cards = VGroup()
        data = [
            ("01", "VALUE", "Where is trade accepted?", PURPLE),
            ("02", "PARTICIPATION", "Who is acting with urgency?", CYAN),
            ("03", "RESPONSE", "Does price hold or fail?", GREEN),
        ]
        for number, title, body, color in data:
            box = self.panel(4.45, 2.35, PANEL_2)
            ring = Circle(radius=0.32, stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.08)
            num = self.txt(number, 17, color, BOLD, MONO).move_to(ring)
            ttl = self.txt(title, 23, WHITE, BOLD)
            bdy = self.txt(body, 16, MUTED)
            content = VGroup(VGroup(ring, num), ttl, bdy).arrange(DOWN, buff=0.18).move_to(box)
            accent = Line(box.get_corner(DL) + RIGHT * 0.2, box.get_corner(DR) + LEFT * 0.2, color=color, stroke_width=4)
            cards.add(VGroup(box, content, accent))
        cards.arrange(RIGHT, buff=0.4).move_to(DOWN * 0.05)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.22) for c in cards], lag_ratio=0.15), run_time=1.2)
        self.show_caption(NARRATION["recap"], 2.8)

        flow = VGroup(
            self.txt("PRICE", 18, MUTED, BOLD), self.txt("searches for", 16, MUTED),
            self.txt("VALUE", 22, PURPLE, BOLD), self.txt("through", 16, MUTED),
            self.txt("TIME + VOLUME", 22, CYAN, BOLD),
        ).arrange(RIGHT, buff=0.17).move_to(DOWN * 1.75)
        closing_line = self.txt("Observe first. Form a hypothesis. Define the risk.", 24, WHITE, BOLD).move_to(DOWN * 2.55)
        source_note = self.txt("AUCTION MARKET THEORY • EDUCATIONAL EXPLAINER", 14, MUTED, font=MONO).move_to(DOWN * 3.42)
        self.play(FadeIn(flow, shift=UP * 0.12), run_time=0.6)
        self.play(Write(closing_line), FadeIn(source_note), run_time=0.9)
        self.wait(2.0 * PACE)
        self.hide_caption()
        self.play(FadeOut(cards), FadeOut(flow), FadeOut(closing_line), FadeOut(source_note), FadeOut(top_chip),
                  heading.animate.set_color(CYAN).scale(0.92), run_time=0.9)
        self.wait(0.8 * PACE)
        self.play(FadeOut(heading), run_time=0.6)


# Optional short render for testing installation and visual style quickly.
class AuctionMarketTheoryTeaser(AuctionMarketTheoryExplainer):
    def construct(self):
        self.caption_mob = None
        self.add(self.make_background())
        self.hook()
