"""Shared chart specifications rendered interactively or into PDF images."""

from dataclasses import dataclass
from io import BytesIO
import textwrap
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from result_analysis.core.subjects_config import COLORS, PASS_PERCENT
from result_analysis.core.translations import t, translate, language
from result_analysis.core.section_names import display_section, section_list
from result_analysis.core.numerals import digits


@dataclass
class Chart:
    """Portable chart definition: screen and PDF share exactly the same data."""

    title: str
    kind: str
    data: pd.DataFrame
    x: str = ""
    y: str = ""
    group: str | None = None
    pass_line: bool = False


def interactive(chart: Chart) -> go.Figure:
    """Plotly figures with readable labels and explicit numerical hover data."""
    d = chart.data
    if chart.kind == "distribution":
        values = d[chart.x].dropna()
        counts, edges = np.histogram(values, bins=np.arange(0, 101, 10))
        fig = go.Figure(
            go.Bar(
                x=(edges[:-1] + edges[1:]) / 2,
                y=counts,
                width=10,
                name="Students",
                marker_color="#3288D1",
                hovertemplate="Score bin %{x}%<br>Students %{y}<extra></extra>",
            )
        )
        if len(values) >= 2 and values.nunique() > 1:
            grid = np.linspace(0, 100, 250)
            density = gaussian_kde(values)(grid) * len(values) * 10
            fig.add_trace(
                go.Scatter(
                    x=grid, y=density, name="KDE (count scale)", line_color="#D84B9B"
                )
            )
        for name, val, color in [
            ("Mean", values.mean(), "#2C9B73"),
            ("Median", values.median(), "#E88A32"),
        ]:
            if pd.notna(val):
                fig.add_vline(
                    x=val,
                    line_color=color,
                    annotation_text=f"{name} {val:.2f}",
                    annotation_position="top left"
                    if name == "Mean"
                    else "bottom right",
                )
        fig.add_vrect(
            x0=0, x1=PASS_PERCENT, fillcolor="red", opacity=0.08, line_width=0
        )
        fig.update_xaxes(title="Score (%)", range=[0, 100])
        fig.update_yaxes(title="Students (KDE scaled to bin counts)")
    elif chart.kind == "heatmap":
        fig = px.imshow(
            d,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="Blues",
            labels={
                "x": d.columns.name or "Subject",
                "y": d.index.name or "Section",
                "color": chart.y,
            },
        )
    elif chart.kind == "box":
        fig = px.box(
            d,
            x=chart.x,
            y=chart.y,
            color=chart.group,
            points="outliers",
            color_discrete_map=COLORS,
            labels={chart.y: "Score (%)"},
        )
    else:
        fig = px.bar(
            d,
            x=chart.x,
            y=chart.y,
            color=chart.group,
            barmode="group",
            text_auto=".2f",
            color_discrete_map=COLORS,
            hover_data={c: ":.2f" for c in d.select_dtypes("number").columns},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        title=dict(text=chart.title, font_size=18),
        template="plotly_dark",
        paper_bgcolor="#142c3d",
        plot_bgcolor="#142c3d",
        margin=dict(t=80, b=100),
        legend_title_text=chart.group or "",
        font=dict(size=13, color="#d5e3ea", family="Source Sans 3, sans-serif"),
        colorway=["#75b8c7", "#d9b477", "#a3e1d2", "#a89cdb"],
        height=470,
    )
    fig.update_xaxes(showgrid=False, automargin=True, title_standoff=18)
    fig.update_yaxes(
        gridcolor="#314958", zerolinecolor="#496170", automargin=True, title_standoff=18
    )
    if chart.pass_line:
        fig.add_hline(
            y=PASS_PERCENT,
            line_dash="dash",
            line_color="#C13B43",
            annotation_text="Pass threshold 40%",
        )
    # Translate rendered strings without changing trace data, keys or colors.
    def localize(obj):
        if isinstance(obj, dict):
            return {k: (t(v) if k in {'text','name','hovertemplate'} and isinstance(v,str) else localize(v)) for k,v in obj.items()}
        if isinstance(obj,list): return [localize(v) for v in obj]
        return obj
    original_trace_names = [trace.name for trace in fig.data]
    fig = go.Figure(localize(fig.to_dict()))
    for trace_index, trace in enumerate(fig.data):
        if chart.group == "Section":
            original_name = original_trace_names[trace_index]
            trace.name = display_section(original_name, language())
            if trace.hovertemplate:
                trace.hovertemplate = trace.hovertemplate.replace(f"={original_name}<br>", f"={trace.name}<br>")
        if trace.hovertemplate:
            trace.hovertemplate = re.sub(r'=([^<%]+)(<br>|<extra>)', lambda m: '=' + t(m[1]) + m[2], trace.hovertemplate)
            trace.hovertemplate = re.sub(
                r'(^|<br>)([^<=>]+)=',
                lambda m: m[1] + t(m[2]) + '=', trace.hovertemplate)

    if chart.kind == 'heatmap':
        fig.update_xaxes(tickmode='array', tickvals=list(d.columns), ticktext=[t(str(v)) for v in d.columns])
        fig.update_yaxes(tickmode='array', tickvals=list(d.index), ticktext=[display_section(v, language()) if d.index.name == "Section" else t(str(v)) for v in d.index])
    elif chart.x in d and not pd.api.types.is_numeric_dtype(d[chart.x]):
        categories = list(d[chart.x].dropna().unique())
        fig.update_xaxes(tickmode='array', tickvals=categories, ticktext=[display_section(v, language()) if chart.x == "Section" else t(str(v)) for v in categories])
    fig.update_layout(font_family="Source Sans 3, Result Tibetan, sans-serif")
    for axis in (fig.layout.xaxis,fig.layout.yaxis):
        if axis.title.text: axis.title.text=t(axis.title.text)
    if language() == 'dz':
        from result_analysis.core.chart_numerals import localize_plotly
        localize_plotly(fig, section_x=chart.x == "Section", section_y=chart.kind == "heatmap" and d.index.name == "Section")
    return fig


def image_bytes(chart: Chart, lang: str = "en") -> bytes:
    """Render a static counterpart with matplotlib, without a browser dependency."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from result_analysis.core.pdf_report import font_path
    from matplotlib.font_manager import FontProperties

    font = FontProperties(fname=str(font_path())) if font_path() else None
    with plt.rc_context({"font.size": 12}):
        fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
        d = chart.data.copy()
        if lang == 'dz':
            for col in d.select_dtypes(include=['object','string']):
                d[col] = d[col].map(lambda v: section_list(v, lang) if col == 'Section' else translate(v, lang))
            if chart.kind == 'heatmap':
                d.columns = [translate(c, lang) for c in d.columns]
                d.index = [display_section(c, lang) if chart.data.index.name == "Section" else translate(c, lang) for c in d.index]
        if chart.kind == "distribution":
            values = d[chart.x].dropna()
            ax.hist(
                values, bins=np.arange(0, 101, 10), color="#3288D1", edgecolor="white"
            )
            if len(values) >= 2 and values.nunique() > 1:
                grid = np.linspace(0, 100, 250)
                ax.plot(
                    grid,
                    gaussian_kde(values)(grid) * len(values) * 10,
                    color="#D84B9B",
                    label="KDE",
                )
            for name, value, color in [
                ("Mean", values.mean(), "#2C9B73"),
                ("Median", values.median(), "#E88A32"),
            ]:
                if pd.notna(value):
                    ax.axvline(value, color=color, label=f"{name} {value:.2f}")
            ax.axvspan(0, PASS_PERCENT, color="red", alpha=0.08)
            ax.set(xlabel="Score (%)", ylabel="Students", xlim=(0, 100))
            if len(values):
                ax.legend(fontsize=10)
        elif chart.kind == "heatmap":
            array = d.to_numpy(dtype=float)
            image = ax.imshow(np.ma.masked_invalid(array), aspect="auto", cmap="Blues")
            fig.colorbar(image, ax=ax, label=chart.y)
            ax.set_xticks(
                range(len(d.columns)),
                [textwrap.fill(str(c), 16) for c in d.columns],
                rotation=30,
                ha="right",
            )
            ax.set_yticks(range(len(d)), d.index)
            for r in range(len(d)):
                for c in range(len(d.columns)):
                    ax.text(
                        c,
                        r,
                        f"{array[r, c]:.2f}" if np.isfinite(array[r, c]) else "NA",
                        ha="center",
                        va="center",
                        fontsize=10,
                        color="white"
                        if np.isfinite(array[r, c]) and image.norm(array[r, c]) > 0.55
                        else "black",
                    )
            ax.set(xlabel="Subject", ylabel="Section")
        elif chart.kind == "box":
            labels = list(d[chart.x].unique())
            arrays = [
                d.loc[d[chart.x].eq(v), chart.y].dropna().to_numpy() for v in labels
            ]
            ax.boxplot(arrays, tick_labels=[textwrap.fill(str(x), 16) for x in labels])
            ax.set(xlabel=chart.x, ylabel="Score (%)")
        else:
            if chart.group:
                pivot = d.pivot(index=chart.x, columns=chart.group, values=chart.y)
            else:
                pivot = d.set_index(chart.x)[[chart.y]]
            x = np.arange(len(pivot))
            width = 0.8 / max(1, len(pivot.columns))
            for j, group in enumerate(pivot.columns):
                values = pivot[group].to_numpy(dtype=float)
                bars = ax.bar(
                    x - 0.4 + width / 2 + j * width,
                    values,
                    width,
                    label=str(group),
                    color={translate(k, lang): v for k, v in COLORS.items()}.get(group),
                )
                ax.bar_label(
                    bars,
                    labels=[f"{v:.2f}" if np.isfinite(v) else "" for v in values],
                    fontsize=10,
                    padding=2,
                )
            ax.set_xticks(
                x,
                [textwrap.fill(str(v), 16) for v in pivot.index],
                rotation=25,
                ha="right",
            )
            ax.set(xlabel=chart.x, ylabel=chart.y)
            if chart.group:
                ax.legend(fontsize=10)
            ax.margins(y=0.2)
        if chart.pass_line:
            ax.axhline(PASS_PERCENT, color="#C13B43", linestyle="--", label="40% pass")
        ax.set_title(textwrap.fill(chart.title, 85), fontsize=15, fontproperties=font)
        if font:
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(font)
        if lang == 'dz':
            from matplotlib.text import Text
            from result_analysis.core.shaped_text import shape_artist
            from matplotlib.ticker import FuncFormatter
            for axis in fig.axes:
                if axis is not ax or chart.kind != 'heatmap':
                    axis.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: digits(f'{v:g}')))
                if axis is ax and chart.kind == 'distribution':
                    axis.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: digits(f'{v:g}')))
            # Force tick creation before translating all visible chart labels.
            for existing in fig.findobj(match=Text):
                if font:
                    size = existing.get_fontsize()
                    existing.set_fontproperties(font)
                    existing.set_fontsize(size)
            fig.canvas.draw()
            for artist in fig.findobj(match=Text):
                label = digits(translate(artist.get_text(), lang), lang)
                artist.set_text(label)
                if font:
                    size = artist.get_fontsize()
                    artist.set_fontproperties(font)
                    artist.set_fontsize(size)
                if any('\u0f00' <= c <= '\u0fff' for c in label):
                    shape_artist(artist, font_path())
        if lang == 'dz':
            fig.get_layout_engine().set(w_pad=0.2, h_pad=0.12)
        output = BytesIO()
        fig.savefig(output, format="png", dpi=140)
        plt.close(fig)
        return output.getvalue()
