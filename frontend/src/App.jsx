import { useEffect, useMemo, useState } from 'react'
import {
  Activity, ArrowUpRight, CheckCircle2, CircleAlert, Clock3, CloudUpload,
  FileVideo, Filter, LayoutDashboard, RefreshCw, Search, ShieldCheck,
  Video, XCircle, Play, Check, X, LoaderCircle
} from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const formatBytes = n => n > 1024 * 1024 ? `${(n / 1024 / 1024).toFixed(1)} MB` : `${(n / 1024).toFixed(0)} KB`
const date = d => d ? new Date(d).toLocaleString() : '—'

function Pill({ children, type = '' }) { return <span className={`pill ${type}`}>{children}</span> }
function Stat({ icon: Icon, label, value, note }) {
  return <div className="stat-card"><div className="stat-top"><span>{label}</span><span className="stat-icon"><Icon size={18}/></span></div><div className="stat-value">{value ?? '—'}</div><div className="stat-note">{note}</div></div>
}

export default function App() {
  const [videos, setVideos] = useState([])
  const [stats, setStats] = useState({})
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('ALL')
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')
  const [reviewer, setReviewer] = useState('Reviewer')
  const [comments, setComments] = useState('')
  const [busy, setBusy] = useState(false)

  async function refresh(keepSelected = true) {
    try {
      const [v, s] = await Promise.all([
        fetch(`${API}/api/videos`).then(r => { if (!r.ok) throw new Error('Could not load videos'); return r.json() }),
        fetch(`${API}/api/stats`).then(r => r.json())
      ])
      setVideos(v); setStats(s)
      if (keepSelected && selected) {
        const fresh = v.find(x => x.id === selected.id)
        if (fresh) setSelected(fresh)
      }
    } catch (e) { setMessage(`${e.message}. Is the FastAPI server running on port 8000?`) }
  }
  useEffect(() => { refresh(false); const t = setInterval(() => refresh(), 5000); return () => clearInterval(t) }, [])

  const visible = useMemo(() => videos.filter(v => {
    const matches = v.original_filename.toLowerCase().includes(search.toLowerCase())
    const status = filter === 'ALL' || (filter === 'PENDING' ? v.review_status === 'PENDING' : filter === 'APPROVED' ? v.review_status === 'APPROVED' : filter === 'REJECTED' ? v.review_status === 'REJECTED' : v.status === filter)
    return matches && status
  }), [videos, search, filter])

  async function upload(e) {
    const files = [...e.target.files]
    if (!files.length) return
    setUploading(true); setMessage('')
    try {
      const data = new FormData()
      files.forEach(f => data.append('files', f))
      const res = await fetch(`${API}/api/videos/upload`, { method: 'POST', body: data })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail || 'Upload failed')
      setMessage(`${body.length} video(s) uploaded. Quality checks are running.`)
      await refresh(false)
    } catch (err) { setMessage(err.message) }
    finally { setUploading(false); e.target.value = '' }
  }

  async function openVideo(video) {
    try {
      const fresh = await fetch(`${API}/api/videos/${video.id}`).then(r => r.json())
      setSelected(fresh); setComments(fresh.review?.comments || '')
    } catch { setSelected(video) }
  }

  async function decide(decision) {
    if (!selected) return
    setBusy(true); setMessage('')
    try {
      const res = await fetch(`${API}/api/videos/${selected.id}/review`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reviewer, comments })
      })
      const body = await res.json()
      if (!res.ok) throw new Error(body.detail || 'Could not save review')
      setSelected(body); setMessage(`Video ${decision.toLowerCase()} successfully.`); await refresh()
    } catch (e) { setMessage(e.message) }
    finally { setBusy(false) }
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Video size={21}/></div><div><strong>Fourthuman</strong><small>VIDEO QUALITY CONTROL</small></div></div>
      <div className="nav-label">WORKSPACE</div>
      <div className="nav-item active"><LayoutDashboard size={17}/> Overview</div>
      <div className="nav-item"><FileVideo size={17}/> Video intake <span className="nav-count">{videos.length}</span></div>
      <div className="sidebar-bottom"><div className="system-status"><span className="live-dot"></span><div><b>System status</b><small>Connected to API</small></div></div><small className="version">VideoQC · MVP 1.0</small></div>
    </aside>

    <main className="main">
      <header className="topbar"><div><div className="eyebrow">WORKSPACE / OVERVIEW</div><h1>Video intake & quality control</h1><p>Manage incoming videos, inspect automated checks and record review decisions.</p></div><button className="btn secondary" onClick={() => refresh()}><RefreshCw size={15}/> Refresh</button></header>
      {message && <div className="notice"><span>{message}</span><button onClick={() => setMessage('')}><X size={15}/></button></div>}

      <section className="stats-grid">
        <Stat icon={FileVideo} label="Total videos" value={stats.total ?? 0} note="All uploaded files"/>
        <Stat icon={CheckCircle2} label="QC passed" value={stats.qc_passed ?? 0} note="Passed configured checks"/>
        <Stat icon={CircleAlert} label="QC failed" value={stats.qc_failed ?? 0} note="Needs attention"/>
        <Stat icon={Clock3} label="Pending review" value={stats.pending_review ?? 0} note="Awaiting human decision"/>
      </section>

      <section className="content-grid">
        <div className="panel video-panel">
          <div className="panel-head"><div><h2>Video library</h2><p>Uploaded assets and their current status</p></div><label className={`btn primary upload-btn ${uploading ? 'disabled' : ''}`}><CloudUpload size={16}/>{uploading ? 'Uploading…' : 'Upload videos'}<input type="file" accept="video/*,.mkv" multiple onChange={upload} disabled={uploading}/></label></div>
          <div className="toolbar"><div className="searchbox"><Search size={16}/><input placeholder="Search videos..." value={search} onChange={e => setSearch(e.target.value)}/></div><div className="filterbox"><Filter size={15}/><select value={filter} onChange={e => setFilter(e.target.value)}><option value="ALL">All videos</option><option value="PENDING">Pending review</option><option value="QC_PASSED">QC passed</option><option value="QC_FAILED">QC failed</option><option value="APPROVED">Approved</option><option value="REJECTED">Rejected</option></select></div></div>
          <div className="table-wrap"><table><thead><tr><th>VIDEO</th><th>QC RESULT</th><th>REVIEW</th><th>UPLOADED</th><th></th></tr></thead><tbody>
            {visible.map(v => <tr key={v.id} className={selected?.id === v.id ? 'selected-row' : ''} onClick={() => openVideo(v)}><td><div className="file-cell"><div className="file-icon"><FileVideo size={18}/></div><div><b>{v.original_filename}</b><small>{formatBytes(v.file_size)} · {v.width && v.height ? `${v.width}×${v.height}` : 'Metadata pending'}</small></div></div></td><td><Pill type={v.status === 'QC_PASSED' ? 'green' : v.status === 'QC_FAILED' || v.status === 'PROCESSING_ERROR' ? 'red' : 'amber'}>{v.status.replaceAll('_',' ')}</Pill></td><td><Pill type={v.review_status === 'APPROVED' ? 'green' : v.review_status === 'REJECTED' ? 'red' : 'blue'}>{v.review_status}</Pill></td><td className="date-cell">{date(v.upload_date)}</td><td><button className="icon-btn" title="Open review"><ArrowUpRight size={16}/></button></td></tr>)}
            {!visible.length && <tr><td colSpan="5"><div className="empty"><FileVideo size={26}/><b>No videos found</b><span>Upload video files to start the QC workflow.</span></div></td></tr>}
          </tbody></table></div>
          <div className="table-foot"><span>Showing {visible.length} of {videos.length} videos</span><span><span className="live-dot"></span> Auto-refreshing every 5 seconds</span></div>
        </div>

        <div className="panel detail-panel">
          {!selected ? <div className="detail-empty"><div className="detail-empty-icon"><ShieldCheck size={27}/></div><h3>Review workspace</h3><p>Select a video from the library to inspect its playback, quality checks and review history.</p><div className="hint"><Play size={14}/> Select any video row to begin</div></div> :
            <><div className="panel-head detail-heading"><div><div className="eyebrow">VIDEO REVIEW</div><h2>Inspection details</h2></div><button className="icon-btn" onClick={() => setSelected(null)}><X size={17}/></button></div>
              <div className="selected-name">{selected.original_filename}</div>
              <div className="player-wrap"><video controls preload="metadata" src={`${API}/api/videos/${selected.id}/file`}><track kind="captions"/></video></div>
              <div className="meta-grid"><div><small>DURATION</small><b>{selected.duration_seconds ? `${selected.duration_seconds.toFixed(2)} sec` : 'Processing'}</b></div><div><small>RESOLUTION</small><b>{selected.width ? `${selected.width} × ${selected.height}` : '—'}</b></div><div><small>FRAME RATE</small><b>{selected.fps ? `${selected.fps.toFixed(2)} FPS` : '—'}</b></div><div><small>FILE SIZE</small><b>{formatBytes(selected.file_size)}</b></div></div>
              <div className="qc-title"><div><h3>Automated quality checks</h3><p>Rule-based inspection results</p></div><Pill type={selected.status === 'QC_PASSED' ? 'green' : selected.status === 'QC_FAILED' ? 'red' : 'amber'}>{selected.status.replaceAll('_',' ')}</Pill></div>
              <div className="checks">{(selected.quality_checks || []).map(c => <div className="check-row" key={c.id}><span className={`check-symbol ${c.result.toLowerCase()}`}>{c.result === 'PASS' ? <Check size={13}/> : c.result === 'FAIL' ? <X size={13}/> : <CircleAlert size={13}/>}</span><div className="check-copy"><b>{c.check_name.replaceAll('_',' ')}</b><small>{c.reason}{c.measured_value ? ` · Measured: ${c.measured_value}` : ''}</small></div><Pill type={c.result === 'PASS' ? 'green' : c.result === 'FAIL' ? 'red' : 'amber'}>{c.result}</Pill></div>)}
                {!selected.quality_checks?.length && <div className="muted">Quality checks will appear after processing.</div>}</div>
              <div className="review-form"><h3>Human review</h3><label>Reviewer name<input value={reviewer} onChange={e => setReviewer(e.target.value)} /></label><label>Comments<textarea rows="3" placeholder="Add review notes or rejection reason..." value={comments} onChange={e => setComments(e.target.value)}/></label><div className="decision-row"><button className="btn danger" disabled={busy} onClick={() => decide('REJECTED')}><XCircle size={15}/> Reject</button><button className="btn approve" disabled={busy} onClick={() => decide('APPROVED')}><CheckCircle2 size={15}/> Approve</button></div>{selected.review && <div className="review-history">Last decision: <b>{selected.review.decision}</b> by {selected.review.reviewer} · {date(selected.review.reviewed_at)}</div>}</div>
            </>}
        </div>
      </section>
      <footer>FOURTHUMAN VIDEOQC <span>·</span> Video intake and quality assurance workspace</footer>
    </main>
  </div>
}
