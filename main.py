import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ===============================
# Load Data
# ===============================
conn = sqlite3.connect("breathing_log.db")
raw = pd.read_sql("SELECT * FROM daily_breathing;", conn)
conn.close()
raw['date'] = pd.to_datetime(raw['date'])

# ===============================
# Aggregate per day
# ===============================
daily = raw.groupby(raw['date'].dt.date).agg(
    total_minutes=('total_minutes', 'sum'),
    sessions=('sessions', 'sum')
).reset_index()

# Fill missing days with zeros
all_dates = pd.date_range(daily['date'].min(), daily['date'].max())
daily = daily.set_index('date').reindex(all_dates, fill_value=0)\
             .rename_axis('date').reset_index()
daily['date_str'] = daily['date'].astype(str)

# Cumulative sums
daily['cumulative_minutes'] = daily['total_minutes'].cumsum()
daily['cumulative_sessions'] = daily['sessions'].cumsum()

# Moving average (3-day window)
daily['minutes_ma'] = daily['total_minutes'].rolling(3, min_periods=1).mean()
daily['sessions_ma'] = daily['sessions'].rolling(3, min_periods=1).mean()

# ===============================
# Basic Stats
# ===============================
mean_minutes = daily['total_minutes'].mean()
median_minutes = daily['total_minutes'].median()
mean_sessions = daily['sessions'].mean()
median_sessions = daily['sessions'].median()

# ===============================
# Shared Layout
# ===============================
shared_layout = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",  
    plot_bgcolor="rgba(0,0,0,0)",    
    font=dict(color="#E6EDF3", family="Helvetica Neue, Segoe UI"),
    title_font=dict(size=18, color="#9CD1FF"),
    margin=dict(l=60, r=30, t=60, b=60)
)
# ===============================
# Daily Minutes & MA
# ===============================
fig_minutes = go.Figure()
fig_minutes.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['total_minutes'],
    mode='lines+markers', name='Daily Minutes',
    line=dict(color='skyblue')
))
fig_minutes.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['minutes_ma'],
    mode='lines', name='3-Day MA',
    line=dict(color='darkblue', dash='dash')
))
fig_minutes.update_layout(title="Daily Breathing Minutes", **shared_layout)

# Daily Sessions & MA
fig_sessions = go.Figure()
fig_sessions.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['sessions'],
    mode='lines+markers', name='Daily Sessions',
    line=dict(color='lightgreen')
))
fig_sessions.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['sessions_ma'],
    mode='lines', name='3-Day MA',
    line=dict(color='green', dash='dash')
))
fig_sessions.update_layout(title="Daily Breathing Sessions", **shared_layout)

# ===============================
# Cumulative Figures
# ===============================
fig_cum_minutes = go.Figure(go.Scatter(
    x=daily['date_str'], y=daily['cumulative_minutes'],
    mode='lines+markers', name='Cumulative Minutes',
    line=dict(color='darkblue')
))
fig_cum_minutes.update_layout(title="Cumulative Minutes", **shared_layout)

fig_cum_sessions = go.Figure(go.Scatter(
    x=daily['date_str'], y=daily['cumulative_sessions'],
    mode='lines+markers', name='Cumulative Sessions',
    line=dict(color='green')
))
fig_cum_sessions.update_layout(title="Cumulative Sessions", **shared_layout)

# ===============================
# Histograms
# ===============================
# --- Histogram of Minutes ---
# --- Calculate bins using Sturges' formula ---

n_minutes = len(daily['total_minutes'])
bins_minutes = int(np.ceil(np.log2(n_minutes) + 1))

counts, bins = np.histogram(daily['total_minutes'], bins=bins_minutes)
bin_centers = 0.5 * (bins[:-1] + bins[1:])
text_labels = [str(int(v)) if v > 0 else "" for v in counts]

fig_hist_minutes = go.Figure(go.Bar(
    x=bin_centers,
    y=counts,
    text=text_labels,
    textposition='outside',
    textfont=dict(size=16, color='#E6EDF3'),
    marker_color='skyblue'
))

fig_hist_minutes.update_layout(
    title="Distribution of Daily Minutes",
    showlegend=False,
    xaxis=dict(title='Minutes', showticklabels=True),
    yaxis=dict(visible=False),
    **shared_layout
)

# --- Sessions ---
n_sessions = len(daily['sessions'])
bins_sessions = int(np.ceil(np.log2(n_sessions) + 1))

counts_s, bins_s = np.histogram(daily['sessions'], bins=bins_sessions)
bin_centers_s = 0.5 * (bins_s[:-1] + bins_s[1:])
text_labels_s = [str(int(v)) if v > 0 else "" for v in counts_s]

fig_hist_sessions = go.Figure(go.Bar(
    x=bin_centers_s,
    y=counts_s,
    text=text_labels_s,
    textposition='outside',
    textfont=dict(size=16, color='#E6EDF3'),
    marker_color='lightgreen'
))

fig_hist_sessions.update_layout(
    title="Distribution of Daily Sessions",
    showlegend=False,
    xaxis=dict(title='Sessions', showticklabels=True),
    yaxis=dict(visible=False),
    **shared_layout
)

# ===============================
# Weekday Aggregation
# ===============================
weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

weekday_minutes = raw.groupby('weekday')['total_minutes'].sum().reindex(weekday_order, fill_value=0)
weekday_sessions = raw.groupby('weekday')['sessions'].sum().reindex(weekday_order, fill_value=0)

fig_weekday_minutes = go.Figure(go.Bar(
    x=weekday_minutes.index, y=weekday_minutes.values,
    text=[f"{v:.2f}" for v in weekday_minutes.values],
    textposition='outside',
    marker_color='skyblue'
))

fig_weekday_minutes.update_traces(
    textfont=dict(size=16, color='white')  
)
fig_weekday_minutes.update_layout(title="Breathing Minutes per Day of Week", **shared_layout)
fig_weekday_minutes.update_yaxes(visible = False, showticklabels=False, showgrid=False, zeroline=False ,range=[0, max(weekday_minutes.values)*1.2])

fig_weekday_sessions = go.Figure(go.Bar(
    x=weekday_sessions.index, y=weekday_sessions.values,
    text=weekday_sessions.values, textposition='outside',
    marker_color='lightgreen'
))

fig_weekday_sessions.update_traces(
    textfont=dict(size=16, color='white')  
)
fig_weekday_sessions.update_layout(title="Breathing Sessions per Day of Week", **shared_layout)
fig_weekday_sessions.update_yaxes(visible = False, showticklabels=False, showgrid=False, zeroline=False , range=[0, max(weekday_sessions.values)*1.2])

# ===============================
# Stats Table
# ===============================
table = go.Figure(data=[go.Table(
    header=dict(values=["Metric", "Minutes", "Sessions"],
                fill_color='paleturquoise', align='left'),
    cells=dict(values=[
        ["Mean", "Median"],
        [f"{mean_minutes:.2f}", f"{median_minutes:.2f}"],
        [f"{mean_sessions:.2f}", f"{median_sessions:.2f}"]
    ], fill_color='lavender', align='left')
)])
table.update_layout(**shared_layout)

# ===============================
# Dual-axis chart: Minutes & Sessions
# ===============================
fig_minutes_sessions = go.Figure()
fig_minutes_sessions.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['total_minutes'],
    mode='lines+markers', name='Minutes', line=dict(color='skyblue')
))
fig_minutes_sessions.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['sessions'],
    mode='lines+markers', name='Sessions', line=dict(color='lightgreen'),
    yaxis='y2'
))
fig_minutes_sessions.update_layout(
    title="Daily Breathing: Minutes & Sessions",
    xaxis=dict(title="Date", showgrid=False, zeroline=False),
    yaxis=dict(title="Minutes", color='skyblue', showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
    yaxis2=dict(title="Sessions", overlaying='y', side='right', color='lightgreen', showgrid=False),
    height=500,
    **shared_layout
)

# ===============================
# Streak Computation
# ===============================
streaks = []
current_streak = 0
for minutes in daily['total_minutes']:
    if minutes > 0:
        current_streak += 1
    else:
        current_streak = 0
    streaks.append(current_streak)
daily['streak'] = streaks

fig_streak = go.Figure()
fig_streak.add_trace(go.Scatter(
    x=daily['date_str'], y=daily['streak'],
    mode='lines+markers', name='Streak (days)',
    line=dict(color='orange', width=3), marker=dict(size=6)
))
fig_streak.update_layout(title="Current Streak of Daily Practice", **shared_layout)

# ===============================
# Participation KPI
# ===============================
days_practiced = (daily['total_minutes'] > 0).sum()
total_days = len(daily)
participation_pct = (days_practiced / total_days) * 100


# tools = """   
#     <h3 style="color:#004D40;">Tools</h3>
#     <ul>
#     <li><strong>Python</strong> — data processing, visualization (Plotly)</li>
#     <li><strong>SQLite</strong> — lightweight database for logging sessions</li>
#     <li><strong>Bash</strong> — automation and terminal-based prompts</li>
#     <li><strong>HTML/CSS</strong> — dashboard layout</li>
#     </ul> 
#     """

note_text = """
<p><strong>Note:</strong> I created this system mainly because I don't want the hassle of logging my sessions in a spreadsheet. 
The only task is to respond "1" in the terminal, which triggers an alert—it helps me break hyperfocus. 
I plan to continue this practice for years and eventually correlate it with subjective factors, professional performance, and personal growth. 
I also intend to maintain a personal notebook about my life, projects, feelings, tasks to do, and what has been accomplished. 
After many months of practice, it will be possible to perform textual analysis, sentiment analysis, and evaluate achievements based on this routine.</p>
"""

# --- Save to single HTML dashboard ---
# Calcule KPIs
days_practiced = (daily['total_minutes'] > 0).sum()
total_days = len(daily)
participation_pct = days_practiced / total_days * 100

with open("journey.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Triangle Breathing Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(145deg, #0f172a, #1e1b4b);
      color: #E6EDF3;
      font-family: 'Inter', 'Segoe UI', sans-serif;
      margin: 0;
      padding: 0;
    }
    h1, h2, h3 {
      color: #A5B4FC;
    }
    .card {
      background: #1e293b;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.25);
      transition: transform 0.2s ease;
    }
    .card:hover {
      transform: translateY(-3px);
    }
  </style>
</head>
<body class="min-h-screen flex flex-col">
""")

with open("journey.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Triangle Breathing Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <style>
    /* ------------------------------------------- */
    /* NOVO CSS: Transferido de 'evidence.html' */
    /* ------------------------------------------- */
    body {
      margin: 0;
      min-height: 100vh; 
      /* Fundo de espaço profundo com gradiente */
      background: radial-gradient(circle at center, #1f1842 0%, #0d0a1f 100%);
      font-family: 'Poppins', sans-serif;
      color: #E6EDF3;
      /* Permite rolagem vertical do conteúdo */
      overflow-y: scroll; 
    }

    /* ESTILOS DAS PARTÍCULAS */
    .particle {
      position: absolute;
      background: #FFFFFF; 
      border-radius: 50%;
      opacity: 0.7; 
      animation: float 15s linear infinite, twinkle 2s alternate infinite; 
    }

    @keyframes float {
      0% { transform: translateY(0) scale(0.9); opacity: 0.7; }
      50% { transform: translateY(-50px) scale(1.1); opacity: 1; }
      100% { transform: translateY(0) scale(0.9); opacity: 0.7; }
    }
    
    @keyframes twinkle {
      0% { opacity: 0.5; }
      100% { opacity: 1; }
    }
    
    /* ESTILOS DOS CARDS DO DASHBOARD (Ajustados ao novo fundo) */
    h1, h2, h3 {
      color: #A5B4FC;
    }
    .card {
      /* Fundo semi-transparente para o universo */
      background: rgba(24, 18, 50, 0.9); 
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.25);
      transition: transform 0.2s ease;
      overflow: hidden; /* Mantém a correção para gráficos */
    }
    .card:hover {
      transform: translateY(-3px);
    }
  </style>
</head>
<body class="min-h-screen"> 
""")
    f.write("""
<div class="particle" style="top:5%; left:90%; width:1px; height:1px; animation-delay:0s;"></div>
<div class="particle" style="top:95%; left:10%; width:2px; height:2px; animation-delay:1.5s;"></div>
<div class="particle" style="top:40%; left:30%; width:1px; height:1px; animation-delay:3s;"></div>
""")

   
    f.write("""
<header class="text-center py-10">
    <h1 class="text-4xl font-bold mb-2">My Breathing Journey</h1>
</header>

""")


    # ====== KPI Panel ======
    f.write(f"""
  <section class="flex flex-wrap justify-center gap-6 px-6 mb-12">
    <div class="card w-44 text-center">
      <h2 class="text-lg font-semibold">Mean Minutes</h2>
      <p class="text-3xl font-bold mt-2">{mean_minutes:.1f}</p>
    </div>
    <div class="card w-44 text-center">
      <h2 class="text-lg font-semibold">Mean Sessions</h2>
      <p class="text-3xl font-bold mt-2">{mean_sessions:.1f}</p>
    </div>
    <div class="card w-44 text-center">
      <h2 class="text-lg font-semibold">Days Practiced</h2>
      <p class="text-3xl font-bold mt-2">{days_practiced}</p>
    </div>
    <div class="card w-44 text-center">
      <h2 class="text-lg font-semibold">Participation %</h2>
      <p class="text-3xl font-bold mt-2">{participation_pct:.1f}%</p>
    </div>
  </section>
""")

    # ======  ======
    figs = [
        (fig_minutes, "Breathing Daily Minutes"),
        (fig_sessions, "Breathing Daily Sessions"),
        (fig_cum_minutes, "Cumulative Minutes"),
        (fig_cum_sessions, "Cumulative Sessions"),
        (fig_hist_minutes, "Distribution of Daily Minutes"),
        (fig_hist_sessions, "Distribution of Daily Sessions"),
        (fig_weekday_minutes, "Minutes per Weekday"),
        (fig_weekday_sessions, "Sessions per Weekday"),
        (fig_streak, "Practice Streak")
    ]

    f.write('<section class="grid grid-cols-1 md:grid-cols-2 gap-10 px-8 mb-16">\n')
    first = True

    shared_layout = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        font=dict(color="#E6EDF3", family="Inter, Segoe UI"),
        title_font=dict(size=18, color="#A5B4FC"),
        xaxis=dict(showgrid=False, zeroline=False, fixedrange=True),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", fixedrange=True),
        margin=dict(l=50, r=30, t=60, b=60), 
        title = None
    )

    for fig, title in figs:
        fig.update_layout(height=480, **shared_layout)
        f.write('<div class="card">\n')
        f.write(f'<h3 class="text-center text-xl font-semibold mb-4">{title}</h3>\n')
        f.write(fig.to_html(full_html=False, include_plotlyjs="cdn" if first else False))
        f.write('</div>\n')
        first = False

    f.write('</section>\n')

    # ====== Table & Notes ======
    f.write(f"""
  <footer class="text-center text-gray-400 text-sm py-6 border-t border-gray-700 mt-auto">
    {note_text}
  </footer>
</body>
</html>
""")

print( " html generated successfully with Calm Flat Layout + Motivation + Tools + KPIs + Charts + Notes!")
