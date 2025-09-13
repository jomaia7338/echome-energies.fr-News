// assets/tarifs.js
(function(){
  function detectRoot(){
    try{
      const s = document.currentScript?.src || '';
      const u = new URL(s, location.href);
      return u.pathname.replace(/assets\/tarifs\.js.*$/,'');
    }catch(e){
      const p = location.pathname.split('/').filter(Boolean);
      return p.length ? '/' + p[0] + '/' : '/';
    }
  }

  // Valeurs de secours si fetch échoue
  const FALLBACK = {
    version: "T3-2025",
    last_updated: new Date().toISOString().slice(0,10),
    edf_oa_surplus: [
      {range:"≤ 9 kWc",   segment:"particuliers",  eur_per_kwh:0.0400, example_surplus_kwh:1000},
      {range:"9–36 kWc",  segment:"petites pros", eur_per_kwh:0.0400, example_surplus_kwh:5000},
      {range:"36–100 kWc",segment:"PME/PMI",      eur_per_kwh:0.0886, example_surplus_kwh:20000}
    ],
    avg_autoconsommation_value_ttc_eur_per_kwh: 0.25
  };

  async function loadTarifs(){
    const root = detectRoot();
    const url = root + 'data/tarifs.json?t=' + Date.now();
    let data;
    try{
      const res = await fetch(url,{cache:'no-store'});
      if(!res.ok) throw new Error('HTTP '+res.status);
      data = await res.json();
    }catch(e){
      console.error('Chargement tarifs.json échoué → fallback', e);
      data = FALLBACK;
      const meta = document.querySelector('#tarifs-meta');
      if(meta){ meta.textContent = '⚠️ Données locales (fallback) — vérifiez /data/tarifs.json'; }
    }

    const body = document.querySelector('#tarifs-table-body');
    const caption = document.querySelector('#tarifs-caption');
    const meta   = document.querySelector('#tarifs-meta');
    if(!body) return;

    body.innerHTML = '';
    for(const row of data.edf_oa_surplus){
      const euros = Number(row.eur_per_kwh||0);
      const exkwh = Number(row.example_surplus_kwh||0);
      body.insertAdjacentHTML('beforeend', `
        <tr>
          <th scope="row">${row.range} (${row.segment})</th>
          <td><strong>${euros.toFixed(4).replace('.', ',')}</strong></td>
          <td>Surplus ${exkwh.toLocaleString('fr-FR')} kWh → 
              <strong>${(exkwh*euros).toLocaleString('fr-FR',{style:'currency',currency:'EUR'})}</strong>/an</td>
        </tr>
      `);
    }

    if(caption){
      caption.textContent = `Tarifs de rachat (EDF OA) — Surplus (${data.version||'à jour'})`;
    }
    if(meta){
      meta.textContent = `✅ Données à jour — ${new Date(data.last_updated||Date.now()).toLocaleDateString('fr-FR')}`;
    }

    const kpi = document.querySelector('#kpi-autoconso-value');
    if(kpi && data.avg_autoconsommation_value_ttc_eur_per_kwh){
      kpi.innerHTML = `💡 Un kWh autoconsommé vaut ~<strong>${Number(data.avg_autoconsommation_value_ttc_eur_per_kwh).toFixed(2).replace('.', ',')} €/kWh TTC</strong>`;
    }
  }
  document.addEventListener('DOMContentLoaded', loadTarifs);
})();
