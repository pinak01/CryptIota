import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
    ArrowLeft, Shield, AlertTriangle, GitBranch, Clock, Cpu, HardDrive, Wifi,
    Battery, RotateCcw, Terminal, CheckCircle2, Loader2, X, ArrowRight,
} from 'lucide-react'
import {
    fetchBenchmarkHistory,
    fetchDevice,
    fetchMigrationStatus,
    startDeviceMigration,
} from '../api/apiClient'
import RiskBadge from '../components/RiskBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const FALLBACK_MIGRATION_OPTIONS = [
    { value: 'Kyber512', label: 'Kyber512' },
    { value: 'Kyber768', label: 'Kyber768' },
    { value: 'Dilithium3', label: 'Dilithium3' },
    { value: 'Falcon-512', label: 'Falcon-512' },
]

const OPTION_LABEL_MAP = {
    'Kyber-512': 'Kyber512',
    Kyber512: 'Kyber512',
    'Kyber-768': 'Kyber768',
    Kyber768: 'Kyber768',
    Dilithium3: 'Dilithium3',
    'Falcon-512': 'Falcon-512',
}

function formatLogTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    })
}

function getMigrationOptions(history) {
    const latestRun = history?.runs?.[0] || []
    const seen = new Set()
    const options = []

    latestRun.forEach(entry => {
        const label = OPTION_LABEL_MAP[entry.algorithm] || OPTION_LABEL_MAP[entry.variant]
        if (label && !seen.has(label)) {
            seen.add(label)
            options.push({ value: label, label })
        }
    })

    if (!options.length) {
        return FALLBACK_MIGRATION_OPTIONS
    }

    FALLBACK_MIGRATION_OPTIONS.forEach(option => {
        if (!seen.has(option.value)) {
            options.push(option)
        }
    })

    return options
}

function emitMigrationUpdate(payload) {
    const enriched = { ...payload, migrated_at: new Date().toISOString() }
    window.localStorage.setItem('quantumguard:lastMigration', JSON.stringify(enriched))
    window.dispatchEvent(new CustomEvent('device-migrated', { detail: enriched }))
}

export default function DeviceDetail() {
    const { id } = useParams()
    const [device, setDevice] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [showModal, setShowModal] = useState(false)
    const [migrationOptions, setMigrationOptions] = useState(FALLBACK_MIGRATION_OPTIONS)
    const [optionsLoading, setOptionsLoading] = useState(false)
    const [selectedAlgorithm, setSelectedAlgorithm] = useState('Kyber768')
    const [migrationState, setMigrationState] = useState(null)
    const [migrationError, setMigrationError] = useState(null)
    const [startingMigration, setStartingMigration] = useState(false)
    const [pageSuccess, setPageSuccess] = useState(null)
    const handledJobs = useRef(new Set())

    const loadDevice = async () => {
        setLoading(true)
        setError(null)
        try {
            const data = await fetchDevice(id)
            setDevice(data)
            return data
        } catch (e) {
            setError(e.message)
            return null
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadDevice()
    }, [id])

    useEffect(() => {
        if (!showModal) return

        setOptionsLoading(true)
        fetchBenchmarkHistory()
            .then(history => {
                const options = getMigrationOptions(history)
                setMigrationOptions(options)
                if (!options.some(option => option.value === selectedAlgorithm)) {
                    setSelectedAlgorithm(options[0]?.value || 'Kyber768')
                }
            })
            .catch(() => {
                setMigrationOptions(FALLBACK_MIGRATION_OPTIONS)
            })
            .finally(() => setOptionsLoading(false))
    }, [showModal])

    useEffect(() => {
        const activeJobId = migrationState?.job_id
        const activeStatus = migrationState?.status
        if (!activeJobId || !['queued', 'running'].includes(activeStatus)) {
            return undefined
        }

        const poll = async () => {
            try {
                const status = await fetchMigrationStatus(activeJobId)
                setMigrationState(status)
            } catch (e) {
                setMigrationError(e.message)
            }
        }

        poll()
        const intervalId = window.setInterval(poll, 500)
        return () => window.clearInterval(intervalId)
    }, [migrationState?.job_id, migrationState?.status])

    useEffect(() => {
        if (!migrationState || migrationState.status !== 'completed') return
        if (handledJobs.current.has(migrationState.job_id)) return

        handledJobs.current.add(migrationState.job_id)
        loadDevice().then(freshDevice => {
            const latestAssessment = freshDevice?.risk_assessments?.[0]
            const successPayload = {
                device_id: migrationState.result?.device_id || id,
                before_algorithm: migrationState.result?.before_algorithm,
                after_algorithm: migrationState.result?.after_algorithm,
                risk_level: migrationState.result?.risk_level || latestAssessment?.risk_level,
                risk_score: migrationState.result?.risk_score ?? latestAssessment?.risk_score,
            }
            setPageSuccess(successPayload)
            emitMigrationUpdate(successPayload)
        })
    }, [migrationState, id])

    if (loading) return <LoadingSpinner text={`Loading ${id}...`} />
    if (error) return <div className="text-center py-20 text-red-400">Error: {error}</div>
    if (!device) return null

    const ra = device.risk_assessments?.[0]
    const plan = device.migration_plan
    const confidence = ra?.confidence_scores || (device.risk_assessments?.length > 0 ? {} : null)
    const riskPct = Math.round((ra?.risk_score || 0) * 100)
    const gaugeColor = riskPct >= 75 ? '#ef4444' : riskPct >= 50 ? '#f97316' : riskPct >= 25 ? '#eab308' : '#22c55e'
    const canMigrate = ['HIGH', 'CRITICAL'].includes(ra?.risk_level)
    const confidenceData = confidence ? Object.entries(confidence).map(([k, v]) => ({ name: k, value: v })) : []
    const confColors = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' }
    const sensitivityLabels = ['Public', 'Internal', 'Confidential', 'Sensitive', 'Critical']
    const infoItems = [
        { icon: Cpu, label: 'CPU', value: `${device.cpu_mhz} MHz` },
        { icon: HardDrive, label: 'RAM', value: `${device.ram_kb} KB` },
        { icon: Wifi, label: 'Network', value: device.network_exposure ? 'Internet-facing' : 'Isolated' },
        { icon: Battery, label: 'Power', value: device.battery_powered ? 'Battery' : 'Mains' },
        { icon: RotateCcw, label: 'Key Rotation', value: `${device.key_rotation_days} days` },
        { icon: Clock, label: 'Deployment Age', value: `${device.deployment_age_years} years` },
    ]
    const visibleLogs = migrationState?.logs || []
    const migrationProgress = migrationState?.progress || 0
    const migrationComplete = migrationState?.status === 'completed'
    const migrationFailed = migrationState?.status === 'failed'
    const latestRiskScore = pageSuccess?.risk_score ?? ra?.risk_score
    const latestRiskPct = latestRiskScore != null ? Math.round(latestRiskScore * 100) : null
    const migratedAlgorithm = pageSuccess?.after_algorithm || device.encryption_algorithm
    const previousAlgorithm = pageSuccess?.before_algorithm

    const handleStartMigration = async () => {
        setStartingMigration(true)
        setMigrationError(null)
        setPageSuccess(null)

        try {
            const job = await startDeviceMigration(device.device_id, { target_algorithm: selectedAlgorithm })
            setMigrationState({
                ...job,
                progress: 0,
                stage: 'Queued',
                logs: [{
                    timestamp: new Date().toISOString(),
                    stage_number: 0,
                    stage_label: 'Queued',
                    progress: 0,
                    message: `Queued OTA migration from ${device.encryption_algorithm} to ${selectedAlgorithm}`,
                }],
            })
        } catch (e) {
            setMigrationError(e.response?.data?.error || e.message)
        } finally {
            setStartingMigration(false)
        }
    }

    return (
        <>
            <div className="space-y-6 animate-fade-in">
                <div className="flex items-center justify-between gap-3 flex-wrap">
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

                    {canMigrate && (
                        <button
                            onClick={() => setShowModal(true)}
                            className="px-4 py-2 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white text-sm font-medium transition-colors"
                        >
                            Migrate Device
                        </button>
                    )}
                </div>

                {pageSuccess && (
                    <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-4 animate-fade-in">
                        <div className="flex items-start gap-3">
                            <CheckCircle2 className="w-5 h-5 text-green-400 mt-0.5" />
                            <div className="space-y-1">
                                <p className="font-semibold text-green-300">Migration Successful</p>
                                <p className="text-sm text-green-100/90 flex items-center gap-2 flex-wrap">
                                    <span className="line-through opacity-70">{pageSuccess.before_algorithm}</span>
                                    <ArrowRight className="w-4 h-4" />
                                    <span className="font-mono text-green-300">{pageSuccess.after_algorithm}</span>
                                </p>
                                {latestRiskPct != null && (
                                    <p className="text-sm text-[var(--color-text-secondary)]">
                                        Updated risk score: <span className="font-semibold text-green-300">{latestRiskPct}%</span>
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-6">
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Shield className="w-5 h-5 text-[var(--color-accent)]" /> Device Profile</h2>
                            <div className="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
                                <div><span className="text-[var(--color-text-muted)]">Type</span><p className="font-medium capitalize">{device.device_type?.replace(/_/g, ' ')}</p></div>
                                <div>
                                    <span className="text-[var(--color-text-muted)]">Algorithm</span>
                                    {previousAlgorithm ? (
                                        <div className="space-y-1">
                                            <p className="font-mono text-xs line-through text-[var(--color-text-muted)]">{previousAlgorithm}</p>
                                            <p className="font-mono font-medium text-green-400">{migratedAlgorithm}</p>
                                        </div>
                                    ) : (
                                        <p className="font-mono font-medium">{device.encryption_algorithm}</p>
                                    )}
                                </div>
                                <div><span className="text-[var(--color-text-muted)]">Sensitivity</span><p className="font-medium">{sensitivityLabels[device.data_sensitivity]} ({device.data_sensitivity})</p></div>
                                <div><span className="text-[var(--color-text-muted)]">Retention</span><p className="font-medium">{device.data_retention_years} years</p></div>
                                <div><span className="text-[var(--color-text-muted)]">Update Capable</span><p className="font-medium">{device.update_capable ? 'Yes' : 'No'}</p></div>
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

                        {ra && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-[var(--color-bg-card)] border-2 border-red-500/30 rounded-xl p-4">
                                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Current Algorithm</p>
                                    {previousAlgorithm ? (
                                        <div className="space-y-1">
                                            <p className="font-mono text-xs line-through text-red-300/70">{previousAlgorithm}</p>
                                            <p className="font-mono font-semibold text-green-400">{migratedAlgorithm}</p>
                                        </div>
                                    ) : (
                                        <p className="font-mono font-semibold text-red-400">{device.encryption_algorithm}</p>
                                    )}
                                    <p className="text-xs mt-1 text-[var(--color-text-secondary)]">
                                        {previousAlgorithm ? 'Updated in live device profile' : 'Current production crypto stack'}
                                    </p>
                                </div>
                                <div className="bg-[var(--color-bg-card)] border-2 border-green-500/30 rounded-xl p-4">
                                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Recommended</p>
                                    <p className="font-mono font-semibold text-green-400">{ra.recommended_algorithm}</p>
                                    <p className="text-xs text-green-400/70 mt-1">Quantum resistant target</p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="space-y-6">
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

                        {plan && (
                            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><GitBranch className="w-5 h-5 text-[var(--color-accent)]" /> Migration Plan</h2>
                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Phase</span><span className="font-medium">{plan.migration_phase}</span></div>
                                    <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Target</span><span className="font-mono">{plan.target_algorithm}</span></div>
                                    <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Effort</span><span className="font-medium">{plan.estimated_effort}</span></div>
                                    <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Priority</span><span className="font-medium">{(plan.priority_score * 100).toFixed(0)}%</span></div>
                                    <div className="flex justify-between">
                                        <span className="text-[var(--color-text-muted)]">Status</span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${plan.status === 'Complete' ? 'bg-green-500/15 text-green-400' : plan.status === 'InProgress' ? 'bg-blue-500/15 text-blue-400' : plan.status === 'Failed' ? 'bg-red-500/15 text-red-400' : 'bg-orange-500/15 text-orange-400'}`}>{plan.status}</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {ra && (
                            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                                <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-[var(--color-medium)]" /> Risk Analysis</h2>
                                <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{ra.reasoning}</p>
                            </div>
                        )}

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

            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
                    <div className="w-full max-w-4xl rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-primary)] shadow-2xl overflow-hidden animate-fade-in">
                        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
                            <div>
                                <h2 className="text-xl font-semibold">Migrate Device</h2>
                                <p className="text-sm text-[var(--color-text-secondary)]">Simulate an OTA post-quantum crypto rollout for {device.device_id}</p>
                            </div>
                            <button
                                onClick={() => setShowModal(false)}
                                className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                            >
                                <X className="w-5 h-5 text-[var(--color-text-secondary)]" />
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            {!migrationState && (
                                <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4 items-end">
                                    <div className="space-y-2">
                                        <label className="block text-sm text-[var(--color-text-secondary)]">Target Algorithm</label>
                                        <select
                                            value={selectedAlgorithm}
                                            onChange={e => setSelectedAlgorithm(e.target.value)}
                                            className="w-full bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-lg px-3 py-3 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]"
                                        >
                                            {migrationOptions.map(option => (
                                                <option key={option.value} value={option.value}>{option.label}</option>
                                            ))}
                                        </select>
                                        <p className="text-xs text-[var(--color-text-muted)]">
                                            {optionsLoading ? 'Loading supported PQC targets from benchmark history...' : 'Options are sourced from existing benchmark data when available.'}
                                        </p>
                                    </div>
                                    <button
                                        onClick={handleStartMigration}
                                        disabled={startingMigration}
                                        className="px-5 py-3 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] disabled:opacity-60 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
                                    >
                                        {startingMigration ? <Loader2 className="w-4 h-4 animate-spin" /> : <Terminal className="w-4 h-4" />}
                                        Start Migration
                                    </button>
                                </div>
                            )}

                            {migrationError && (
                                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
                                    {migrationError}
                                </div>
                            )}

                            {migrationState && (
                                <div className="space-y-5">
                                    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] p-5">
                                        <div className="flex items-center justify-between gap-3 mb-3">
                                            <div>
                                                <p className="text-sm text-[var(--color-text-secondary)]">Current Stage</p>
                                                <p className="font-semibold">{migrationState.stage}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-sm text-[var(--color-text-secondary)]">Progress</p>
                                                <p className="font-mono text-lg">{migrationProgress}%</p>
                                            </div>
                                        </div>
                                        <div className="h-3 rounded-full bg-slate-800 overflow-hidden">
                                            <div
                                                className="h-full rounded-full bg-gradient-to-r from-cyan-500 via-blue-500 to-green-400 transition-all duration-500"
                                                style={{ width: `${migrationProgress}%` }}
                                            />
                                        </div>
                                        {migrationComplete && (
                                            <div className="mt-4 rounded-lg border border-green-500/30 bg-green-500/10 p-4">
                                                <p className="font-semibold text-green-300 flex items-center gap-2">
                                                    <CheckCircle2 className="w-4 h-4" />
                                                    Migration Successful
                                                </p>
                                                <p className="text-sm text-[var(--color-text-secondary)] mt-1 flex items-center gap-2 flex-wrap">
                                                    <span className="line-through">{migrationState.result?.before_algorithm}</span>
                                                    <ArrowRight className="w-4 h-4" />
                                                    <span className="font-mono text-green-300">{migrationState.result?.after_algorithm}</span>
                                                </p>
                                                {latestRiskPct != null && (
                                                    <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                                                        Updated risk score: <span className="font-semibold text-green-300">{latestRiskPct}%</span>
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                        {migrationFailed && (
                                            <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                                                {migrationState.error || 'Migration job failed.'}
                                            </div>
                                        )}
                                    </div>

                                    <div className="rounded-xl border border-[var(--color-border)] bg-[#020617] overflow-hidden">
                                        <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--color-border)] bg-slate-900/80">
                                            <Terminal className="w-4 h-4 text-cyan-400" />
                                            <span className="text-sm font-medium">Device Console</span>
                                        </div>
                                        <div className="max-h-[360px] overflow-y-auto px-4 py-3 font-mono text-xs space-y-2">
                                            {visibleLogs.map((log, index) => (
                                                <div key={`${log.timestamp}-${index}`} className="animate-fade-in">
                                                    <p className="text-slate-400">
                                                        [{formatLogTime(log.timestamp)}] <span className="text-cyan-400">stage-{log.stage_number || 0}</span>
                                                    </p>
                                                    <p className="text-slate-100">{log.message}</p>
                                                    {log.metrics && (
                                                        <pre className="mt-1 text-[11px] text-green-300 whitespace-pre-wrap break-words">
                                                            {JSON.stringify(log.metrics, null, 2)}
                                                        </pre>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
