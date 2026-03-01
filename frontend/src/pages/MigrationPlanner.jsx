import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, Download, Shield, Clock, Zap } from 'lucide-react'
import { fetchMigrationRoadmap } from '../api/apiClient'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const PHASE_CONFIG = {
    Immediate: { color: '#ef4444', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: AlertTriangle, label: 'Immediate' },
    ShortTerm: { color: '#f97316', bg: 'bg-orange-500/10', border: 'border-orange-500/20', icon: Clock, label: 'Short-Term' },
    LongTerm: { color: '#eab308', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', icon: Zap, label: 'Long-Term' },
    Monitor: { color: '#22c55e', bg: 'bg-green-500/10', border: 'border-green-500/20', icon: Shield, label: 'Monitor' },
}

export default function MigrationPlanner() {
    const [roadmap, setRoadmap] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        fetchMigrationRoadmap()
            .then(setRoadmap)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [])

    if (loading) return <LoadingSpinner text="Building migration roadmap..." />
    if (error) return <div className="text-center py-20 text-red-400">Error: {error}</div>
    if (!roadmap) return null

    const summary = roadmap.summary || {}

    const handleExport = () => {
        const blob = new Blob([JSON.stringify(roadmap, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = 'migration_roadmap.json'; a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <h1 className="text-2xl font-bold">Post-Quantum Migration Roadmap</h1>
                <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg text-sm font-medium transition-colors">
                    <Download className="w-4 h-4" /> Export Report
                </button>
            </div>

            {/* Summary Banner */}
            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5 flex flex-wrap gap-6">
                <div className="text-center">
                    <p className="text-3xl font-bold text-red-400">{summary.immediate_count || 0}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">Immediate Action</p>
                </div>
                <div className="text-center">
                    <p className="text-3xl font-bold text-orange-400">{summary.shortterm_count || 0}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">Short-Term</p>
                </div>
                <div className="text-center">
                    <p className="text-3xl font-bold text-yellow-400">{summary.longterm_count || 0}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">Long-Term</p>
                </div>
                <div className="text-center">
                    <p className="text-3xl font-bold text-green-400">{summary.monitor_count || 0}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">Monitoring</p>
                </div>
                <div className="text-center ml-auto">
                    <p className="text-3xl font-bold text-[var(--color-text-primary)]">{summary.total_devices || 0}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">Total Devices</p>
                </div>
            </div>

            {/* Kanban */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                {Object.entries(PHASE_CONFIG).map(([phase, config]) => {
                    const devices = roadmap[phase] || []
                    const Icon = config.icon
                    return (
                        <div key={phase} className="flex flex-col">
                            <div className={`flex items-center gap-2 px-4 py-3 rounded-t-xl ${config.bg} ${config.border} border`}>
                                <Icon className="w-5 h-5" style={{ color: config.color }} />
                                <span className="font-semibold text-sm" style={{ color: config.color }}>{config.label}</span>
                                <span className="ml-auto text-xs font-mono bg-white/5 px-2 py-0.5 rounded">{devices.length}</span>
                            </div>
                            <div className={`flex-1 ${config.border} border border-t-0 rounded-b-xl p-3 space-y-2 max-h-[500px] overflow-y-auto bg-[var(--color-bg-card)]/50`}>
                                {devices.length === 0 ? (
                                    <p className="text-center text-xs text-[var(--color-text-muted)] py-6">No devices in this phase</p>
                                ) : (
                                    devices.map(d => (
                                        <Link key={d.device_id} to={`/devices/${d.device_id}`} className="block p-3 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] hover:border-[var(--color-accent)]/30 transition-colors">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-xs font-mono text-[var(--color-accent)]">{d.device_id}</span>
                                                <RiskBadge level={d.risk_level} size="sm" />
                                            </div>
                                            <p className="text-xs text-[var(--color-text-secondary)] capitalize">{d.device_type?.replace(/_/g, ' ')}</p>
                                            <div className="flex items-center gap-1 mt-2 text-[10px] text-[var(--color-text-muted)]">
                                                <span className="font-mono">{d.current_algorithm}</span>
                                                <ArrowRight className="w-3 h-3" />
                                                <span className="font-mono text-green-400">{d.target_algorithm?.substring(0, 20)}</span>
                                            </div>
                                            <div className="flex items-center justify-between mt-2">
                                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${d.estimated_effort === 'High' ? 'bg-red-500/15 text-red-400' : d.estimated_effort === 'Medium' ? 'bg-orange-500/15 text-orange-400' : 'bg-green-500/15 text-green-400'}`}>{d.estimated_effort} effort</span>
                                                <span className="text-[10px] text-[var(--color-text-muted)]">{(d.priority_score * 100).toFixed(0)}% priority</span>
                                            </div>
                                        </Link>
                                    ))
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
