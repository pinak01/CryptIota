import { useState, useEffect } from 'react'
import { Tooltip as RechartsTooltip } from 'recharts'
import { fetchDevices } from '../api/apiClient'
import LoadingSpinner from '../components/LoadingSpinner'

const DEVICE_TYPES = ['environmental_sensor', 'medical_wearable', 'industrial_controller', 'smart_home', 'energy_meter', 'security_camera', 'autonomous_vehicle_sensor', 'water_treatment_sensor']
const SENSITIVITY_LEVELS = [0, 1, 2, 3, 4]
const SENS_LABELS = ['Public', 'Internal', 'Confidential', 'Sensitive', 'Critical']
const RISK_COLORS = { CRITICAL: '#ef4444', HIGH: '#f97316', MEDIUM: '#eab308', LOW: '#22c55e', NONE: '#334155' }

export default function RiskHeatmap() {
    const [heatData, setHeatData] = useState({})
    const [loading, setLoading] = useState(true)
    const [hoveredCell, setHoveredCell] = useState(null)

    useEffect(() => {
        fetchDevices({ limit: 999 })
            .then(data => {
                const grid = {}
                for (const dev of data.devices) {
                    const key = `${dev.device_type}__${dev.data_sensitivity}`
                    if (!grid[key]) grid[key] = { count: 0, risks: [], scores: [] }
                    grid[key].count++
                    const rl = dev.risk_assessment?.risk_level
                    if (rl) grid[key].risks.push(rl)
                    if (dev.risk_assessment?.risk_score) grid[key].scores.push(dev.risk_assessment.risk_score)
                }
                setHeatData(grid)
            })
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [])

    if (loading) return <LoadingSpinner text="Building heatmap..." />

    const getDominantRisk = (risks) => {
        if (!risks?.length) return 'NONE'
        const order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        for (const r of order) { if (risks.includes(r)) return r }
        return 'LOW'
    }

    // Find top 3 hotspots
    const allCells = Object.entries(heatData)
        .map(([key, val]) => ({ key, ...val, dominant: getDominantRisk(val.risks), avgScore: val.scores.length ? val.scores.reduce((a, b) => a + b) / val.scores.length : 0 }))
        .sort((a, b) => b.avgScore - a.avgScore)
    const hotspots = allCells.filter(c => c.dominant !== 'NONE').slice(0, 3)

    return (
        <div className="space-y-6 animate-fade-in">
            <h1 className="text-2xl font-bold">Quantum Risk Landscape</h1>

            {/* Heatmap Grid */}
            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6 overflow-x-auto">
                <div className="min-w-[700px]">
                    {/* Header */}
                    <div className="grid gap-1" style={{ gridTemplateColumns: '120px repeat(8, 1fr)' }}>
                        <div />
                        {DEVICE_TYPES.map(dt => (
                            <div key={dt} className="text-[10px] text-[var(--color-text-muted)] text-center px-1 leading-tight">
                                {dt.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()).substring(0, 12)}
                            </div>
                        ))}
                    </div>

                    {/* Rows */}
                    {SENSITIVITY_LEVELS.map(sens => (
                        <div key={sens} className="grid gap-1 mt-1" style={{ gridTemplateColumns: '120px repeat(8, 1fr)' }}>
                            <div className="text-xs text-[var(--color-text-muted)] flex items-center">{SENS_LABELS[sens]} ({sens})</div>
                            {DEVICE_TYPES.map(dt => {
                                const key = `${dt}__${sens}`
                                const cell = heatData[key]
                                const dominant = cell ? getDominantRisk(cell.risks) : 'NONE'
                                const count = cell?.count || 0
                                const avgScore = cell && cell.scores.length ? (cell.scores.reduce((a, b) => a + b) / cell.scores.length * 100).toFixed(0) : 0
                                const isHovered = hoveredCell === key

                                return (
                                    <div
                                        key={key}
                                        onMouseEnter={() => setHoveredCell(key)}
                                        onMouseLeave={() => setHoveredCell(null)}
                                        className="relative aspect-square rounded-lg flex flex-col items-center justify-center text-xs transition-all cursor-default"
                                        style={{
                                            backgroundColor: count > 0 ? RISK_COLORS[dominant] + '30' : RISK_COLORS.NONE,
                                            border: `2px solid ${count > 0 ? RISK_COLORS[dominant] + '60' : 'transparent'}`,
                                            transform: isHovered ? 'scale(1.08)' : 'scale(1)',
                                            zIndex: isHovered ? 10 : 1,
                                        }}
                                    >
                                        <span className="font-bold text-base" style={{ color: RISK_COLORS[dominant] }}>{count}</span>
                                        {count > 0 && <span className="text-[9px] text-[var(--color-text-muted)]">{avgScore}%</span>}
                                        {isHovered && count > 0 && (
                                            <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-2 text-[10px] w-36 z-50 shadow-xl">
                                                <p className="font-medium">{count} devices</p>
                                                <p className="text-[var(--color-text-muted)]">Avg risk: {avgScore}%</p>
                                                <p className="text-[var(--color-text-muted)]">Dominant: {dominant}</p>
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    ))}
                </div>

                {/* Legend */}
                <div className="flex items-center gap-4 mt-6 justify-center">
                    {Object.entries(RISK_COLORS).filter(([k]) => k !== 'NONE').map(([label, color]) => (
                        <div key={label} className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded" style={{ backgroundColor: color + '50', border: `1px solid ${color}` }} />
                            <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Risk Hotspots */}
            <div>
                <h2 className="text-lg font-semibold mb-3">Risk Hotspots</h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {hotspots.map((h, i) => {
                        const [dtype, sens] = h.key.split('__')
                        return (
                            <div key={h.key} className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-4 relative overflow-hidden">
                                <div className="absolute top-2 right-2 w-8 h-8 flex items-center justify-center rounded-full bg-white/5 text-sm font-bold text-[var(--color-text-muted)]">#{i + 1}</div>
                                <p className="text-sm font-semibold capitalize">{dtype.replace(/_/g, ' ')}</p>
                                <p className="text-xs text-[var(--color-text-muted)]">{SENS_LABELS[parseInt(sens)]} data</p>
                                <div className="mt-3 flex items-center gap-2">
                                    <span className="text-2xl font-bold" style={{ color: RISK_COLORS[h.dominant] }}>{h.count}</span>
                                    <span className="text-xs text-[var(--color-text-muted)]">devices at {(h.avgScore * 100).toFixed(0)}% avg risk</span>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
