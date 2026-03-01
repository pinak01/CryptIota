import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Shield, AlertTriangle, GitBranch, Clock, Cpu, HardDrive, Wifi, Battery, RotateCcw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchDevice } from '../api/apiClient'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

export default function DeviceDetail() {
    const { id } = useParams()
    const [device, setDevice] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        setLoading(true)
        fetchDevice(id)
            .then(setDevice)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [id])

    if (loading) return <LoadingSpinner text={`Loading ${id}...`} />
    if (error) return <div className="text-center py-20 text-red-400">Error: {error}</div>
    if (!device) return null

    const ra = device.risk_assessments?.[0]
    const plan = device.migration_plan
    const confidence = ra?.confidence_scores || (device.risk_assessments?.length > 0 ? {} : null)

    // Risk gauge
    const riskPct = Math.round((ra?.risk_score || 0) * 100)
    const gaugeColor = riskPct >= 75 ? '#ef4444' : riskPct >= 50 ? '#f97316' : riskPct >= 25 ? '#eab308' : '#22c55e'

    const sensitivityLabels = ['Public', 'Internal', 'Confidential', 'Sensitive', 'Critical']
    const infoItems = [
        { icon: Cpu, label: 'CPU', value: `${device.cpu_mhz} MHz` },
        { icon: HardDrive, label: 'RAM', value: `${device.ram_kb} KB` },
        { icon: Wifi, label: 'Network', value: device.network_exposure ? 'Internet-facing' : 'Isolated' },
        { icon: Battery, label: 'Power', value: device.battery_powered ? 'Battery' : 'Mains' },
        { icon: RotateCcw, label: 'Key Rotation', value: `${device.key_rotation_days} days` },
        { icon: Clock, label: 'Deployment Age', value: `${device.deployment_age_years} years` },
    ]

    // Confidence chart data
    const confidenceData = confidence ? Object.entries(confidence).map(([k, v]) => ({ name: k, value: v })) : []
    const confColors = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-3">
                <Link to="/devices" className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                    <ArrowLeft className="w-5 h-5 text-[var(--color-text-secondary)]" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold font-mono">{device.device_id}</h1>
                    <p className="text-sm text-[var(--color-text-secondary)]">{device.location}</p>
                </div>
                {ra && <RiskBadge level={ra.risk_level} size="lg" />}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* LEFT COLUMN */}
                <div className="space-y-6">
                    {/* Device Profile */}
                    <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Shield className="w-5 h-5 text-[var(--color-accent)]" /> Device Profile</h2>
                        <div className="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
                            <div><span className="text-[var(--color-text-muted)]">Type</span><p className="font-medium capitalize">{device.device_type?.replace(/_/g, ' ')}</p></div>
                            <div><span className="text-[var(--color-text-muted)]">Algorithm</span><p className="font-mono font-medium">{device.encryption_algorithm}</p></div>
                            <div><span className="text-[var(--color-text-muted)]">Sensitivity</span><p className="font-medium">{sensitivityLabels[device.data_sensitivity]} ({device.data_sensitivity})</p></div>
                            <div><span className="text-[var(--color-text-muted)]">Retention</span><p className="font-medium">{device.data_retention_years} years</p></div>
                            <div><span className="text-[var(--color-text-muted)]">Update Capable</span><p className="font-medium">{device.update_capable ? '✅ Yes' : '❌ No'}</p></div>
                            <div><span className="text-[var(--color-text-muted)]">Connected Devices</span><p className="font-medium">{device.num_connected_devices}</p></div>
                            <div><span className="text-[var(--color-text-muted)]">Data Volume</span><p className="font-medium">{device.data_volume_mb_per_day} MB/day</p></div>
                        </div>
                        <div className="grid grid-cols-3 gap-3 mt-5">
                            {infoItems.map(({ icon: Icon, label, value }) => (
                                <div key={label} className="flex items-center gap-2 p-2 rounded-lg bg-white/5 text-xs">
                                    <Icon className="w-4 h-4 text-[var(--color-text-muted)]" />
                                    <div><p className="text-[var(--color-text-muted)]">{label}</p><p className="font-medium">{value}</p></div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Risk Gauge */}
                    <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Risk Score</h2>
                        <div className="flex items-center justify-center">
                            <div className="relative w-48 h-48">
                                <svg viewBox="0 0 120 120" className="w-full h-full">
                                    <circle cx="60" cy="60" r="50" fill="none" stroke="#334155" strokeWidth="8" strokeDasharray="235.6" strokeDashoffset="78.5" strokeLinecap="round" transform="rotate(135 60 60)" />
                                    <circle cx="60" cy="60" r="50" fill="none" stroke={gaugeColor} strokeWidth="8" strokeDasharray="235.6" strokeDashoffset={235.6 - (riskPct / 100) * 157} strokeLinecap="round" transform="rotate(135 60 60)" style={{ transition: 'stroke-dashoffset 1s ease-in-out' }} />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-4xl font-bold" style={{ color: gaugeColor }}>{riskPct}</span>
                                    <span className="text-xs text-[var(--color-text-muted)]">Risk Score</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Current vs Recommended */}
                    {ra && (
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-[var(--color-bg-card)] border-2 border-red-500/30 rounded-xl p-4">
                                <p className="text-xs text-[var(--color-text-muted)] mb-1">Current Algorithm</p>
                                <p className="font-mono font-semibold text-red-400">{device.encryption_algorithm}</p>
                                <p className="text-xs text-red-400/70 mt-1">⚠ Quantum Vulnerable</p>
                            </div>
                            <div className="bg-[var(--color-bg-card)] border-2 border-green-500/30 rounded-xl p-4">
                                <p className="text-xs text-[var(--color-text-muted)] mb-1">Recommended</p>
                                <p className="font-mono font-semibold text-green-400">{ra.recommended_algorithm}</p>
                                <p className="text-xs text-green-400/70 mt-1">✓ Quantum Resistant</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* RIGHT COLUMN */}
                <div className="space-y-6">
                    {/* Confidence Scores */}
                    {confidenceData.length > 0 && (
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-4">ML Classification Confidence</h2>
                            <div className="space-y-3">
                                {confidenceData.map(({ name, value }) => (
                                    <div key={name}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="font-medium">{name}</span>
                                            <span className="text-[var(--color-text-muted)]">{value}%</span>
                                        </div>
                                        <div className="h-2.5 bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${value}%`, backgroundColor: confColors[name] }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Migration Plan */}
                    {plan && (
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><GitBranch className="w-5 h-5 text-[var(--color-accent)]" /> Migration Plan</h2>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Phase</span><span className="font-medium">{plan.migration_phase}</span></div>
                                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Target</span><span className="font-mono">{plan.target_algorithm}</span></div>
                                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Effort</span><span className="font-medium">{plan.estimated_effort}</span></div>
                                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Priority</span><span className="font-medium">{(plan.priority_score * 100).toFixed(0)}%</span></div>
                                <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Status</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${plan.status === 'Complete' ? 'bg-green-500/15 text-green-400' : plan.status === 'InProgress' ? 'bg-blue-500/15 text-blue-400' : 'bg-orange-500/15 text-orange-400'}`}>{plan.status}</span>
                                </div>
                                {plan.notes && <p className="text-[var(--color-text-secondary)] bg-white/5 p-3 rounded-lg">{plan.notes}</p>}
                            </div>
                        </div>
                    )}

                    {/* Reasoning */}
                    {ra && (
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-[var(--color-medium)]" /> Risk Analysis</h2>
                            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{ra.reasoning}</p>
                        </div>
                    )}

                    {/* Alerts */}
                    {device.alerts?.length > 0 && (
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-3">Alerts ({device.alerts.length})</h2>
                            <div className="space-y-2">
                                {device.alerts.map(a => (
                                    <div key={a.id} className="p-3 rounded-lg bg-white/5 text-sm">
                                        <div className="flex items-center gap-2">
                                            <RiskBadge level={a.severity} size="sm" />
                                            <span className="text-[var(--color-text-muted)] text-xs">{new Date(a.created_at).toLocaleDateString()}</span>
                                        </div>
                                        <p className="text-[var(--color-text-secondary)] mt-1">{a.message}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
