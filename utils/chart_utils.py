import plotly.graph_objects as go
import pandas as pd
from collections import Counter

# ── Design tokens ────────────────────────────────────────
PANEL   = 'rgba(255,255,255,0.025)'
GRID    = 'rgba(255,255,255,0.06)'
TEXT    = '#e2e8f0'
SUBTEXT = '#64748b'
ACCENT  = '#667eea'

MOOD_COLORS = {
    'Happy':    '#00e87a',
    'Calm':     '#00c4ff',
    'Neutral':  '#94a3b8',
    'Sad':      '#4fc3f7',
    'Stressed': '#ffa502',
    'Angry':    '#ff4757',
    'Tired':    '#a29bfe',
    'Energetic':'#ffd93d',
    'No Data':  '#334155',
}

TEAM_COLORS = {
    'Team Alpha 🔵': '#667eea',
    'Team Beta 🟢':  '#00e87a',
    'Team Gamma 🔴': '#ff4757',
}

# ── Shared helpers ───────────────────────────────────────
def _base(title='', height=360, margin=None):
    return dict(
        title=dict(text=title,
                   font=dict(size=16, color=TEXT, family='Sora, sans-serif'),
                   x=0.5, xanchor='center', y=0.97),
        height=height,
        paper_bgcolor=PANEL,
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT, family='Sora, sans-serif', size=12),
        margin=margin or dict(l=50, r=40, t=60, b=50),

    )

def _axis(title='', grid=True):
    return dict(
        title=dict(text=title, font=dict(color=SUBTEXT, size=11)),
        gridcolor=GRID if grid else 'rgba(0,0,0,0)',
        showgrid=grid, zeroline=False,
        tickfont=dict(color=SUBTEXT, size=10),
        linecolor=GRID,
    )

def _empty(msg='No Data'):
    fig = go.Figure()
    fig.add_annotation(text=f'<b>{msg}</b>', x=0.5, y=0.5,
                       showarrow=False, font=dict(size=14, color='#475569'))
    fig.update_layout(
        **_base(height=300),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
    )
    return fig


# ══════════════════════════════════════════════════════════
#  1. OVERALL MOOD BAR CHART
#     app.py: create_overall_mood_chart(ts['mood_distribution'])
#     ts['mood_distribution'] = {'Happy': 3, 'Stressed': 2, ...}
# ══════════════════════════════════════════════════════════

def create_overall_mood_chart(mood_distribution: dict):
    if not mood_distribution or sum(mood_distribution.values()) == 0:
        return _empty('No mood data yet')

    items  = sorted(mood_distribution.items(), key=lambda x: -x[1])
    labels = [i[0] for i in items]
    values = [i[1] for i in items]
    colors = [MOOD_COLORS.get(l, ACCENT) for l in labels]

    fig = go.Figure()
    # Glow shadow (behind, wider)
    # Glow shadow with rgba opacity (plotly doesn't support 8-char hex)
    def _hex_rgba(h, a=0.13):
        h = h.lstrip('#')
        r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f'rgba({r},{g},{b},{a})'
    shadow_colors = [_hex_rgba(c) for c in colors]
    fig.add_trace(go.Bar(
        x=labels, y=values,
        marker=dict(color=shadow_colors, line=dict(width=0)),
        hoverinfo='skip', showlegend=False, width=0.75,
    ))
    # Main bars
    fig.add_trace(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors,
                    line=dict(color='rgba(255,255,255,0.08)', width=1)),
        text=values, textposition='outside',
        textfont=dict(color=TEXT, size=13),
        hovertemplate='<b>%{x}</b><br>%{y} employees<extra></extra>',
        width=0.55,
    ))
    fig.update_layout(
        **_base('📊  Company-wide Mood Distribution', height=380,
                margin=dict(l=50, r=40, t=70, b=50)),
        barmode='overlay',
        xaxis=_axis('Emotion', grid=False),
        yaxis=_axis('Employees'),
        bargap=0.3,
    )
    return fig


# ══════════════════════════════════════════════════════════
#  2. TEAM MOOD GROUPED BAR
#     app.py: create_team_mood_charts(team_stats_all)
#     team_stats_all = {team_name: get_team_stats(name, data)}
#     get_team_stats returns dict with key 'mood_distribution'
#     app.py does: if fig2: st.plotly_chart(fig2, ...) → must return a single Figure
# ══════════════════════════════════════════════════════════

def create_team_mood_charts(team_stats: dict):
    """
    Returns ONE grouped bar Figure comparing moods across teams.
    app.py uses: st.plotly_chart(fig2, width="stretch")
    """
    if not team_stats:
        return _empty('No team data')

    # Collect all moods across all teams
    all_moods = set()
    for ts in team_stats.values():
        if ts:
            # Key from get_team_stats() is 'mood_distribution'
            all_moods.update(ts.get('mood_distribution', {}).keys())
    all_moods = sorted(all_moods)

    if not all_moods:
        return _empty('No mood data')

    team_names = list(team_stats.keys())
    # Short labels: "Alpha", "Beta", "Gamma"
    short_names = [n.split(" ")[1] if " " in n else n for n in team_names]

    fig = go.Figure()
    for mood in all_moods:
        values = []
        for tn in team_names:
            ts = team_stats.get(tn) or {}
            values.append(ts.get('mood_distribution', {}).get(mood, 0))

        fig.add_trace(go.Bar(
            name=mood,
            x=short_names,
            y=values,
            marker_color=MOOD_COLORS.get(mood, ACCENT),
            hovertemplate=f'<b>{mood}</b> · %{{x}}<br>%{{y}} employees<extra></extra>',
        ))

    fig.update_layout(
        **_base('🏢  Team Mood Breakdown', height=380,
                margin=dict(l=50, r=40, t=70, b=50)),
        barmode='group',
        xaxis=_axis('Team', grid=False),
        yaxis=_axis('Employees'),
        showlegend=True,
        legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center',
                    font=dict(size=10, color=SUBTEXT),
                    bgcolor='rgba(0,0,0,0)'),
        bargap=0.2, bargroupgap=0.05,
    )
    return fig


# ══════════════════════════════════════════════════════════
#  3. STRESS DISTRIBUTION
#     app.py: create_stress_distribution(emp_stress)
#     emp_stress = [{'name': 'Raksha', 'stress': 7.2}, ...]
# ══════════════════════════════════════════════════════════

def create_stress_distribution(emp_stress: list):
    if not emp_stress:
        return _empty('No stress data')

    df = pd.DataFrame(emp_stress).sort_values('stress', ascending=True)
    colors = []
    for s in df['stress']:
        if   s >= 8: colors.append('#ff4757')
        elif s >= 6: colors.append('#ffa502')
        elif s >= 4: colors.append('#ffd93d')
        else:        colors.append('#00e87a')

    fig = go.Figure()
    # Background track
    fig.add_trace(go.Bar(
        y=df['name'], x=[10] * len(df), orientation='h',
        marker=dict(color='rgba(255,255,255,0.03)', line=dict(width=0)),
        hoverinfo='skip', showlegend=False,
    ))
    # Actual bars
    fig.add_trace(go.Bar(
        y=df['name'], x=df['stress'], orientation='h',
        marker=dict(color=colors,
                    line=dict(color='rgba(0,0,0,0.15)', width=1)),
        text=df['stress'].round(1), textposition='outside',
        textfont=dict(color=TEXT, size=11),
        hovertemplate='<b>%{y}</b><br>Stress: %{x}/10<extra></extra>',
    ))
    for xv, col, lbl in [(6, '#ffa502', 'Warning'), (8, '#ff4757', 'Critical')]:
        fig.add_vline(x=xv, line_dash='dot', line_color=col, line_width=1.5,
                      annotation_text=lbl,
                      annotation_font=dict(color=col, size=10),
                      annotation_position='top right')

    fig.update_layout(
        **_base('⚠️  Employee Stress Distribution',
                height=max(300, len(df) * 36 + 100),
                margin=dict(l=120, r=70, t=66, b=50)),
        barmode='overlay',
        xaxis={**_axis('Stress Level (0–10)'), 'range': [0, 11]},
        yaxis=_axis(grid=False),
    )
    return fig


# ══════════════════════════════════════════════════════════
#  4. TEAM HEALTH GAUGE
#     app.py: create_team_health_gauge(health, f"{td['icon']} {team_name.split(' ')[1]}")
#     e.g.  : create_team_health_gauge(72.0, "🔵 Alpha")
# ══════════════════════════════════════════════════════════

def create_team_health_gauge(score: float, team_name: str = ''):
    needle = '#00e87a' if score >= 70 else '#ffa502' if score >= 40 else '#ff4757'

    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode='gauge+number',
        value=score,
        title=dict(text=f'<b>{team_name}</b><br>Team Health',
                   font=dict(size=14, color=TEXT)),
        number=dict(font=dict(size=44, color=needle, family='Sora, sans-serif'),
                    suffix='/100'),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=SUBTEXT,
                      tickfont=dict(size=9, color=SUBTEXT), dtick=25),
            bar=dict(color=needle, thickness=0.22),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
            steps=[
                dict(range=[0,  40], color='rgba(255,71,87,0.15)'),
                dict(range=[40, 70], color='rgba(255,165,2,0.12)'),
                dict(range=[70,100], color='rgba(0,232,122,0.12)'),
            ],
            threshold=dict(line=dict(color=needle, width=3),
                           thickness=0.8, value=score),
        ),
    ))
    fig.update_layout(
        height=250, paper_bgcolor=PANEL,
        font=dict(color=TEXT, family='Sora, sans-serif'),
        margin=dict(l=30, r=30, t=40, b=20),
    )
    return fig


# ══════════════════════════════════════════════════════════
#  5. MOOD TIMELINE
#     app.py imports create_mood_timeline_chart from mood_tracking.py
#     This function is for any direct use elsewhere
# ══════════════════════════════════════════════════════════

def create_mood_timeline(employee: str, history: list):
    if not history:
        return _empty(f'No history for {employee}')

    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['stress_level'],
        mode='lines+markers', name='Stress',
        line=dict(color='#ff4757', width=2.5, shape='spline'),
        marker=dict(size=7, color='#ff4757',
                    line=dict(color='rgba(15,12,41,0.8)', width=2)),
        fill='tozeroy', fillcolor='rgba(255,71,87,0.08)',
        hovertemplate='<b>%{x|%b %d}</b><br>Stress: %{y}/10<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['workload'],
        mode='lines+markers', name='Workload',
        line=dict(color='#00c4ff', width=2, dash='dot', shape='spline'),
        marker=dict(size=6, color='#00c4ff'),
        hovertemplate='<b>%{x|%b %d}</b><br>Workload: %{y}/10<extra></extra>',
        showlegend=True,
    ))
    fig.add_hline(y=7, line_dash='dot', line_color='#ffa502', line_width=1.2,
                  annotation_text='⚠️ Warning Zone',
                  annotation_font=dict(color='#ffa502', size=10),
                  annotation_position='top right')

    fig.update_layout(
        **_base(f'📈  {employee} — Stress & Workload Timeline', height=340,
                margin=dict(l=55, r=50, t=66, b=50)),
        xaxis={**_axis('Date'), 'showgrid': False},
        yaxis={**_axis('Level (0–10)'), 'range': [0, 10.5]},
        showlegend=True,
        legend=dict(orientation='h', y=1.06, x=1, xanchor='right',
                    font=dict(size=10, color=SUBTEXT), bgcolor='rgba(0,0,0,0)'),
        hovermode='x unified',
    )
    return fig


# ══════════════════════════════════════════════════════════
#  6. MOOD DISTRIBUTION DONUT — single employee
# ══════════════════════════════════════════════════════════

def create_mood_distribution_chart(employee: str, history: list):
    if not history:
        return _empty(f'No data for {employee}')

    counts = Counter(h.get('emotion', 'Neutral') for h in history)
    labels = list(counts.keys())
    values = list(counts.values())
    colors = [MOOD_COLORS.get(l, '#555') for l in labels]

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors,
                    line=dict(color='rgba(15,12,41,0.9)', width=3)),
        textinfo='label+percent',
        textfont=dict(size=11, color=TEXT),
        pull=[0.06 if v == max(values) else 0 for v in values],
        hovertemplate='<b>%{label}</b><br>%{value} entries (%{percent})<extra></extra>',
    ))
    top_mood  = max(counts, key=counts.get)
    top_color = MOOD_COLORS.get(top_mood, ACCENT)
    fig.add_annotation(
        text=(f'<b style="color:{top_color};font-size:15px">{top_mood}</b>'
              f'<br><span style="font-size:10px;color:{SUBTEXT}">Top Mood</span>'),
        x=0.5, y=0.5, showarrow=False,
    )
    fig.update_layout(
        **_base(f'🎭  {employee} — Mood Mix', height=300,
                margin=dict(l=10, r=10, t=56, b=60)),
        showlegend=True,
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center',
                    font=dict(size=10, color=SUBTEXT), bgcolor='rgba(0,0,0,0)'),
    )
    return fig


# ══════════════════════════════════════════════════════════
#  7. TEAM × MOOD HEATMAP
#     team_data = {team_name: get_team_stats(name, data)}
#     key is 'mood_distribution' (NOT 'moods')
# ══════════════════════════════════════════════════════════

def create_mood_heatmap(team_data: dict):
    if not team_data:
        return _empty('No team data')

    mood_cols = ['Happy', 'Calm', 'Neutral', 'Tired', 'Stressed', 'Angry', 'Energetic']
    teams, z  = [], []

    for team, td in team_data.items():
        if not td:
            continue
        # get_team_stats() uses key 'mood_distribution'
        moods = td.get('mood_distribution', td.get('moods', {}))
        teams.append(team.split(" ")[1] if " " in team else team)
        z.append([moods.get(m, 0) for m in mood_cols])

    if not teams:
        return _empty('No team data')

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=z, x=mood_cols, y=teams,
        colorscale=[
            [0.0, 'rgba(15,12,41,1)'],
            [0.3, 'rgba(102,126,234,0.4)'],
            [0.7, 'rgba(118,75,162,0.7)'],
            [1.0, 'rgba(246,79,89,1)'],
        ],
        text=z,
        texttemplate='<b>%{text}</b>',
        textfont=dict(color=TEXT, size=13),
        showscale=True,
        colorbar=dict(tickfont=dict(color=SUBTEXT, size=10),
                      outlinewidth=0, thickness=12),
        hovertemplate='<b>%{y}</b> · %{x}<br>Count: %{z}<extra></extra>',
    ))
    fig.update_layout(
        **_base('🔥  Team × Mood Heatmap', height=290,
                margin=dict(l=80, r=80, t=70, b=50)),
        xaxis=dict(side='top', tickfont=dict(color=SUBTEXT, size=11),
                   showgrid=False, zeroline=False),
        yaxis=dict(tickfont=dict(color=TEXT, size=11),
                   showgrid=False, zeroline=False),
    )
    return fig


if __name__ == '__main__':
    print('✅ chart_utils loaded — all functions ready')