"""One-off edit: turn the Studio panel into one compact column (run with any Python)."""
import ast

PANEL = "C:/Users/lilis/Documents/Unreal Projects/Midterm-a-tool-you-d-actually-use/Content/Python/lowpoly_studio_panel.py"
CORE = "C:/Users/lilis/Documents/Unreal Projects/Midterm-a-tool-you-d-actually-use/Content/Python/lowpoly_studio.py"

NEW_BUILD = '''        root = w._new(unreal.Border, widget, "LPSRoot")
        root.set_brush(w._rounded_brush(w._color("bg"), 0.0))
        root.set_padding(w._margin(0, 0, 0, 6))
        root.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_LEFT)
        # One column, the object on top and everything below it.  Arrows and
        # sliders sit two per line, so the whole Studio fits without scrolling.
        panel = w._new(unreal.VerticalBox, widget, "LPSPanel")
        root.add_child(w._size_box(widget, "LPSColumn", panel, width=STUDIO_WIDTH))
        w._add(host, root, w._margin(0, 0, 0, 0))

        # Title and category tabs share one line.
        header = w._new(unreal.HorizontalBox, widget, "LPSHeader")
        logo = header.add_child(_icon(widget, "LPSLogo", "studio", 16, "accent"))
        logo.set_padding(w._margin(0, 0, 5, 0))
        logo.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        title = header.add_child(w._text(widget, "LPSTitle", "Low-Poly Studio", True, w._color("text"), 11))
        title.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        title.set_padding(w._margin(0, 0, 10, 0))
        for index, kind in enumerate(core.KIND_ORDER):
            spec = core.KINDS[kind]
            button = _button(widget, "LPSTab_" + kind, spec["label"], "soft", 8, spec["icon"])
            button.on_clicked.add_callable(self.keep(self._tab_callback(kind)))
            w._add(header, button, w._margin(0 if index == 0 else 3, 0, 0, 0), fill=True)
        w._add(panel, w._size_box(widget, "LPSHeaderBox", header, height=26.0), w._margin(8, 6, 8, 4))

        # The preview: what the booth camera films, turning slowly.
        stage = w._new(unreal.Border, widget, "LPSStage")
        stage.set_brush(w._rounded_brush(w._color("card"), 8.0, w._color("line"), 1.0))
        stage.set_padding(w._margin(3, 3, 3, 2))
        stage.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
        stage_box = w._new(unreal.VerticalBox, widget, "LPSStageBox")
        picture = w._new(unreal.Image, widget, "LPSPreviewImage")
        picture.set_color_and_opacity(unreal.LinearColor(1, 1, 1, 1))
        stage_box.add_child(w._size_box(widget, "LPSPreviewBox", picture, core.PREVIEW_SIZE[0], core.PREVIEW_SIZE[1]))
        caption = stage_box.add_child(w._text(widget, "LPSCaption", "", True, w._color("text"), 8))
        caption.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER)
        caption.set_padding(w._margin(0, 2, 0, 0))
        stage.add_child(stage_box)
        w._add(panel, stage, w._margin(8, 0, 8, 3))

        switcher = w._new(unreal.WidgetSwitcher, widget, "LPSPages")
        for kind in core.KIND_ORDER:
            page = w._new(unreal.VerticalBox, widget, "LPSPage_" + kind)
            switcher.add_child(page)
            self._build_design_page(page, kind)
        w._add(panel, switcher)

        # Surprise, new variant and Add to forest on one line.
        actions = w._new(unreal.HorizontalBox, widget, "LPSActions")
        for name, label, icon, tip, method, tone in (
            ("LPSSurprise", "Surprise", "dice", "A random design", self.surprise, "soft"),
            ("LPSVariant", "Variant", "refresh", "Same design, another seed", self.new_variant, "soft"),
            ("LPSAdd", "Add to forest", "add", "Houdini bakes %d variants of this design; your forest grows them" % core.VARIANTS,
             self.add_to_forest, "primary"),
        ):
            button = _button(widget, name, label, tone, 9, icon)
            button.set_tool_tip_text(tip)
            button.on_clicked.add_callable(self.keep(self._call(method)))
            slot = w._add(actions, button, w._margin(0 if name == "LPSSurprise" else 3, 0, 0, 0), fill=True)
            if tone == "primary":
                size = unreal.SlateChildSize()
                size.set_editor_property("size_rule", unreal.SlateSizeRule.FILL)
                size.set_editor_property("value", 1.6)
                slot.set_size(size)
        w._add(panel, w._size_box(widget, "LPSActionsBox", actions, height=26.0), w._margin(8, 3, 8, 3))

        # The population, with "Grow forest now" on its title line.
        forest = w._new(unreal.Border, widget, "LPSForestCard")
        forest.set_brush(w._rounded_brush(w._color("card"), 8.0, w._color("line"), 1.0))
        forest.set_padding(w._margin(8, 4, 8, 5))
        forest.set_tool_tip_text("What the World Builder grows. Click a name to edit it; x1/x2/x3 is how often it grows.")
        forest_box = w._new(unreal.VerticalBox, widget, "LPSForestBox")
        heading = w._new(unreal.HorizontalBox, widget, "LPSForestHeading")
        icon = heading.add_child(_icon(widget, "LPSForestIcon", "forest", 12, "accent"))
        icon.set_padding(w._margin(0, 0, 5, 0))
        icon.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        label = w._text(widget, "LPSForestTitle", "Your forest", True, w._color("text"), 9)
        w._add(heading, label, w._margin(0, 0, 0, 0), fill=True).set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        grow = _button(widget, "LPSGrow", "Grow forest now", "soft", 8, "vegetation")
        grow.set_tool_tip_text("Same ground, new plants with your designs (World Builder: New plants)")
        grow.on_clicked.add_callable(self.keep(self._call(self.grow_now)))
        heading.add_child(w._size_box(widget, "LPSGrowBox", grow, height=20.0))
        forest_box.add_child(heading)
        w._add(forest_box, w._new(unreal.VerticalBox, widget, "LPSPopulation"), w._margin(0, 3, 0, 0))
        forest.add_child(forest_box)
        w._add(panel, forest, w._margin(8, 0, 8, 3))

        status = w._new(unreal.Border, widget, "LPSStatus")
        status.set_brush(w._rounded_brush(w._color("card"), 6.0, w._color("line"), 1.0))
        status.set_padding(w._margin(8, 3, 8, 3))
        status.add_child(w._text(widget, "LPSStatusText", "Ready.", False, w._color("text"), 8, wrap=True))
        w._add(panel, status, w._margin(8, 0, 8, 0))

        self.show_kind(self.kind)
        self.refresh_population()
        w._resize_icons(widget)
        widget.invalidate_layout_and_volatility()
        widget.force_layout_prepass()

    def _grid(self, card, name):
        """Two columns inside a card; returns (left, right)."""
        widget = self.widget
        row = w._new(unreal.HorizontalBox, widget, name)
        left = w._new(unreal.VerticalBox, widget, name + "Left")
        right = w._new(unreal.VerticalBox, widget, name + "Right")
        w._add(row, left, w._margin(0, 0, 5, 0), fill=True)
        w._add(row, right, w._margin(5, 0, 0, 0), fill=True)
        w._add(card, row)
        return left, right

    def _card(self, page, name, title, tip, icon):
        """A compact card: a small title line, then its content."""
        widget = self.widget
        card = w._new(unreal.Border, widget, name + "Card")
        card.set_brush(w._rounded_brush(w._color("card"), 8.0, w._color("line"), 1.0))
        card.set_padding(w._margin(8, 3, 8, 4))
        card.set_tool_tip_text(tip)
        box = w._new(unreal.VerticalBox, widget, name + "Box")
        heading = w._new(unreal.HorizontalBox, widget, name + "Heading")
        mark = heading.add_child(_icon(widget, name + "Icon", icon, 11, "accent"))
        mark.set_padding(w._margin(0, 0, 5, 0))
        mark.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        heading.add_child(w._text(widget, name + "Title", title, True, w._color("text"), 9))
        w._add(box, heading, w._margin(0, 0, 0, 2))
        card.add_child(box)
        w._add(page, card, w._margin(8, 0, 8, 3))
        return box

    def _build_design_page(self, page, kind):
        widget, spec = self.widget, core.KINDS[kind]
        if kind == "import":
            self._build_source(page)
        look = self._card(page, "LPSLook_" + kind, "Look", "The arrows change the look; the preview follows.", "palette")
        columns = self._grid(look, "LPSLookGrid_" + kind)
        for index, (key, label, options) in enumerate(spec["arrows"]):
            self._arrow_row(columns[index % 2], kind, key, label, options)
        tune = self._card(page, "LPSTune_" + kind, "Fine tuning", "Let go of a slider to see the change.", "scale")
        columns = self._grid(tune, "LPSTuneGrid_" + kind)
        for index, (key, label, low, high, default, decimals) in enumerate(spec["sliders"]):
            self._slider(columns[index % 2], kind, key, label, low, high, default, decimals)

    def _slider(self, panel, kind, key, label, low, high, default, decimals):
        """A slider half a line wide: short label, rail, value."""
        widget, name = self.widget, "LPS_%s_%s" % (kind, key)
        row = w._new(unreal.HorizontalBox, widget, name + "Row")
        caption = w._text(widget, name + "Label", label, False, w._color("muted"), 8)
        caption.set_min_desired_width(54.0)
        row.add_child(caption).set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        slider = w._new(unreal.Slider, widget, name + "Slider")
        slider.set_min_value(low)
        slider.set_max_value(high)
        slider.set_value(default)
        if not decimals:
            slider.set_step_size(1.0)
        try:
            slider.set_slider_bar_color(w._color("faint"))
            slider.set_slider_handle_color(w._color("accent"))
        except Exception:
            pass
        w._add(row, slider, w._margin(0, 0, 4, 0), fill=True)
        readout = w._text(widget, name + "Readout", "%.2f" % default if decimals else str(default), True, w._color("text"), 8)
        readout.set_min_desired_width(26.0)
        row.add_child(readout).set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
        w._add(panel, w._size_box(widget, name + "Box", row, height=19.0))
        slider.on_value_changed.add_callable(self.keep(self._slider_callback(kind, key, decimals)))
        slider.on_mouse_capture_end.add_callable(self.keep(self._call(self.changed)))

'''


def replace(text, old, new):
    assert old in text, old[:70]
    return text.replace(old, new)


s = open(PANEL, encoding="utf-8").read()
a = s.index('        root = w._new(unreal.Border, widget, "LPSRoot")')
b = s.index('    def _build_source(self, page):')
s = s[:a] + NEW_BUILD + s[b:]
s = replace(s, 'LEFT_WIDTH, RIGHT_WIDTH = 336.0, 372.0      # two columns: preview and actions | design controls',
            'STUDIO_WIDTH = 470.0')
s = replace(s, '''        caption.set_min_desired_width(66.0)''', '''        caption.set_min_desired_width(50.0)''')
s = replace(s, '''chip, 7.0, 16.0), w._margin(1, 0, 0, 0))''', '''chip, 5.0, 14.0), w._margin(1, 0, 0, 0))''')
ast.parse(s)
open(PANEL, "w", encoding="utf-8").write(s)

t = open(CORE, encoding="utf-8").read()
t = replace(t, "PREVIEW_SIZE = (320, 250)", "PREVIEW_SIZE = (448, 220)")
t = replace(t, '''    radius = max((extent.x ** 2 + extent.y ** 2 + extent.z ** 2) ** 0.5, 30.0)
    distance = radius / math.tan(math.radians(35.0 * 0.5)) * 0.95''', '''    radius = max((extent.x ** 2 + extent.y ** 2 + extent.z ** 2) ** 0.5, 30.0)
    # The picture is wider than tall: fit the object to its height.
    half_vertical = math.atan(math.tan(math.radians(35.0 * 0.5)) * PREVIEW_SIZE[1] / PREVIEW_SIZE[0])
    distance = radius / math.tan(half_vertical) * 0.9''')
ast.parse(t)
open(CORE, "w", encoding="utf-8").write(t)
print("ok")
