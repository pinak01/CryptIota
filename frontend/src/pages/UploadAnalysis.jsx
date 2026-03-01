import { useState, useRef } from 'react'
import { Upload, FileText, Download, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { uploadCSV } from '../api/apiClient'
import RiskBadge from '../components/RiskBadge'

const RISK_COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' }

const SAMPLE_CSV = `device_id,device_type,encryption_algorithm,data_sensitivity,data_retention_years,network_exposure,update_capable,battery_powered,cpu_mhz,ram_kb,key_rotation_days,deployment_age_years,num_connected_devices,data_volume_mb_per_day
SAMPLE-001,medical_wearable,RSA-1024,4,15,1,0,1,160,256,365,6,12,5.2
SAMPLE-002,industrial_controller,AES-256,2,5,0,1,0,1500,8192,30,3,50,200.0
SAMPLE-003,smart_home,ECC-256,1,2,1,1,0,240,512,60,2,15,8.0
SAMPLE-004,energy_meter,3DES,3,10,1,0,0,240,256,365,8,100,45.0
SAMPLE-005,security_camera,Kyber-512,1,3,1,1,0,1200,4096,30,1,20,500.0`

export default function UploadAnalysis() {
    const fileRef = useRef(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    const handleFile = (file) => {
        if (!file || !file.name.endsWith('.csv')) {
            setError('Please upload a CSV file.')
            return
        }
        setUploading(true)
        setError(null)
        setResult(null)
        uploadCSV(file)
            .then(setResult)
            .catch(e => setError(e.response?.data?.error || e.message))
            .finally(() => setUploading(false))
    }

    const handleDrop = (e) => {
        e.preventDefault(); setDragOver(false)
        const file = e.dataTransfer.files[0]
        handleFile(file)
    }

    const downloadSample = () => {
        const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url; a.download = 'sample_devices.csv'; a.click()
        URL.revokeObjectURL(url)
    }

    const downloadResults = () => {
        if (!result) return
        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url; a.download = 'analysis_results.json'; a.click()
        URL.revokeObjectURL(url)
    }

    const pieData = result ? Object.entries(result.risk_distribution).map(([name, value]) => ({ name, value })).filter(d => d.value > 0) : []

    return (
        <div className="space-y-6 animate-fade-in">
            <h1 className="text-2xl font-bold">Upload & Analysis</h1>

            {/* Upload Zone */}
            <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`relative cursor-pointer border-2 border-dashed rounded-2xl p-12 text-center transition-all ${dragOver ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/5' : 'border-[var(--color-border)] hover:border-[var(--color-accent)]/50 hover:bg-white/[0.02]'}`}
            >
                <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={e => handleFile(e.target.files[0])} />
                {uploading ? (
                    <div className="flex flex-col items-center gap-4">
                        <Loader2 className="w-12 h-12 text-[var(--color-accent)] animate-spin" />
                        <p className="text-lg font-medium">Analyzing devices...</p>
                        <p className="text-sm text-[var(--color-text-muted)]">Running ML classification on each device</p>
                    </div>
                ) : (
                    <>
                        <Upload className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                        <p className="text-lg font-medium mb-1">Drop your IoT device CSV here</p>
                        <p className="text-sm text-[var(--color-text-muted)]">or click to browse</p>
                        <p className="text-xs text-[var(--color-text-muted)] mt-4">
                            Required columns: device_id, device_type, encryption_algorithm, data_sensitivity, data_retention_years,
                            network_exposure, update_capable, battery_powered, cpu_mhz, ram_kb, key_rotation_days,
                            deployment_age_years, num_connected_devices, data_volume_mb_per_day
                        </p>
                    </>
                )}
            </div>

            {/* Download Sample + Error */}
            <div className="flex items-center gap-4">
                <button onClick={downloadSample} className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-[var(--color-border)] rounded-lg text-sm transition-colors">
                    <Download className="w-4 h-4" /> Download Sample CSV
                </button>
                {error && <p className="text-red-400 text-sm flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> {error}</p>}
            </div>

            {/* Results */}
            {result && (
                <div className="space-y-6 animate-fade-in">
                    {/* Summary Bar */}
                    <div className="flex flex-wrap gap-4 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                        <div className="flex items-center gap-2">
                            <CheckCircle className="w-5 h-5 text-green-400" />
                            <span className="text-sm"><strong>{result.total_rows}</strong> devices analyzed</span>
                        </div>
                        <div className="flex items-center gap-3 ml-auto flex-wrap">
                            {Object.entries(result.risk_distribution).map(([level, count]) => (
                                <div key={level} className="flex items-center gap-1.5">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: RISK_COLORS[level] }} />
                                    <span className="text-sm">{count} {level}</span>
                                </div>
                            ))}
                        </div>
                        <span className="text-xs text-[var(--color-text-muted)]">
                            ⏱ {result.processing_time_ms?.toFixed(0)} ms
                        </span>
                    </div>

                    {/* Pie + Table */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                            <h3 className="text-sm font-semibold mb-3">Risk Distribution</h3>
                            <ResponsiveContainer width="100%" height={220}>
                                <PieChart>
                                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                                        {pieData.map(e => <Cell key={e.name} fill={RISK_COLORS[e.name]} stroke="transparent" />)}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>

                        <div className="lg:col-span-2 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[var(--color-border)]">
                                        {['Device ID', 'Risk', 'Score', 'Strategy', 'Recommended'].map(h => (
                                            <th key={h} className="text-left px-4 py-3 font-medium text-[var(--color-text-secondary)]">{h}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {(result.results || []).slice(0, 50).map((r, i) => (
                                        <tr key={i} className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-card-hover)]">
                                            <td className="px-4 py-2 font-mono text-xs">{r.device_id}</td>
                                            <td className="px-4 py-2">{r.risk_level ? <RiskBadge level={r.risk_level} size="sm" /> : <span className="text-red-400 text-xs">{r.error?.substring(0, 40)}</span>}</td>
                                            <td className="px-4 py-2 font-mono text-xs">{r.risk_score?.toFixed(3)}</td>
                                            <td className="px-4 py-2 text-xs">{r.strategy}</td>
                                            <td className="px-4 py-2 font-mono text-xs">{r.recommended_algorithm?.substring(0, 25)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <button onClick={downloadResults} className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg text-sm font-medium transition-colors">
                        <Download className="w-4 h-4" /> Download Report
                    </button>
                </div>
            )}
        </div>
    )
}
