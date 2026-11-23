"""Dzongkha display strings for Plotly; trace coordinates remain numeric."""
import math
import re
import numbers
import numpy as np
from result_analysis.core.numerals import digits, display_number
from result_analysis.core.translations import translate
from result_analysis.core.section_names import display_section


def localize_plotly(fig, section_x=False, section_y=False):
    for trace in fig.data:
        if trace.type == 'heatmap':
            trace.text = [[display_number(v, 'dz') for v in row] for row in trace.z]
            trace.texttemplate = '%{text}'
            grid = np.empty(np.asarray(trace.z).shape + (2,), dtype=object)
            xvalues = list(trace.x) if trace.x is not None else list(range(grid.shape[1]))
            yvalues = list(trace.y) if trace.y is not None else list(range(grid.shape[0]))
            for row, yvalue in enumerate(yvalues):
                for col, xvalue in enumerate(xvalues):
                    grid[row, col, 0] = display_section(xvalue, 'dz') if section_x else translate(str(xvalue),'dz')
                    grid[row, col, 1] = display_section(yvalue, 'dz') if section_y else translate(str(yvalue),'dz')
            trace.customdata = grid
            if trace.hovertemplate:
                for field, column in [('x',0),('y',1)]:
                    trace.hovertemplate = re.sub(r'%\{'+field+r'(?::[^}]*)?\}', lambda _, col=column: f'%{{customdata[{col}]}}', trace.hovertemplate)
                trace.hovertemplate = re.sub(r'%\{z(?::[^}]*)?\}', '%{text}', trace.hovertemplate)
            finite = np.asarray(trace.z, dtype=float)
            finite = finite[np.isfinite(finite)]
            if len(finite) and trace.coloraxis:
                vals = np.linspace(float(finite.min()), float(finite.max()), 5)
                fig.update_coloraxes(colorbar_tickvals=vals, colorbar_ticktext=[display_number(v,'dz') for v in vals])
            continue
        count = max(len(trace.x) if trace.x is not None else 0, len(trace.y) if trace.y is not None else 0)
        if not count:
            continue
        previous = np.asarray(trace.customdata, dtype=object) if trace.customdata is not None else np.empty((count, 0),dtype=object)
        if previous.ndim == 1:
            previous = previous.reshape(count,1)
        if previous.shape[0] != count:
            continue
        previous = np.array([[display_number(v,'dz') if isinstance(v,numbers.Number) else translate(str(v),'dz') for v in row] for row in previous],dtype=object)
        fields = {}
        for key in ('x','y'):
            values = getattr(trace,key,None)
            if values is not None and len(values)==count:
                fields[key] = previous.shape[1]
                def display_coordinate(v):
                    if isinstance(v,numbers.Number):
                        return display_number(v,'dz')
                    if (key == 'x' and section_x) or (key == 'y' and section_y):
                        return display_section(v,'dz')
                    return translate(str(v),'dz')
                previous = np.column_stack([previous,[display_coordinate(v) for v in values]])
        trace.customdata = previous
        if trace.hovertemplate:
            template = trace.hovertemplate
            # customdata now contains ready-to-display strings, never numeric formats.
            template = re.sub(r'%\{customdata\[(\d+)\](?::[^}]*)?\}',r'%{customdata[\1]}',template)
            for field,column in fields.items():
                template = re.sub(r'%\{'+field+r'(?::[^}]*)?\}',lambda _: f'%{{customdata[{column}]}}',template)
            trace.hovertemplate = template
        if trace.type == 'bar' and 'y' in fields:
            trace.text = [display_number(v,'dz') for v in trace.y]
            trace.texttemplate = '%{text}'
    for coordinate,axis in [('x',fig.layout.xaxis),('y',fig.layout.yaxis)]:
        if axis.tickmode == 'array':
            if axis.ticktext:
                axis.ticktext = [digits(v) for v in axis.ticktext]
            continue
        values=[]
        for trace in fig.data:
            data=getattr(trace,coordinate,None)
            if data is not None:
                values += [float(v) for v in data if isinstance(v,numbers.Number) and math.isfinite(float(v))]
        if not values:
            continue
        low=min(0,min(values)); high=max(values)
        if high <= low: high=low+1
        step=10**math.floor(math.log10((high-low)/5))
        step *= next((v for v in (1,2,5,10) if v*step >= (high-low)/5),10)
        ticks=np.arange(math.floor(low/step)*step, math.ceil(high/step)*step+step/2, step)
        axis.tickmode='array';axis.tickvals=ticks
        axis.ticktext=[digits(f'{v:g}') for v in ticks]
    return fig
