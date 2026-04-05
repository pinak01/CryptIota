import { useState, useEffect, useCallback } from 'react'
import {
    FlaskConical, Wifi, WifiOff, Shield, ShieldAlert, ShieldCheck, ShieldX,
    Radio, Zap, Cpu, MemoryStick, Play, RefreshCw, Loader2, AlertTriangle,
    Plus, ArrowDownUp, Eye, Lock, Unlock
} from 'lucide-react'
import {
    fetchIoTLabSummary, fetchIoTLabDevices, fetchIoTLabSessions,
    fetchIoTLabAttacks, simulateAttack, registerIoTDevice,
} from '../api/apiClient'

const MODE_STYLES = {
    pqc: { bg: 'bg-green-500/15', text: 'text-green-400', border: 'border-green-500/30', label: 'PQC (Kyber)' },
    classical: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30', label: 'Classical (ECDH)' },
    hybrid: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', border: 'border-yellow-500/30', label: 'Hybrid' },
}

const SEVERITY_STYLES = {
    critical: { bg: 'bg-red-500/15', text: 'text-red-400', icon: ShieldX },
    warning: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', icon: AlertTriangle },
    info: { bg: 'bg-blue-500/15', text: 'text-blue-400', icon: Eye },
}

function ModeBadge({ mode }) {
    const s = MODE_STYLES[mode] || MODE_STYLES.classical
    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${s.bg} ${s.text} border ${s.border}`}>
            {mode === 'pqc' ? <ShieldCheck className="w-3 h-3" /> : mode === 'hybrid' ? <Shield className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
            {s.label}
        </span>
    )
}

function SeverityBadge({ severity }) {
    const s = SEVERITY_STYLES[severity] || SEVERITY_STYLES.info
    const Icon = s.icon
    return (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${s.bg} ${s.text}`}>
            <Icon className="w-3 h-3" />
            {severity.toUpperCase()}
        </span>
    )
}

function StatCard({ icon: Icon, label, value, sub, color = 'text-[var(--color-accent)]' }) {
    return (
        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5 flex items-start gap-4">
            <div className={`w-10 h-10 rounded-lg ${color === 'text-green-400' ? 'bg-green-500/15' : color === 'text-red-400' ? 'bg-red-500/15' : color === 'text-yellow-400' ? 'bg-yellow-500/15' : 'bg-blue-500/15'} flex items-center justify-center shrink-0`}>
                <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
                <p className="text-sm text-[var(--color-text-muted)]">{label}</p>
                <p className={`text-2xl font-bold ${color}`}>{value ?? '—'}</p>
                {sub && <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{sub}</p>}
            </div>
        </div>
    )
}

export default function IoTSecurityLab() {
    const [summary, setSummary] = useState(null)
    const [devices, setDevices] = useState([])
    const [sessions, setSessions] = useState([])
    const [attacks, setAttacks] = useState([])
    const [loading, setLoading] = useState(true)
    const [simulating, setSimulating] = useState(null)
    const [showRegister, setShowRegister] = useState(false)
    const [regForm, setRegForm] = useState({ device_name: '', device_type: 'simulated', cpu_mhz: 240, ram_kb: 520, supports_pqc: false })
    const [regLoading, setRegLoading] = useState(false)

    const refresh = useCallback(() => {
        setLoading(true)
        Promise.all([
            fetchIoTLabSummary().catch(() => null),
            fetchIoTLabDevices().catch(() => ({ devices: [] })),
            fetchIoTLabSessions().catch(() => ({ sessions: [] })),
            fetchIoTLabAttacks().catch(() => ({ attacks: [] })),
        ]).then(([sum, dev, sess, atk]) => {
            setSummary(sum)
            setDevices(dev?.devices || [])
            setSessions(sess?.sessions || [])
            setAttacks(atk?.attacks || [])
        }).finally(() => setLoading(false))
    }, [])

    useEffect(() => { refresh() }, [refresh])

    const handleSimulate = async (type) => {
        setSimulating(type)
        try {
            await simulateAttack(type)
            refresh()
        } catch { /* ignore */ }
        setSimulating(null)
    }

    const handleRegister = async (e) => {
        e.preventDefault()
        setRegLoading(true)
        try {
            await registerIoTDevice(regForm)
            setShowRegister(false)
            setRegForm({ device_name: '', device_type: 'simulated', cpu_mhz: 240, ram_kb: 520, supports_pqc: false })
            refresh()
        } catch { /* ignore */ }
        setRegLoading(false)
    }

    const avgPqc = summary?.avg_handshake_ms_by_mode?.pqc
    const avgClassical = summary?.avg_handshake_ms_by_mode?.classical

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/25">
                        <FlaskConical className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold">IoT Security Lab</h1>
                        <p className="text-sm text-[var(--color-text-muted)]">Quantum-secure communication testbed</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={refresh} disabled={loading} className="flex items-center gap-2 px-3 py-2 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg text-sm hover:bg-[var(--color-bg-card-hover)] transition-colors">
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
                    </button>
                    <button onClick={() => setShowRegister(!showRegister)} className="flex items-center gap-2 px-3 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg text-sm font-medium transition-colors">
                        <Plus className="w-4 h-4" /> Register Device
                    </button>
                </div>
            </div>

            {/* liboqs status badge */}
            {summary && (
                <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${summary.using_liboqs ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'}`}>
                    <div className={`w-2 h-2 rounded-full ${summary.using_liboqs ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`} />
                    {summary.using_liboqs ? '🔐 liboqs active — Real PQC operations' : '⚠ Simulated PQC mode'}
                </div>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={Wifi} label="Connected Devices" value={summary?.online_devices || 0} sub={`${summary?.total_devices || 0} total registered`} color="text-green-400" />
                <StatCard icon={Radio} label="Active Sessions" value={summary?.active_sessions || 0} sub={`${summary?.total_sessions || 0} total`} color="text-[var(--color-accent)]" />
                <StatCard icon={ShieldAlert} label="Attacks Detected" value={summary?.attack_stats?.total_attacks || 0} sub={`${summary?.attack_stats?.by_severity?.critical || 0} critical`} color="text-red-400" />
                <StatCard icon={Zap} label="Avg PQC Handshake" value={avgPqc != null ? `${avgPqc.toFixed(1)}ms` : '—'} sub={avgClassical != null ? `Classical: ${avgClassical.toFixed(1)}ms` : 'No data yet'} color="text-yellow-400" />
            </div>

            {/* Device Registration Form */}
            {showRegister && (
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-accent)]/30 rounded-xl p-5 animate-fade-in">
                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Plus className="w-4 h-4 text-[var(--color-accent)]" /> Register New Device</h3>
                    <form onSubmit={handleRegister} className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                        <input value={regForm.device_name} onChange={e => setRegForm(p => ({ ...p, device_name: e.target.value }))} placeholder="Device Name" required className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-accent)]" />
                        <select value={regForm.device_type} onChange={e => setRegForm(p => ({ ...p, device_type: e.target.value }))} className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-accent)]">
                            <option value="simulated">Simulated</option>
                            <option value="esp32">ESP32</option>
                            <option value="rpi">Raspberry Pi</option>
                        </select>
                        <input type="number" value={regForm.cpu_mhz} onChange={e => setRegForm(p => ({ ...p, cpu_mhz: +e.target.value }))} placeholder="CPU MHz" className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-accent)]" />
                        <input type="number" value={regForm.ram_kb} onChange={e => setRegForm(p => ({ ...p, ram_kb: +e.target.value }))} placeholder="RAM KB" className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-accent)]" />
                        <label className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                            <input type="checkbox" checked={regForm.supports_pqc} onChange={e => setRegForm(p => ({ ...p, supports_pqc: e.target.checked }))} className="accent-[var(--color-accent)]" /> PQC Capable
                        </label>
                        <button type="submit" disabled={regLoading} className="flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                            {regLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Register
                        </button>
                    </form>
                </div>
            )}

            {/* Devices */}
            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
                    <h2 className="text-sm font-semibold flex items-center gap-2"><Cpu className="w-4 h-4 text-[var(--color-text-muted)]" /> Lab Devices</h2>
                    <span className="text-xs text-[var(--color-text-muted)]">{devices.length} devices</span>
                </div>
                {devices.length === 0 ? (
                    <div className="px-5 py-8 text-center text-[var(--color-text-muted)] text-sm">No devices registered. Click "Register Device" to add one, or run a simulation.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead><tr className="border-b border-[var(--color-border)]">
                                {['Name', 'Type', 'CPU', 'RAM', 'PQC', 'Mode', 'Status', 'Last Seen'].map(h => <th key={h} className="text-left px-4 py-2.5 font-medium text-[var(--color-text-muted)] text-xs">{h}</th>)}
                            </tr></thead>
                            <tbody>{devices.map(d => (
                                <tr key={d.id} className="border-b border-[var(--color-border)] hover:bg-white/[0.02] transition-colors">
                                    <td className="px-4 py-2.5 font-medium">{d.device_name}</td>
                                    <td className="px-4 py-2.5 text-[var(--color-text-secondary)] font-mono text-xs">{d.device_type}</td>
                                    <td className="px-4 py-2.5 font-mono text-xs">{d.cpu_mhz} MHz</td>
                                    <td className="px-4 py-2.5 font-mono text-xs">{d.ram_kb} KB</td>
                                    <td className="px-4 py-2.5">{d.supports_pqc ? <ShieldCheck className="w-4 h-4 text-green-400" /> : <ShieldAlert className="w-4 h-4 text-red-400" />}</td>
                                    <td className="px-4 py-2.5"><ModeBadge mode={d.handshake_mode} /></td>
                                    <td className="px-4 py-2.5">
                                        <span className={`inline-flex items-center gap-1.5 text-xs ${d.status === 'online' ? 'text-green-400' : 'text-[var(--color-text-muted)]'}`}>
                                            {d.status === 'online' ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />} {d.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-2.5 text-xs text-[var(--color-text-muted)]">{d.last_seen ? new Date(d.last_seen).toLocaleTimeString() : '—'}</td>
                                </tr>
                            ))}</tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Sessions & Attacks Side by Side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Sessions */}
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-[var(--color-border)]">
                        <h2 className="text-sm font-semibold flex items-center gap-2"><Lock className="w-4 h-4 text-[var(--color-text-muted)]" /> Cryptographic Sessions</h2>
                    </div>
                    {sessions.length === 0 ? (
                        <div className="px-5 py-8 text-center text-[var(--color-text-muted)] text-sm">No sessions yet. Run a simulation to create one.</div>
                    ) : (
                        <div className="divide-y divide-[var(--color-border)] max-h-[400px] overflow-y-auto">
                            {sessions.map(s => (
                                <div key={s.session_id} className="px-5 py-3 hover:bg-white/[0.02] transition-colors">
                                    <div className="flex items-center justify-between mb-1.5">
                                        <span className="font-mono text-xs text-[var(--color-text-muted)]">{s.session_id?.substring(0, 8)}…</span>
                                        <ModeBadge mode={s.mode} />
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div><span className="text-[var(--color-text-muted)]">Handshake:</span> <span className="text-[var(--color-accent)] font-mono">{s.handshake_time_ms?.toFixed(2)}ms</span></div>
                                        <div><span className="text-[var(--color-text-muted)]">Key:</span> <span className="font-mono">{s.public_key_bytes}B</span></div>
                                        <div><span className="text-[var(--color-text-muted)]">CT:</span> <span className="font-mono">{s.ciphertext_bytes}B</span></div>
                                    </div>
                                    {(s.device_handshake_cpu_time_ms != null || s.device_free_heap_before != null) && (
                                        <div className="grid grid-cols-3 gap-2 text-xs mt-1 pt-1 border-t border-[var(--color-border)]">
                                            {s.device_handshake_cpu_time_ms != null && <div><span className="text-[var(--color-text-muted)]">Dev CPU:</span> <span className="text-orange-400 font-mono">{s.device_handshake_cpu_time_ms?.toFixed(1)}ms</span></div>}
                                            {s.device_free_heap_before != null && <div><span className="text-[var(--color-text-muted)]">Heap Δ:</span> <span className="text-purple-400 font-mono">{((s.device_free_heap_before - (s.device_free_heap_after || 0)) / 1024).toFixed(1)}KB</span></div>}
                                            <div><span className="text-[var(--color-text-muted)]">Nonces:</span> <span className="font-mono">{s.nonce_counter}</span></div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Attack Log */}
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-[var(--color-border)]">
                        <h2 className="text-sm font-semibold flex items-center gap-2"><ShieldX className="w-4 h-4 text-red-400" /> Attack Detection Log</h2>
                    </div>
                    {attacks.length === 0 ? (
                        <div className="px-5 py-8 text-center text-[var(--color-text-muted)] text-sm">No attacks detected. Use the simulator below to trigger test attacks.</div>
                    ) : (
                        <div className="divide-y divide-[var(--color-border)] max-h-[400px] overflow-y-auto">
                            {attacks.map(a => {
                                let details = {}
                                try { details = JSON.parse(a.details || '{}') } catch { details = {} }
                                return (
                                    <div key={a.id} className="px-5 py-3 hover:bg-white/[0.02] transition-colors">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-2">
                                                <SeverityBadge severity={a.severity} />
                                                <span className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]">{a.attack_type}</span>
                                            </div>
                                            <span className="text-xs text-[var(--color-text-muted)]">{a.detected_at ? new Date(a.detected_at).toLocaleTimeString() : ''}</span>
                                        </div>
                                        <p className="text-xs text-[var(--color-text-secondary)] mt-1">{details.description || a.details}</p>
                                        {a.source_ip && <p className="text-xs text-[var(--color-text-muted)] mt-0.5 font-mono">Source: {a.source_ip}</p>}
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* Attack Simulator */}
            <div className="bg-[var(--color-bg-card)] border border-purple-500/20 rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-1 flex items-center gap-2">
                    <FlaskConical className="w-5 h-5 text-purple-400" /> Attack Simulator
                </h2>
                <p className="text-sm text-[var(--color-text-muted)] mb-4">Trigger controlled attack scenarios to test detection capabilities. Each simulation creates a full device → handshake → telemetry cycle before injecting the attack.</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {[
                        { type: 'replay', label: 'Replay Attack', desc: 'Re-sends a captured telemetry packet with the same nonce to test nonce-reuse detection.', icon: RefreshCw, color: 'from-red-600 to-red-700' },
                        { type: 'downgrade', label: 'Downgrade Attack', desc: 'Forces a device from PQC → Classical to test protocol downgrade detection.', icon: ArrowDownUp, color: 'from-yellow-600 to-yellow-700' },
                        { type: 'mitm', label: 'MITM Attack', desc: 'Injects tampered ciphertext to test AES-GCM authentication tag validation.', icon: ShieldX, color: 'from-purple-600 to-purple-700' },
                    ].map(({ type, label, desc, icon: Icon, color }) => (
                        <button
                            key={type}
                            onClick={() => handleSimulate(type)}
                            disabled={simulating !== null}
                            className="text-left p-4 rounded-xl border border-[var(--color-border)] hover:border-[var(--color-border-light)] transition-all group disabled:opacity-50"
                        >
                            <div className="flex items-center gap-3 mb-2">
                                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center`}>
                                    {simulating === type ? <Loader2 className="w-4 h-4 text-white animate-spin" /> : <Icon className="w-4 h-4 text-white" />}
                                </div>
                                <span className="font-semibold text-sm">{label}</span>
                            </div>
                            <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">{desc}</p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Research Metrics Explainer */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[var(--color-bg-card)] border border-green-500/20 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2"><ShieldCheck className="w-5 h-5 text-green-400" /><h3 className="font-semibold text-green-400">PQC Channel (Kyber)</h3></div>
                    <p className="text-sm text-[var(--color-text-secondary)]">ML-KEM-512 via liboqs → HKDF-SHA256 → AES-256-GCM. Quantum-resistant key encapsulation with 128-bit security level. Larger keys (~800B) but sub-millisecond handshakes on modern hardware.</p>
                </div>
                <div className="bg-[var(--color-bg-card)] border border-red-500/20 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2"><ShieldAlert className="w-5 h-5 text-red-400" /><h3 className="font-semibold text-red-400">Classical Channel (ECDH)</h3></div>
                    <p className="text-sm text-[var(--color-text-secondary)]">ECDH P-256 → HKDF-SHA256 → AES-256-GCM. Performance baseline for comparison. Smaller keys (~91B) but vulnerable to Shor's algorithm on future quantum computers.</p>
                </div>
                <div className="bg-[var(--color-bg-card)] border border-purple-500/20 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2"><FlaskConical className="w-5 h-5 text-purple-400" /><h3 className="font-semibold text-purple-400">Attack Resilience</h3></div>
                    <p className="text-sm text-[var(--color-text-secondary)]">Replay: nonce tracking. Downgrade: mode regression detection. MITM/Tampering: AES-GCM authentication tag verification. All events logged for comparative analysis.</p>
                </div>
            </div>
        </div>
    )
}
