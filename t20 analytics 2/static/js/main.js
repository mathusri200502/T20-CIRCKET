async function loadTeamPage() {
  const res = await fetch(`/api/team/${encodeURIComponent(TEAM)}`);
  const players = await res.json();
  
  const grid = document.querySelector('.player-grid');
  grid.innerHTML = ''; // Clear existing content
  
  players.forEach(p => {
    const card = document.createElement('div');
    card.className = 'player-card';
    
    // Create image name from player name
    const imgName = p.name.toLowerCase().replace(/[^a-z0-9]+/g,'_');
    
    card.innerHTML = `
      <img src="/static/images/${imgName}.jpg" alt="${p.name}" onerror="this.src='/static/images/placeholder.svg'">
      <div class="info">
        <h3>${p.name}</h3>
        <div class="role">${p.playingRole || 'Player'} | ${p.battingStyle || ''}</div>
        <div class="stats">
          <div class="stat">
            <div class="value">${p.runs || 0}</div>
            <div class="label">Runs</div>
          </div>
          <div class="stat">
            <div class="value">${p.wickets || 0}</div>
            <div class="label">Wickets</div>
          </div>
          <div class="stat">
            <div class="value">${p.bat_avg || 0}</div>
            <div class="label">Bat Avg</div>
          </div>
          <div class="stat">
            <div class="value">${p.economy || 0}</div>
            <div class="label">Economy</div>
          </div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
  
  // Create team summary charts
  const names = players.map(p => p.name);
  const runs = players.map(p => p.runs || 0);
  const wickets = players.map(p => p.wickets || 0);
  const averages = players.map(p => p.bat_avg || 0);
  
  try {
    new Chart(document.getElementById('teamRunsChart'), {
      type: 'bar',
      data: { labels: names, datasets: [{ label: 'Runs', data: runs }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
    
    new Chart(document.getElementById('teamWicketsChart'), {
      type: 'bar',
      data: { labels: names, datasets: [{ label: 'Wickets', data: wickets }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
    
    new Chart(document.getElementById('teamAvgChart'), {
      type: 'line',
      data: { labels: names, datasets: [{ label: 'Batting Average', data: averages, fill: true }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  } catch(err) {
    console.error('Error creating team charts:', err);
  }
}

document.addEventListener('DOMContentLoaded', ()=>{
  // card navigation animate
  document.querySelectorAll('.card').forEach(c=>{
    c.onclick = () => {
      const cat = c.dataset.cat;
      // animated page transition using simple fade
      document.body.style.opacity = 0.3;
      setTimeout(()=> window.location.href = `/category/${cat}`, 220);
    };
  });

  // If category page: load players
  if (typeof CATEGORY !== 'undefined') {
    if (CATEGORY === 'fast'){
      loadFastCategory(CATEGORY);
    } else {
      loadCategory(CATEGORY);
    }
  }

  // hover popup logic


  function setupPlayerHoverPopup() {
    const hover = document.getElementById('player-hover');
    let lastTarget = null;
    // Use event delegation for dynamic elements
    document.body.addEventListener('mouseenter', async (e) => {
      const el = e.target.closest('[data-player-name]');
      if (el) {
        lastTarget = el;
        const name = el.dataset.playerName;
        if (!window._playersCache) {
          window._playersCache = fetch('/api/players').then(r=>r.json());
        }
        const players = await window._playersCache;
        const p = players.find(x=>x.name===name);
        if (p) {
          document.getElementById('player-info').innerHTML = `
            <div style="font-weight:700;font-size:1.1em;color:#e4007a;">${p.name}</div>
            <div style="color:#5a00b8;">${p.team}</div>
            <div style="color:#00bfae;">${p.playingRole||''}</div>
            <div style="margin-top:0.3em;font-size:0.95em;">Runs: <b>${p.runs}</b> | SR: <b>${p.strike_rate}</b> | Avg: <b>${p.bat_avg}</b></div>
          `;
          const img = `/static/images/${name.toLowerCase().replace(/[^a-z0-9]+/g,'_')}.jpg`;
          document.getElementById('player-photo').src = img;
          hover.classList.remove('hidden');
          // position near mouse, but keep within viewport
          let x = e.clientX + 16;
          let y = e.clientY + 16;
          setTimeout(()=>{
            const rect = hover.getBoundingClientRect();
            if (x + rect.width > window.innerWidth) x = window.innerWidth - rect.width - 8;
            if (y + rect.height > window.innerHeight) y = window.innerHeight - rect.height - 8;
            hover.style.left = x + 'px';
            hover.style.top = y + 'px';
          }, 0);
        }
      }
    }, true);
    document.body.addEventListener('mouseleave', (e) => {
      const el = e.target.closest('[data-player-name]');
      if (el) {
        hover.classList.add('hidden');
      }
    }, true);
    // Hide popup if mouse leaves popup itself (edge case)
    hover.addEventListener('mouseleave', () => {
      hover.classList.add('hidden');
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setupPlayerHoverPopup();
    // ...existing code...
  });

});

async function loadCategory(cat){
  const title = document.getElementById('cat-title');
  title.innerText = title.innerText.replace('{{ category }}', cat);
  const res = await fetch(`/api/category/${cat}`);
  const arr = await res.json();
  const tbody = document.querySelector('#players-table tbody');
  tbody.innerHTML = '';
  const names = [], runs = [], avg = [], sr = [], bf = [], bndry = [];
  arr.forEach(p=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td data-player-name="${p.name}">${p.name}</td><td>${p.team||''}</td><td>${p.battingStyle||''}</td>
      <td>${p.innings||0}</td><td>${p.runs||0}</td><td>${p.balls||0}</td><td>${p.strike_rate||0}</td><td>${p.bat_avg||0}</td><td>${p.batting_position||''}</td><td>${p.boundary_pct||0}</td>`;
    // make name cell show hover
    tr.querySelector('td').setAttribute('data-player-name', p.name);
    tbody.appendChild(tr);
    names.push(p.name);
    runs.push(p.runs||0);
    avg.push(p.bat_avg||0);
    sr.push(p.strike_rate||0);
    bf.push(p.avg_ball_faced||0);
    bndry.push(p.boundary_pct||0);
  });

  // create charts with Chart.js
  // barRuns
  try{
    new Chart(document.getElementById('barRuns'), {
      type: 'bar',
      data: { labels: names, datasets: [{ label:'Runs', data: runs }]},
      options:{responsive:true, maintainAspectRatio:false}
    });
  }catch(err){
    fetch('/api/log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({what:'chart_error', chart:'barRuns', err:err && err.message})});
    document.getElementById('barRuns').insertAdjacentHTML('afterend','<div class="chart-error">Unable to render charts in this browser.</div>');
  }
  // areaAvg
  try{
    new Chart(document.getElementById('areaAvg'), {
      type: 'line',
      data: {labels:names, datasets:[{label:'Bat Avg', data:avg, fill:true}]},
      options:{elements:{point:{radius:3}}, maintainAspectRatio:false}
    });
  }catch(err){
    fetch('/api/log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({what:'chart_error', chart:'areaAvg', err:err && err.message})});
  }
  // areaSR
  try{
    new Chart(document.getElementById('areaSR'), {
      type:'line', data:{labels:names, datasets:[{label:'SR', data:sr, fill:true}]}, options:{maintainAspectRatio:false}
    });
  }catch(err){
    fetch('/api/log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({what:'chart_error', chart:'areaSR', err:err && err.message})});
  }
  // areaBF
  try{
    new Chart(document.getElementById('areaBF'), {
      type:'line', data:{labels:names, datasets:[{label:'Avg Balls Faced', data:bf, fill:true}]}, options:{maintainAspectRatio:false}
    });
  }catch(err){
    fetch('/api/log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({what:'chart_error', chart:'areaBF', err:err && err.message})});
  }
  // scatterAvgSR
  try{
    new Chart(document.getElementById('scatterAvgSR'), {
      type:'scatter',
      data:{datasets:[{label:'Avg vs SR', data:names.map((nm,i)=>({x:avg[i], y:sr[i], r:6}))}]},
      options:{scales:{x:{title:{display:true,text:'Bat Avg'}}, y:{title:{display:true,text:'SR'}}}, maintainAspectRatio:false}
    });
  }catch(err){
    fetch('/api/log', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({what:'chart_error', chart:'scatterAvgSR', err:err && err.message})});
  }
}

async function loadFastCategory(cat){
  const title = document.getElementById('cat-title');
  title.innerText = title.innerText.replace('{{ category }}', cat);
  const res = await fetch(`/api/category/${cat}`);
  const arr = await res.json();
  const tbody = document.querySelector('#fast-players-table tbody');
  tbody.innerHTML = '';
  const names = [], wickets = [], bowling_avg = [], dotballs = [], econ = [], bsr = [], innings = [], balls = [], maidens = [];
  arr.forEach(p=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td data-player-name="${p.name}">${p.name}</td><td>${p.team||''}</td><td>${p.bowlingStyle||''}</td><td>${p.runs_conceded||0}</td><td>${p.innings_bowled||0}</td><td>${p.balls_bowled||0}</td><td>${p.wickets||0}</td><td>${p.economy||0}</td><td>${p.bowling_sr||0}</td><td>${p.dot_balls||0}</td><td>${p.maiden||0}</td>`;
    tr.querySelector('td').setAttribute('data-player-name', p.name);
    tbody.appendChild(tr);
    names.push(p.name);
    wickets.push(p.wickets||0);
    bowling_avg.push(p.bowling_avg||0);
    dotballs.push(p.dot_balls||0);
    econ.push(p.economy||0);
    bsr.push(p.bowling_sr||0);
    innings.push(p.innings_bowled||0);
    balls.push(p.balls_bowled||0);
    maidens.push(p.maiden||0);
  });

  try{ new Chart(document.getElementById('barWickets'), {type:'bar', data:{labels:names,datasets:[{label:'Wickets',data:wickets}]}, options:{responsive:true,maintainAspectRatio:false}});}catch(e){fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({what:'chart_error',chart:'barWickets',err:e&&e.message})});}
  try{ new Chart(document.getElementById('areaBowlingAvg'), {type:'line', data:{labels:names,datasets:[{label:'Bowling Avg',data:bowling_avg,fill:true}]}, options:{maintainAspectRatio:false}});}catch(e){fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({what:'chart_error',chart:'areaBowlingAvg',err:e&&e.message})});}
  try{ new Chart(document.getElementById('areaDotBalls'), {type:'line', data:{labels:names,datasets:[{label:'Dot Balls',data:dotballs,fill:true}]}, options:{maintainAspectRatio:false}});}catch(e){fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({what:'chart_error',chart:'areaDotBalls',err:e&&e.message})});}
  try{ new Chart(document.getElementById('areaEconomy'), {type:'line', data:{labels:names,datasets:[{label:'Economy',data:econ,fill:true}]}, options:{maintainAspectRatio:false}});}catch(e){fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({what:'chart_error',chart:'areaEconomy',err:e&&e.message})});}
  try{ new Chart(document.getElementById('areaBowlingSR'), {type:'line', data:{labels:names,datasets:[{label:'Bowling SR',data:bsr,fill:true}]}, options:{maintainAspectRatio:false}});}catch(e){fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({what:'chart_error',chart:'areaBowlingSR',err:e&&e.message})});}
  try{ new Chart(document.getElementById('scatterSRvsEconomy'), {type:'scatter', data:{datasets:[{label:'SR vs Econ', data:names.map((nm,i)=>({x:bsr[i], y:econ[i], r:6}))}]}, options:{scales:{x:{title:{display:true,text:'Bowling SR'}}, y:{title:{display:true,text:'Economy'}}}, maintainAspectRatio:false}});}catch(e){fetch('/api/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({what:'chart_error',chart:'scatterSRvsEconomy',err:e&&e.message})});}
}
