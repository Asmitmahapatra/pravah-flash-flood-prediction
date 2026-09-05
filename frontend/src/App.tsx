import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import { Activity, AlertTriangle, BarChart3, Bell, CalendarDays, Check, ChevronRight, Clock3, CloudRain, Gauge, Layers3, LocateFixed, Menu, Radio, RefreshCw, Search, ShieldCheck, SlidersHorizontal, Waves, X } from 'lucide-react'
import type { FeatureCollection, Feature } from 'geojson'
import 'leaflet/dist/leaflet.css'
import './App.css'

type Tier = 'EMERGENCY' | 'WARNING' | 'ADVISORY' | 'NORMAL'
type Station = { gauge_id: string; station_name: string; river: string; basin: string; latitude: number; longitude: number; warning_level_m: number; danger_level_m: number }
type Prediction = { status: string; station: Station; alert_tier: { tier: Tier; color: string; recommendation: string }; task_a_onset: { model_used: string; probability: number; threshold: number; is_flood_onset_predicted: boolean }; task_b_active: { model_used: string; probability: number; threshold: number; is_active_flood_predicted: boolean }; antecedent_rainfall_summary: { rain_1d_mm: number; rain_3d_sum_mm: number; rain_7d_sum_mm: number; rain_10d_sum_mm: number } }
type Historical = { date: string; total_stations_active: number; emergency_count: number; warning_count: number; advisory_count: number; normal_count: number; catchments: Array<{ gauge_id: string; station_name: string; river: string; alert_tier: Tier; onset_probability: number; active_probability: number }> }
type AlertRecord = { id: string; tier: Tier; gaugeId: string; stationName: string; probability: number; activeProbability: number; recommendation: string; createdAt: string; acknowledged: boolean }
type ApiAlert = { id: string; tier: Tier; gauge_id: string; station_name: string; probability: number; active_probability: number; recommendation: string; created_at: string; acknowledged: boolean }
type ModelMetric = { roc_auc: number; threshold: number; precision: number; recall: number; f1: number }
type ModelSummary = { task_a_onset?: Record<string, ModelMetric>; task_b_active?: Record<string, ModelMetric> }
type NotificationStatus = { enabled: boolean; configured_channels: string[] }

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const tiers: Tier[] = ['EMERGENCY', 'WARNING', 'ADVISORY', 'NORMAL']
const tierClass: Record<Tier, string> = { EMERGENCY: 'emergency', WARNING: 'warning', ADVISORY: 'advisory', NORMAL: 'normal' }
const rainfallPresets: Record<string, number[]> = {
  'Moderate monsoon': [5, 8, 12, 14, 18, 25, 30, 40, 52, 68],
  'Heavy storm': [20, 35, 55, 80, 110, 130, 140, 115, 90, 105],
  'August 2019 deluge': [45, 85, 130, 190, 250, 280, 260, 210, 180, 220],
}

function MapViewport({ selected }: { selected: Station | undefined }) {
  const map = useMap()
  useEffect(() => { if (selected) map.flyTo([selected.latitude, selected.longitude], 10, { duration: 0.8 }) }, [map, selected])
  return null
}

function App() {
  const [stations, setStations] = useState<Station[]>([])
  const [geojson, setGeojson] = useState<FeatureCollection | null>(null)
  const [selectedGauge, setSelectedGauge] = useState('684')
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [historical, setHistorical] = useState<Historical | null>(null)
  const [rainfall, setRainfall] = useState(rainfallPresets['Moderate monsoon'])
  const [preset, setPreset] = useState('Moderate monsoon')
  const [onsetModel, setOnsetModel] = useState('RandomForest')
  const [activeModel, setActiveModel] = useState('XGBoost')
  const [view, setView] = useState<'live' | 'history' | 'models'>('live')
  const [historyDate, setHistoryDate] = useState('2019-08-05')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [forecastLoading, setForecastLoading] = useState(false)
  const [error, setError] = useState('')
  const [mobileNav, setMobileNav] = useState(false)
  const [alerts, setAlerts] = useState<AlertRecord[]>([])
  const [alertsOpen, setAlertsOpen] = useState(false)
  const [modelSummary, setModelSummary] = useState<ModelSummary>({})
  const [apiOnline, setApiOnline] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [notificationStatus, setNotificationStatus] = useState<NotificationStatus>({ enabled: false, configured_channels: [] })

  const selected = stations.find((station) => station.gauge_id === selectedGauge)
  const filteredStations = useMemo(() => stations.filter((station) => `${station.station_name} ${station.gauge_id} ${station.river} ${station.basin}`.toLowerCase().includes(query.toLowerCase())), [stations, query])

  useEffect(() => {
    const load = async () => {
      try {
        const [catchmentResponse, healthResponse, modelResponse, notificationResponse] = await Promise.all([fetch(`${API}/api/v1/catchments`), fetch(`${API}/health`), fetch(`${API}/api/v1/models/summary`), fetch(`${API}/api/v1/notifications/status` )])
        if (!catchmentResponse.ok) throw new Error('FastAPI service is not responding')
        const data = await catchmentResponse.json() as FeatureCollection
        setApiOnline(healthResponse.ok)
        if (modelResponse.ok) setModelSummary(await modelResponse.json() as ModelSummary)
        if (notificationResponse.ok) setNotificationStatus(await notificationResponse.json() as NotificationStatus)
        setGeojson(data)
        setStations((data.features ?? []).map((feature) => feature.properties as Station).sort((a, b) => a.gauge_id.localeCompare(b.gauge_id)))
        setLastRefresh(new Date())
      } catch (err) { setError(err instanceof Error ? err.message : 'Unable to reach the PRAVAH API') }
      finally { setLoading(false) }
    }
    void load()
  }, [])

  const runForecast = async () => {
    setForecastLoading(true); setError('')
    try {
      const response = await fetch(`${API}/api/v1/predict/live`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ gauge_id: selectedGauge, rainfall_history_10d: rainfall, onset_model: onsetModel, active_model: activeModel }) })
      if (!response.ok) throw new Error((await response.json()).detail ?? 'Forecast request failed')
      setPrediction(await response.json() as Prediction)
      await loadAlerts()
      setApiOnline(true)
      setLastRefresh(new Date())
    } catch (err) { setError(err instanceof Error ? err.message : 'Forecast failed') }
    finally { setForecastLoading(false) }
  }

  const runHistory = async () => {
    setForecastLoading(true); setError('')
    try {
      const response = await fetch(`${API}/api/v1/predict/historical/${historyDate}?onset_model=${onsetModel}&active_model=${activeModel}`)
      if (!response.ok) throw new Error((await response.json()).detail ?? 'Historical replay failed')
      setHistorical(await response.json() as Historical)
      setLastRefresh(new Date())
    } catch (err) { setError(err instanceof Error ? err.message : 'Historical replay failed') }
    finally { setForecastLoading(false) }
  }

  const loadAlerts = async () => {
    const response = await fetch(`${API}/api/v1/alerts`)
    if (!response.ok) return
    const records = await response.json() as ApiAlert[]
    setAlerts(records.map((alert) => ({ id: alert.id, tier: alert.tier, gaugeId: alert.gauge_id, stationName: alert.station_name, probability: alert.probability, activeProbability: alert.active_probability, recommendation: alert.recommendation, createdAt: alert.created_at, acknowledged: alert.acknowledged })))
  }

  useEffect(() => { void loadAlerts() }, [])
  useEffect(() => { if (!loading && stations.length) void runForecast() }, [loading, stations.length])
  useEffect(() => { if (preset !== 'Custom') setRainfall(rainfallPresets[preset]) }, [preset])
  useEffect(() => {
    const refreshTimer = window.setInterval(() => { if (!forecastLoading && view === 'live') void runForecast() }, 60000)
    return () => window.clearInterval(refreshTimer)
  }, [selectedGauge, onsetModel, activeModel, rainfall, view, forecastLoading])

  const riskTier = prediction?.alert_tier.tier ?? 'NORMAL'
  const riskCounts = historical ? { EMERGENCY: historical.emergency_count, WARNING: historical.warning_count, ADVISORY: historical.advisory_count, NORMAL: historical.normal_count } : { EMERGENCY: 0, WARNING: 0, ADVISORY: 0, NORMAL: 0 }
  const unreadAlerts = alerts.filter((alert) => !alert.acknowledged)
  const acknowledgeAlert = async (id: string) => { await fetch(`${API}/api/v1/alerts/${encodeURIComponent(id)}/acknowledge`, { method: 'POST' }); await loadAlerts() }
  const acknowledgeAll = async () => { await fetch(`${API}/api/v1/alerts/acknowledge-all`, { method: 'POST' }); await loadAlerts() }

  const geoStyle = (feature?: Feature) => {
    const id = String(feature?.properties?.GaugeID ?? feature?.properties?.gauge_id ?? '')
    const isSelected = id === selectedGauge || id.endsWith(selectedGauge)
    return { color: isSelected ? '#f4f7f4' : '#4a736c', weight: isSelected ? 3 : 1.5, fillColor: isSelected ? '#d86b49' : '#398f80', fillOpacity: isSelected ? 0.75 : 0.32 }
  }

  return (
    <div className="app-shell">
      <aside className={mobileNav ? 'sidebar is-open' : 'sidebar'}>
        <div className="brand"><div className="brand-mark"><Waves size={23} /></div><div><strong>PRAVAH</strong><span>RISK INTELLIGENCE</span></div><button className="icon-button mobile-close" onClick={() => setMobileNav(false)} aria-label="Close menu"><X size={18} /></button></div>
        <div className="region-switch"><span className="live-dot" /> Western Ghats corridor <ChevronRight size={15} /></div>
        <p className="nav-label">WORKSPACE</p>
        <nav className="side-nav">
          <button className={view === 'live' ? 'active' : ''} onClick={() => { setView('live'); setMobileNav(false) }}><Gauge size={17} /> Live operations <span>01</span></button>
          <button className={view === 'history' ? 'active' : ''} onClick={() => { setView('history'); setMobileNav(false) }}><CalendarDays size={17} /> Historical replay <span>02</span></button>
          <button className={view === 'models' ? 'active' : ''} onClick={() => { setView('models'); setMobileNav(false) }}><BarChart3 size={17} /> Model performance <span>03</span></button>
        </nav>
        <p className="nav-label">NETWORK</p>
        <div className="network-status"><div><Radio size={15} /><span>Inference API</span></div><b className={apiOnline ? '' : 'offline'}>{apiOnline ? 'ONLINE' : 'OFFLINE'}</b><small>{modelSummary.task_a_onset ? Object.keys(modelSummary.task_a_onset).length * 2 : 6} models · {stations.length || 20} gauges</small><small className={notificationStatus.enabled ? 'notify-ready' : ''}>Delivery: {notificationStatus.enabled ? notificationStatus.configured_channels.join(', ') || 'enabled' : 'in-app only'}</small></div>
        <div className="sidebar-bottom"><ShieldCheck size={16} /><span>Validated data pipeline</span></div>
      </aside>

      <main className="main-content">
        <header className="topbar"><button className="icon-button menu-trigger" onClick={() => setMobileNav(true)} aria-label="Open menu"><Menu size={20} /></button><div className="crumb"><span>PRAVAH</span><ChevronRight size={14} /><b>{view === 'live' ? 'Live operations' : view === 'history' ? 'Historical replay' : 'Model performance'}</b></div><div className="top-actions"><span className="last-sync"><span className={apiOnline ? 'live-dot' : 'live-dot offline-dot'} /> {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Connecting to API'}</span><button className="icon-button" onClick={() => view === 'history' ? void runHistory() : void runForecast()} aria-label="Refresh data"><RefreshCw size={17} className={forecastLoading ? 'spin' : ''} /></button><div className="alert-anchor"><button className={unreadAlerts.length ? 'icon-button alert-trigger has-alerts' : 'icon-button alert-trigger'} onClick={() => setAlertsOpen((open) => !open)} aria-label="Open alerts"><Bell size={18} /><span>{unreadAlerts.length}</span></button>{alertsOpen && <div className="alert-drawer"><div className="alert-drawer-head"><div><p className="eyebrow">OPERATOR ALERTS</p><h3>{unreadAlerts.length ? `${unreadAlerts.length} require attention` : 'No unread alerts'}</h3></div><button className="text-button" onClick={() => void acknowledgeAll()} disabled={!unreadAlerts.length}>Acknowledge all</button></div>{alerts.length ? <div className="alert-list">{alerts.map((alert) => <div className={alert.acknowledged ? 'alert-item acknowledged' : 'alert-item'} key={alert.id}><div className={`alert-severity ${tierClass[alert.tier]}`}><AlertTriangle size={14} /></div><div className="alert-copy"><div><b>{alert.tier}</b><span>Gauge {alert.gaugeId} · {alert.stationName}</span></div><p>{alert.recommendation}</p><small><Clock3 size={11} /> {new Date(alert.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} · onset {(alert.probability * 100).toFixed(1)}% · active {(alert.activeProbability * 100).toFixed(1)}%</small></div>{!alert.acknowledged && <button className="ack-button" onClick={() => void acknowledgeAlert(alert.id)} aria-label={`Acknowledge ${alert.tier} alert`}><Check size={15} /></button>}</div>)}</div> : <div className="empty-alerts"><Bell size={20} /><p>Alerts will appear here when a live model crosses its calibrated risk tier.</p></div>}</div>}</div><div className="avatar">AK</div></div></header>

        <section className="page-intro"><div><p className="eyebrow">MONSOON WATCH · 05 SEP 2026</p><h1>{view === 'live' ? 'Live catchment operations' : view === 'history' ? 'Replay a flood day' : 'Model performance'}</h1><p className="intro-copy">A decision surface for rainfall, catchment saturation, and early warning across Maharashtra's Western Ghats.</p></div><div className="intro-meta"><span>UTC +05:30</span><strong>20</strong><small>target catchments</small></div></section>
        {error && <div className="error-strip"><AlertTriangle size={17} /> {error}<button onClick={() => setError('')} aria-label="Dismiss error"><X size={15} /></button></div>}
        {view === 'live' && prediction && prediction.alert_tier.tier !== 'NORMAL' && <div className={`active-alert ${tierClass[prediction.alert_tier.tier]}`}><div className="active-alert-icon"><AlertTriangle size={19} /></div><div><span>ACTIVE {prediction.alert_tier.tier} ALERT · GAUGE {prediction.station.gauge_id}</span><strong>{prediction.station.station_name} requires operator attention</strong><p>{prediction.alert_tier.recommendation}</p></div><button className="alert-action" onClick={() => setAlertsOpen(true)}>Open alert center <ChevronRight size={15} /></button></div>}

        {view === 'live' && <>
          <section className="signal-grid">{tiers.map((tier) => <div className={`signal ${tierClass[tier]}`} key={tier}><span className="signal-kicker">{tier === 'EMERGENCY' ? 'Immediate action' : tier === 'WARNING' ? 'High attention' : tier === 'ADVISORY' ? 'Watch closely' : 'Baseline'}</span><strong>{historical ? riskCounts[tier] : tier === riskTier ? 1 : 0}</strong><span className="signal-label">{tier.toLowerCase()} risk</span></div>)}</section>
          <div className="workspace-grid">
            <section className="map-panel panel"><div className="panel-heading"><div><p className="eyebrow">SPATIAL VIEW</p><h2>Catchment risk field</h2></div><div className="legend">{tiers.map((tier) => <span key={tier}><i className={tierClass[tier]} />{tier[0] + tier.slice(1).toLowerCase()}</span>)}</div></div><div className="map-wrap">{geojson && <MapContainer center={[18.3, 74.3]} zoom={7} scrollWheelZoom className="risk-map"><TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" /><MapViewport selected={selected} /><GeoJSON data={geojson} style={geoStyle} /></MapContainer>}<div className="map-float"><Layers3 size={15} /> Risk layer <span>20 / 20 reporting</span></div></div></section>
            <aside className="detail-panel panel"><div className="panel-heading"><div><p className="eyebrow">SELECTED CATCHMENT</p><h2>{selected?.station_name ?? 'Loading station'}</h2></div><span className={`tier-pill ${tierClass[riskTier]}`}>{riskTier}</span></div><div className="station-id"><span>{selectedGauge}</span><span>{selected?.river ?? 'River network'} · {selected?.basin ?? 'Western Ghats'}</span><LocateFixed size={15} /></div>{prediction && <><div className="probability-block"><span>ONSET PROBABILITY</span><strong>{(prediction.task_a_onset.probability * 100).toFixed(1)}<small>%</small></strong><div className="probability-track"><i style={{ width: `${prediction.task_a_onset.probability * 100}%` }} /></div><div className="metric-note"><span>Model <b>{prediction.task_a_onset.model_used.replace('task_a_onset_', '')}</b></span><span>Threshold {prediction.task_a_onset.threshold.toFixed(3)}</span></div></div><div className="dual-metrics"><div><span>ACTIVE FLOOD</span><strong>{(prediction.task_b_active.probability * 100).toFixed(1)}%</strong><small>{prediction.task_b_active.model_used.replace('task_b_active_', '')}</small></div><div><span>10-DAY TOTAL</span><strong>{prediction.antecedent_rainfall_summary.rain_10d_sum_mm}<small> mm</small></strong><small>Antecedent rainfall</small></div></div><p className="recommendation"><AlertTriangle size={16} /> {prediction.alert_tier.recommendation}</p></>}</aside>
          </div>
          <section className="bottom-grid"><div className="panel controls-panel"><div className="panel-heading"><div><p className="eyebrow">FORECAST INPUT</p><h2>Rainfall scenario</h2></div><CloudRain size={20} className="panel-icon" /></div><div className="search-field"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search station, river, or basin" /></div><div className="control-row"><label>Catchment<select value={selectedGauge} onChange={(event) => setSelectedGauge(event.target.value)}>{filteredStations.map((station) => <option value={station.gauge_id} key={station.gauge_id}>{station.gauge_id} · {station.station_name}</option>)}</select></label><label>Scenario<select value={preset} onChange={(event) => setPreset(event.target.value)}><option>Custom</option>{Object.keys(rainfallPresets).map((name) => <option key={name}>{name}</option>)}</select></label></div><div className="control-row"><label>Onset model<select value={onsetModel} onChange={(event) => setOnsetModel(event.target.value)}><option>RandomForest</option><option>XGBoost</option><option>LightGBM</option></select></label><label>Active model<select value={activeModel} onChange={(event) => setActiveModel(event.target.value)}><option>XGBoost</option><option>LightGBM</option><option>RandomForest</option></select></label></div><button className="primary-button" onClick={() => void runForecast()} disabled={forecastLoading}><Activity size={17} /> {forecastLoading ? 'Running inference...' : 'Run live forecast'} <ChevronRight size={17} /></button></div><div className="panel rainfall-panel"><div className="panel-heading"><div><p className="eyebrow">ANTECEDENT PROFILE</p><h2>10-day rainfall</h2></div><span className="unit-label">millimetres / day</span></div><div className="rain-bars">{rainfall.map((value, index) => <div className="rain-bar" key={`${value}-${index}`}><span style={{ height: `${Math.max(value / 280 * 100, 5)}%` }} /><small>T-{10 - index}</small><b>{value}</b></div>)}</div></div></section>
        </>}

        {view === 'history' && <section className="history-layout"><div className="panel history-toolbar"><div><p className="eyebrow">EVENT REPLAY</p><h2>Step into the archive</h2><p>Run the production models against a recorded day and compare every catchment.</p></div><div className="history-controls"><label>Date<input type="date" value={historyDate} onChange={(event) => setHistoryDate(event.target.value)} /></label><button className="primary-button" onClick={() => void runHistory()} disabled={forecastLoading}><RefreshCw size={17} /> Replay date</button></div></div>{historical && <><div className="signal-grid history-signals">{tiers.map((tier) => <div className={`signal ${tierClass[tier]}`} key={tier}><span className="signal-kicker">{tier}</span><strong>{riskCounts[tier]}</strong><span className="signal-label">catchments</span></div>)}</div><div className="panel table-panel"><div className="panel-heading"><div><p className="eyebrow">CATCHMENT OUTCOMES</p><h2>{historical.date}</h2></div><span className="unit-label">{historical.total_stations_active} active records</span></div><div className="table-scroll"><table><thead><tr><th>Catchment</th><th>River</th><th>Tier</th><th>Onset probability</th><th>Active probability</th></tr></thead><tbody>{historical.catchments.map((item) => <tr key={item.gauge_id} onClick={() => { setSelectedGauge(item.gauge_id); setView('live') }}><td><b>{item.station_name}</b><small>Gauge {item.gauge_id}</small></td><td>{item.river}</td><td><span className={`tier-pill ${tierClass[item.alert_tier]}`}>{item.alert_tier}</span></td><td>{(item.onset_probability * 100).toFixed(1)}%</td><td>{(item.active_probability * 100).toFixed(1)}%</td></tr>)}</tbody></table></div></div></>}</section>}

        {view === 'models' && <section className="models-layout"><div className="panel model-hero"><div><p className="eyebrow">MODEL GOVERNANCE</p><h2>Every score has a provenance</h2><p>The frontend displays the exact serialized model selected for each inference call, including its calibrated decision threshold.</p></div><div className="model-badge"><SlidersHorizontal size={20} /><b>{Object.keys(modelSummary.task_a_onset ?? {}).length + Object.keys(modelSummary.task_b_active ?? {}).length || 6}</b><span>artifacts loaded</span></div></div><div className="model-cards"><div className="panel model-card"><span className="model-number">01</span><p className="eyebrow">TASK A · ONSET</p><h3>Flood onset classifier</h3><div className="model-score"><strong>0.8384</strong><span>ROC-AUC<br />test set</span></div><div className="model-row"><span>RandomForest</span><b>0.8384</b></div><div className="model-row"><span>XGBoost</span><b>0.7935</b></div><div className="model-row"><span>LightGBM</span><b>0.8102</b></div></div><div className="panel model-card accent-card"><span className="model-number">02</span><p className="eyebrow">TASK B · ACTIVE STATE</p><h3>Active flood classifier</h3><div className="model-score"><strong>0.7552</strong><span>ROC-AUC<br />test set</span></div><div className="model-row"><span>LightGBM</span><b>0.7552</b></div><div className="model-row"><span>XGBoost</span><b>0.6744</b></div><div className="model-row"><span>RandomForest</span><b>0.7036</b></div></div></div></section>}
      </main>
    </div>
  )
}

export default App
