import sqlite3

import pandas as pd
import plotly.graph_objects as go

# --- Load data ---
conn = sqlite3.connect("breathing_log.db")
raw = pd.read_sql("SELECT * FROM daily_breathing;", conn)
conn.close()

# --- Aggregate per day ---
raw['date'] = pd.to_datetime(raw['date'])
daily = raw.groupby(raw['date'].dt.date).agg(
    total_minutes=('total_minutes', 'sum'),
    sessions=('sessions', 'sum')
).reset_index()

daily['date_str'] = daily['date'].astype(str)

# --- Compute cumulative sums ---
daily['cumulative_minutes'] = daily['total_minutes'].cumsum()
daily['cumulative_sessions'] = daily['sessions'].cumsum()

# --- Moving average (3-day window) ---
daily['minutes_ma'] = daily['total_minutes'].rolling(3, min_periods=1).mean()
daily['sessions_ma'] = daily['sessions'].rolling(3, min_periods=1).mean()

# --- Stats ---
mean_minutes = daily['total_minutes'].mean()
median_minutes = daily['total_minutes'].median()
mean_sessions = daily['sessions'].mean()
median_sessions = daily['sessions'].median()

# --- Create figures ---
# Daily minutes + MA
fig_minutes = go.Figure()
fig_minutes.add_trace(go.Scatter(
    x=daily['date_str'],
    y=daily['total_minutes'],
    mode='lines+markers',
    name='Daily Minutes',
    line=dict(color='skyblue')
))
fig_minutes.add_trace(go.Scatter(
    x=daily['date_str'],
    y=daily['minutes_ma'],
    mode='lines',
    name='3-Day MA',
    line=dict(color='darkblue', dash='dash')
))
fig_minutes.update_layout(title="Daily Breathing Minutes",
                          xaxis_title="Date", yaxis_title="Minutes")

# Daily sessions + MA
fig_sessions = go.Figure()
fig_sessions.add_trace(go.Scatter(
    x=daily['date_str'],
    y=daily['sessions'],
    mode='lines+markers',
    name='Daily Sessions',
    line=dict(color='lightgreen')
))
fig_sessions.add_trace(go.Scatter(
    x=daily['date_str'],
    y=daily['sessions_ma'],
    mode='lines',
    name='3-Day MA',
    line=dict(color='green', dash='dash')
))
fig_sessions.update_layout(
    title="Daily Breathing Sessions", xaxis_title="Date", yaxis_title="Sessions")

# Cumulative figures
fig_cum_minutes = go.Figure(go.Scatter(x=daily['date_str'], y=daily['cumulative_minutes'],
                                       mode='lines+markers', name='Cumulative Minutes', line=dict(color='darkblue')))
fig_cum_minutes.update_layout(
    title="Cumulative Minutes", xaxis_title="Date", yaxis_title="Minutes")

fig_cum_sessions = go.Figure(go.Scatter(x=daily['date_str'], y=daily['cumulative_sessions'],
                                        mode='lines+markers', name='Cumulative Sessions', line=dict(color='green')))
fig_cum_sessions.update_layout(
    title="Cumulative Sessions", xaxis_title="Date", yaxis_title="Sessions")

# Histograms
fig_hist_minutes = go.Figure(go.Histogram(
    x=daily['total_minutes'], nbinsx=20, marker_color='skyblue'))
fig_hist_minutes.update_layout(
    title="Distribution of Daily Minutes", xaxis_title="Minutes", yaxis_title="Count")

fig_hist_sessions = go.Figure(go.Histogram(
    x=daily['sessions'], nbinsx=10, marker_color='lightgreen'))
fig_hist_sessions.update_layout(
    title="Distribution of Daily Sessions", xaxis_title="Sessions", yaxis_title="Count")

# Stats table
table = go.Figure(data=[go.Table(
    header=dict(values=["Metric", "Minutes", "Sessions"],
                fill_color='paleturquoise', align='left'),
    cells=dict(values=[
        ["Mean", "Median"],
        [f"{mean_minutes:.2f}", f"{median_minutes:.2f}"],
        [f"{mean_sessions:.2f}", f"{median_sessions:.2f}"]
    ], fill_color='lavender', align='left'))
])

motivation_html = """
<div id="motivation" style="margin: 20px 0; font-family: Arial, sans-serif;">
    <h2 style="color:#00796B;">Motivation</h2>
    <p>
        According to scientific studies, working long hours without sufficient rest increases the risk of burnout, lowers productivity, and harms mental health. 
        Practices involving controlled breathing and mindfulness have been found beneficial for stress reduction, improving mood, mitigating fatigue, and enhancing overall well-being.
    </p>

    <h3 style="color:#004D40;">Evidence from Research</h3>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width:100%; margin-bottom:20px;">
        <tr style="background-color: #B2DFDB; font-weight: bold;">
            <td style="width:70%;">Finding</td>
            <td style="width:30%;">Reference</td>
        </tr>
        <tr>
            <td>Nurses who practiced daily breathing-meditation for 8 weeks showed reduced negative emotions and job burnout, and improved attention.</td>
            <td><a href="https://pubmed.ncbi.nlm.nih.gov/38814605/" target="_blank">PubMed</a></td>
        </tr>
        <tr>
            <td>Diaphragmatic breathing (deep belly breathing) is effective in reducing physiological and psychological stress in adults.</td>
            <td><a href="https://pubmed.ncbi.nlm.nih.gov/31436595/" target="_blank">PubMed</a></td>
        </tr>
        <tr>
            <td>Brief structured breathwork exercises (5 minutes daily) improved mood and reduced anxiety more than mindfulness meditation in some comparisons.</td>
            <td><a href="https://pubmed.ncbi.nlm.nih.gov/36630953/" target="_blank">PubMed</a></td>
        </tr>
        <tr>
            <td>In heart failure patients, daily yoga breathing exercise improved self-care, reduced fatigue and dyspnea.</td>
            <td><a href="https://pubmed.ncbi.nlm.nih.gov/39499816/" target="_blank">PubMed</a></td>
        </tr>
    </table>

    <h3 style="color:#004D40;">System Goals</h3>
    <ul>
        <li>Take regular guided breathing breaks using <code>breathing.sh</code></li>
        <li>Log readiness and track completed vs skipped sessions</li>
        <li>Visualize progress (minutes, frequency) over time with interactive dashboards</li>
    </ul>

    <h3 style="color:#004D40;">Hypothesis / Expected Benefits</h3>
    <p>
        Regular breathing practice is expected to:
    </p>
    <ul>
        <li>Reduce mental fatigue and improve mood</li>
        <li>Help prevent burnout</li>
        <li>Increase focus and productivity</li>
        <li>Support better sleep, stress resilience, and overall routine</li>
    </ul>

    <h3 style="color:#004D40;">Demonstration</h3>
    <p>Here is a short video demonstrating how my system works:</p>
    
<iframe width="560" height="315" src="https://www.youtube.com/embed/DwT-EoZOaeI?si=OvzWF930pGPIzwmH&amp;controls=0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</div>
"""


# --- Save to single HTML ---
with open("index.html", "w") as f:
    f.write("<h1>Triangle Breathing (10, 20, 10)  Dashboard</h1>\n")
    f.write(motivation_html)
    f.write(fig_minutes.to_html(full_html=False, include_plotlyjs='cdn'))
    f.write(fig_sessions.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_cum_minutes.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_cum_sessions.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_hist_minutes.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_hist_sessions.to_html(full_html=False, include_plotlyjs=False))
    f.write(table.to_html(full_html=False, include_plotlyjs=False))

print("index.html generated successfully with aggregated daily data!")
