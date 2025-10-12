import sqlite3

import pandas as pd
import plotly.graph_objects as go

# --- Load data ---
conn = sqlite3.connect("breathing_log.db")
raw = pd.read_sql("SELECT * FROM daily_breathing;", conn)
conn.close()

# --- Aggregate per day ---
raw['date'] = pd.to_datetime(raw['date'])

# --- Fill missing days with 0 ---

daily = raw.groupby(raw['date'].dt.date).agg(
    total_minutes=('total_minutes', 'sum'),
    sessions=('sessions', 'sum')
).reset_index()

all_dates = pd.date_range(daily['date'].min(), daily['date'].max())
daily = daily.set_index('date').reindex(
    all_dates, fill_value=0).rename_axis('date').reset_index()

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

# Distribution/week day
weekday_order = ['Monday', 'Tuesday', 'Wednesday',
                 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Agrupa minutos e sessões por weekday
weekday_minutes = raw.groupby('weekday')['total_minutes'].sum().reindex(
    weekday_order, fill_value=0)
weekday_sessions = raw.groupby('weekday')['sessions'].sum().reindex(
    weekday_order, fill_value=0)

fig_weekday_minutes = go.Figure(go.Bar(
    x=weekday_minutes.index,
    y=weekday_minutes.values,
    text=weekday_minutes.values,
    textposition='outside',
    marker_color='skyblue'
))
fig_weekday_minutes.update_layout(
    title="Breathing Minutes per Day of Week",
    xaxis_title="Day of Week",
    yaxis_title="Total Minutes",
    yaxis=dict(range=[0, max(weekday_minutes.values)*1.2])
)

fig_weekday_sessions = go.Figure(go.Bar(
    x=weekday_sessions.index,
    y=weekday_sessions.values,
    text=weekday_sessions.values,
    textposition='outside',
    marker_color='lightgreen'
))
fig_weekday_sessions.update_layout(
    title="Breathing Sessions per Day of Week",
    xaxis_title="Day of Week",
    yaxis_title="Total Sessions",
    yaxis=dict(range=[0, max(weekday_sessions.values)*1.2])
)

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

shared_layout = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(18, 12, 35, 1)",
    plot_bgcolor="rgba(18, 12, 35, 1)",
    font=dict(color="#E6EDF3", family="Helvetica Neue, Segoe UI"),
    title_font=dict(size=18, color="#9CD1FF"),
    xaxis=dict(showgrid=False, zeroline=False, fixedrange=True),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)",
               fixedrange=True),
    margin=dict(l=60, r=30, t=60, b=60)
)

for fig in [
    fig_minutes, fig_sessions, fig_cum_minutes, fig_cum_sessions,
    fig_hist_minutes, fig_hist_sessions, fig_weekday_minutes, fig_weekday_sessions
]:
    fig.update_layout(**shared_layout)


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
    
    <iframe width="560" height="315" src="https://www.youtube.com/embed/DwT-EoZOaeI?si=OvzWF930pGPIzwmH&amp;controls=0" 
            title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
            referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


</div>
"""

note_text = """
<p><strong>Note:</strong> I created this system mainly because I don't want the hassle of logging my sessions in a spreadsheet. 
The only task is to respond "1" in the terminal, which triggers an alert—it helps me break hyperfocus. 
I plan to continue this practice for years and eventually correlate it with subjective factors, professional performance, and personal growth. 
I also intend to maintain a personal notebook about my life, projects, feelings, tasks to do, and what has been accomplished. 
After many months of practice, it will be possible to perform textual analysis, sentiment analysis, and evaluate achievements based on this routine.</p>
"""

tools = """   
    <h3 style="color:#004D40;">Tools</h3>
    <ul>
    <li><strong>Python</strong> — data processing, visualization (Plotly)</li>
    <li><strong>SQLite</strong> — lightweight database for logging sessions</li>
    <li><strong>Bash</strong> — automation and terminal-based prompts</li>
    <li><strong>HTML/CSS</strong> — dashboard layout</li>
    </ul> 
    """

triangle_html = """
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;margin:40px 0;">
  <svg id="triangleSVG" width="500" height="400" viewBox="0 0 500 400">
    <!-- Triangle and particle will be created via JS -->
  </svg>
  <h3 id="breathText">Breathe...</h3>
  <div id="countdown">Time left: 0s</div>
  <div id="rounds">Rounds: 0</div>
  <div id="minutes">Total minutes: 0</div>
</div>

<audio id="bellAudio">
  <source src="tibetan_bell.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>

<audio id="backgroundAudio" loop>
  <source src="meditation_music.wav" type="audio/wav">
  Your browser does not support the audio element.
</audio>

<script>
const svg = document.getElementById("triangleSVG");
const textEl = document.getElementById("breathText");
const countdownEl = document.getElementById("countdown");
const roundsEl = document.getElementById("rounds");
const minutesEl = document.getElementById("minutes");
const bellAudio = document.getElementById("bellAudio");
const bgAudio = document.getElementById("backgroundAudio");
document.addEventListener("click", () => {
    if(bgAudio.paused){
        bgAudio.volume = 0.5;
        bgAudio.play().catch(e => console.log("Audio play blocked:", e));
    }
}, {once: true});


// ========== PARAMETERS ==========
const baseWidth = 300;
const height = 250;
const particleRadius = 15;
const strokeColor = "#00d4ff";

const inhaleTime = 10000;
const holdTime = 20000;
const exhaleTime = 10000;

const playBellAtVertex = true;

// ========== CALCULATE POINTS ==========
const centerX = 250;
const topLeft = {x: centerX - baseWidth/2, y:100};
const topRight = {x: centerX + baseWidth/2, y:100};
const bottom = {x: centerX, y: 100 + height};

const vertices = [bottom, topLeft, topRight];
const tolerance = 2

// Create triangle
const triangle = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
triangle.setAttribute("points", `${topLeft.x},${topLeft.y} ${topRight.x},${topRight.y} ${bottom.x},${bottom.y}`);
triangle.setAttribute("fill", "none");
triangle.setAttribute("stroke", strokeColor);
triangle.setAttribute("stroke-width", 5);
svg.appendChild(triangle);

// Create particle
const particle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
particle.setAttribute("cx", bottom.x);
particle.setAttribute("cy", bottom.y);
particle.setAttribute("r", particleRadius);
particle.setAttribute("fill", strokeColor);
svg.appendChild(particle);

// ========== PHASES ==========
const phases = [
  {text:"Inhale", duration:inhaleTime, start:bottom, end:topLeft},
  {text:"Hold", duration:holdTime, start:topLeft, end:topRight},
  {text:"Exhale", duration:exhaleTime, start:topRight, end:bottom},
];

let idx = 0;
let rounds = 0;
let totalSeconds = 0;

let vertexFlags = {};
vertices.forEach((v,i) => vertexFlags[i] = false);

function animatePhase() {
  const phase = phases[idx];
  textEl.innerText = phase.text;
  const startTime = performance.now();

  function step(now) {
    const t = Math.min((now - startTime)/phase.duration, 1);
    const cx = phase.start.x + (phase.end.x - phase.start.x) * t;
    const cy = phase.start.y + (phase.end.y - phase.start.y) * t;
    particle.setAttribute("cx", cx);
    particle.setAttribute("cy", cy);

    // Update countdown
    const secondsLeft = Math.ceil((phase.duration*(1-t))/1000);
    countdownEl.innerText = `Time left: ${secondsLeft}s`;

    vertices.forEach((v, i) => {

    if(Math.abs(cx - v.x) > tolerance || Math.abs(cy - v.y) > tolerance){
        vertexFlags[i] = false;
    }

    else if(!vertexFlags[i]){
        bellAudio.currentTime = 0;
        bellAudio.play().catch(e => console.log("Audio play blocked:", e));
        vertexFlags[i] = true;
    }
    });

    if(t < 1) requestAnimationFrame(step);
    else {
      idx = (idx + 1) % phases.length;
      if(idx === 0) rounds++;  // completed a full cycle
      totalSeconds += phase.duration/1000;
      roundsEl.innerText = `Rounds: ${rounds}`;
      minutesEl.innerText = `Total minutes: ${(totalSeconds/60).toFixed(1)}`;
      vertices.forEach((v,i) => vertexFlags[i] = false);

      animatePhase();
    }
  }

  requestAnimationFrame(step);
}

animatePhase();
</script>


"""

# --- Save to single HTML ---
with open("index_test.html", "w") as f:
    f.write('<h1 style="margin-top:30px;">Triangle Breathing (10, 20, 10)</h1>\n')
    f.write("""<p style="text-align:center; font-style:italic; color:gray;">
  Click anywhere to activate sound 🎵</p>""")
    f.write(triangle_html)
    f.write(motivation_html)
    f.write(tools)
    f.write(fig_minutes.to_html(full_html=False, include_plotlyjs='cdn'))
    f.write(fig_sessions.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_cum_minutes.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_cum_sessions.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_hist_minutes.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_hist_sessions.to_html(full_html=False, include_plotlyjs=False))
    f.write(fig_weekday_minutes.to_html(
        full_html=False, include_plotlyjs=False))
    f.write(fig_weekday_sessions.to_html(
        full_html=False, include_plotlyjs=False))
    f.write(table.to_html(full_html=False, include_plotlyjs=False))
    f.write(note_text)

print("index.html generated successfully with aggregated daily data!")
