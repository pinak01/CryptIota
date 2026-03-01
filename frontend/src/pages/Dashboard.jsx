import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Server, AlertTriangle, GitBranch, ShieldCheck, CheckCircle } from 'lucide-react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { fetchDashboardSummary, acknowledgeAlert } from '../api/apiClient'
import StatCard from '../components/StatCard'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const RISK_COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' }

export default function Dashboard() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const load = () => {
        setLoading(true)
        fetchDashboardSummary()
            .then(setData)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }

    useEffect(() => { load() }, [])

    if (loading) return <LoadingSpinner text="Loading dashboard..." />
    if (error) return (
        <div className="text-center py-20">
            <p className="text-red-400 mb-4">Failed to load dashboard: {error}</p>
            <button onClick={load} className="px-4 py-2 bg-[var(--color-accent)] rounded-lg text-sm">Retry</button>
        </div>
    )
    if (!data) return null

    const pieData = Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }))
    const migrationPie = [
        { name: 'Pending', value: data.migration_progress.pending, color: '#f97316' },
        { name: 'In Progress', value: data.migration_progress.in_progress, color: '#3b82f6' },
        { name: 'Complete', value: data.migration_progress.complete, color: '#22c55e' },
    ]
    const barData = (data.top_vulnerable_device_types || []).map(t => ({
        name: t.device_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).substring(0, 15),
        risk: Math.round(t.avg_risk * 100),
        count: t.count,
    }))

    const handleAck = async (id) => {
        try {
            await acknowledgeAlert(id)
            load()
        } catch { }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <h1 className="text-2xl font-bold">Dashboard</h1>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={Server} value={data.total_devices} label="Total Devices" color="blue" />
                <StatCard icon={AlertTriangle} value={data.risk_distribution.CRITICAL} label="Critical Risk" color="red" pulse={data.risk_distribution.CRITICAL > 0} />
                <StatCard icon={GitBranch} value={data.devices_needing_immediate_action} label="Migrations Needed" color="orange" />
                <StatCard icon={ShieldCheck} value={data.risk_distribution.LOW} label="Protected Devices" color="green" />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Risk Distribution Pie */}
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Risk Distribution</h2>
                    <ResponsiveContainer width="100%" height={260}>
                        <PieChart>
                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                                {pieData.map(entry => (
                                    <Cell key={entry.name} fill={RISK_COLORS[entry.name]} stroke="transparent" />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Top Device Types Bar */}
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Top Device Types by Risk</h2>
                    <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={barData} barCategoryGap="20%">
                            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
                            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                            <Bar dataKey="risk" name="Risk Score" fill="#f97316" radius={[6, 6, 0, 0]} />
                            <Bar dataKey="count" name="Device Count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Alerts */}
            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                <h2 className="text-lg font-semibold mb-4">Active Alerts</h2>
                {data.recent_alerts.length === 0 ? (
                    <div className="flex items-center gap-3 text-[var(--color-low)] py-6 justify-center">
                        <CheckCircle className="w-6 h-6" />
                        <span className="text-lg font-medium">All Clear — No Active Alerts</span>
                    </div>
                ) : (
                    <div className="space-y-3 max-h-80 overflow-y-auto">
                        {data.recent_alerts.map(alert => (
                            <div key={alert.id} className={`flex items-start gap-3 p-3 rounded-lg border ${alert.severity === 'CRITICAL' ? 'bg-red-500/5 border-red-500/20' : 'bg-orange-500/5 border-orange-500/20'}`}>
                                <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${alert.severity === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'}`} />
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <RiskBadge level={alert.severity} size="sm" />
                                        <Link to={`/devices/${alert.device_id}`} className="text-sm font-mono text-[var(--color-accent)] hover:underline">{alert.device_id}</Link>
                                    </div>
                                    <p className="text-sm text-[var(--color-text-secondary)] mt-1">{alert.message}</p>
                                    <p className="text-xs text-[var(--color-text-muted)] mt-1">{new Date(alert.created_at).toLocaleString()}</p>
                                </div>
                                <button onClick={() => handleAck(alert.id)} className="px-3 py-1.5 text-xs rounded-lg bg-white/5 hover:bg-white/10 border border-[var(--color-border)] shrink-0 transition-colors">Acknowledge</button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Devices */}
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Recent Assessments</h2>
                    <p className="text-sm text-[var(--color-text-secondary)]">
                        Last assessment: {data.last_assessment_time ? new Date(data.last_assessment_time).toLocaleString() : 'N/A'}
                    </p>
                    <p className="text-sm text-[var(--color-text-secondary)] mt-2">
                        Average risk score: <span className="font-semibold text-[var(--color-text-primary)]">{(data.avg_risk_score * 100).toFixed(1)}%</span>
                    </p>
                    <Link to="/devices" className="inline-block mt-4 text-sm text-[var(--color-accent)] hover:underline">
                        View all devices →
                    </Link>
                </div>

                {/* Migration Progress */}
                <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                    <h2 className="text-lg font-semibold mb-4">Migration Progress</h2>
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie data={migrationPie} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                                {migrationPie.map(entry => (
                                    <Cell key={entry.name} fill={entry.color} stroke="transparent" />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}
