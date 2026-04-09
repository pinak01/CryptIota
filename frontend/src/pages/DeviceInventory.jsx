import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Search, Upload, ChevronLeft, ChevronRight } from 'lucide-react'
import { fetchDevices } from '../api/apiClient'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const RISK_LEVELS = ['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
const DEVICE_TYPES = ['', 'environmental_sensor', 'medical_wearable', 'industrial_controller', 'smart_home', 'energy_meter', 'security_camera', 'autonomous_vehicle_sensor', 'water_treatment_sensor']
const ALGOS = ['', 'RSA-1024', 'RSA-2048', 'ECC-256', 'ECC-384', 'AES-128', 'AES-256', '3DES', 'ChaCha20', 'Kyber-512', 'Kyber-768', 'HYBRID-ECC-Kyber']
const PER_PAGE = 20

const strategyIcon = { Classical: '🔒', Hybrid: '🔀', PostQuantum: '🛡️' }

export default function DeviceInventory() {
    const navigate = useNavigate()
    const [devices, setDevices] = useState([])
    const [total, setTotal] = useState(0)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [page, setPage] = useState(0)
    const [filters, setFilters] = useState({ risk_level: '', device_type: '', algorithm: '', search: '' })
    const [migrationOverlay, setMigrationOverlay] = useState({})

    const applyMigrationUpdate = (payload) => {
        if (!payload?.device_id) return

        setMigrationOverlay(prev => ({
            ...prev,
            [payload.device_id]: payload,
        }))

        setDevices(prev => prev.map(device => {
            if (device.device_id !== payload.device_id) return device
            return {
                ...device,
                encryption_algorithm: payload.after_algorithm || device.encryption_algorithm,
                risk_assessment: device.risk_assessment ? {
                    ...device.risk_assessment,
                    risk_level: payload.risk_level || device.risk_assessment.risk_level,
                    risk_score: payload.risk_score ?? device.risk_assessment.risk_score,
                } : device.risk_assessment,
            }
        }))
    }

    const load = () => {
        setLoading(true)
        const params = { limit: PER_PAGE, offset: page * PER_PAGE }
        if (filters.risk_level) params.risk_level = filters.risk_level
        if (filters.device_type) params.device_type = filters.device_type
        if (filters.search) params.search = filters.search
        fetchDevices(params)
            .then(d => {
                const hydratedDevices = d.devices.map(device => {
                    const migration = migrationOverlay[device.device_id]
                    if (!migration) return device
                    return {
                        ...device,
                        encryption_algorithm: migration.after_algorithm || device.encryption_algorithm,
                        risk_assessment: device.risk_assessment ? {
                            ...device.risk_assessment,
                            risk_level: migration.risk_level || device.risk_assessment.risk_level,
                            risk_score: migration.risk_score ?? device.risk_assessment.risk_score,
                        } : device.risk_assessment,
                    }
                })
                setDevices(hydratedDevices)
                setTotal(d.total)
            })
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }

    useEffect(() => { load() }, [page, filters.risk_level, filters.device_type, migrationOverlay])
    useEffect(() => { const t = setTimeout(load, 300); return () => clearTimeout(t) }, [filters.search, migrationOverlay])
    useEffect(() => {
        const onMigration = (event) => applyMigrationUpdate(event.detail)
        const onStorage = (event) => {
            if (event.key !== 'quantumguard:lastMigration' || !event.newValue) return
            applyMigrationUpdate(JSON.parse(event.newValue))
        }

        const cached = window.localStorage.getItem('quantumguard:lastMigration')
        if (cached) {
            try {
                applyMigrationUpdate(JSON.parse(cached))
            } catch {
                // Ignore malformed persisted state.
            }
        }

        window.addEventListener('device-migrated', onMigration)
        window.addEventListener('storage', onStorage)
        return () => {
            window.removeEventListener('device-migrated', onMigration)
            window.removeEventListener('storage', onStorage)
        }
    }, [])

    const totalPages = Math.ceil(total / PER_PAGE)
    const updateFilter = (key, val) => { setFilters(f => ({ ...f, [key]: val })); setPage(0) }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <h1 className="text-2xl font-bold">Device Inventory</h1>
                <Link to="/upload" className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg text-sm font-medium transition-colors">
                    <Upload className="w-4 h-4" /> Upload CSV
                </Link>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-3">
                <select value={filters.risk_level} onChange={e => updateFilter('risk_level', e.target.value)} className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]">
                    <option value="">All Risk Levels</option>
                    {RISK_LEVELS.filter(Boolean).map(l => <option key={l} value={l}>{l}</option>)}
                </select>
                <select value={filters.device_type} onChange={e => updateFilter('device_type', e.target.value)} className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]">
                    <option value="">All Device Types</option>
                    {DEVICE_TYPES.filter(Boolean).map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                </select>
                <div className="relative flex-1 min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
                    <input type="text" placeholder="Search by device ID or location..." value={filters.search} onChange={e => updateFilter('search', e.target.value)} className="w-full bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg pl-10 pr-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-accent)]" />
                </div>
            </div>

            {loading ? <LoadingSpinner text="Loading devices..." /> : error ? (
                <div className="text-center py-12">
                    <p className="text-red-400">Failed to load: {error}</p>
                    <button onClick={load} className="mt-3 px-4 py-2 bg-[var(--color-accent)] rounded-lg text-sm">Retry</button>
                </div>
            ) : (
                <>
                    <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
                                    {['Device ID', 'Type', 'Location', 'Encryption', 'Sensitivity', 'Retention', 'Risk Level', 'Strategy', ''].map(h => (
                                        <th key={h} className="text-left px-4 py-3 font-medium text-[var(--color-text-secondary)]">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {devices.map(d => {
                                    const ra = d.risk_assessment
                                    const migration = migrationOverlay[d.device_id]
                                    return (
                                        <tr key={d.device_id} onClick={() => navigate(`/devices/${d.device_id}`)} className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)] cursor-pointer transition-colors">
                                            <td className="px-4 py-3 font-mono text-[var(--color-accent)]">{d.device_id}</td>
                                            <td className="px-4 py-3 text-[var(--color-text-secondary)] capitalize">{d.device_type?.replace(/_/g, ' ')}</td>
                                            <td className="px-4 py-3 text-[var(--color-text-secondary)]">{d.location}</td>
                                            <td className="px-4 py-3 font-mono text-xs">
                                                {migration?.before_algorithm && (
                                                    <p className="line-through text-[var(--color-text-muted)]">{migration.before_algorithm}</p>
                                                )}
                                                <p className={migration ? 'text-green-400' : ''}>{d.encryption_algorithm}</p>
                                            </td>
                                            <td className="px-4 py-3 text-center">{d.data_sensitivity}</td>
                                            <td className="px-4 py-3 text-center">{d.data_retention_years}y</td>
                                            <td className="px-4 py-3">{ra ? <RiskBadge level={ra.risk_level} size="sm" /> : <span className="text-[var(--color-text-muted)]">—</span>}</td>
                                            <td className="px-4 py-3">{ra ? <span className="text-xs">{strategyIcon[ra.recommended_strategy] || ''} {ra.recommended_strategy}</span> : '—'}</td>
                                            <td className="px-4 py-3">
                                                <Link to={`/devices/${d.device_id}`} className="text-xs text-[var(--color-accent)] hover:underline" onClick={e => e.stopPropagation()}>Details</Link>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-[var(--color-text-secondary)]">
                            Showing {page * PER_PAGE + 1}–{Math.min((page + 1) * PER_PAGE, total)} of {total}
                        </p>
                        <div className="flex gap-2">
                            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="p-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] disabled:opacity-30 hover:bg-white/5 transition-colors">
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <span className="flex items-center px-3 text-sm text-[var(--color-text-secondary)]">{page + 1} / {totalPages || 1}</span>
                            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="p-2 rounded-lg bg-[var(--color-bg-card)] border border-[var(--color-border)] disabled:opacity-30 hover:bg-white/5 transition-colors">
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
