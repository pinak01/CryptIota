import { useState, useEffect } from 'react'
import { Play, RefreshCw, ShieldCheck, ShieldAlert, ShieldQuestion, Loader2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts'
import { runBenchmark, runCryptoDemo } from '../api/apiClient'
import LoadingSpinner from '../components/LoadingSpinner'

const ALGO_OPTIONS = [
    { value: 'rsa-2048', label: 'RSA-2048' },
    { value: 'rsa-1024', label: 'RSA-1024' },
    { value: 'ecc-256', label: 'ECC-P256' },
    { value: 'aes-256', label: 'AES-256-GCM' },
    { value: 'kyber-512', label: 'Kyber-512' },
    { value: 'kyber-768', label: 'Kyber-768' },
    { value: 'dilithium-2', label: 'Dilithium-2' },
    { value: 'hybrid', label: 'Hybrid (ECDH+Kyber)' },
]

const tooltipStyle = { backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f1f5f9' }

export default function BenchmarkPage() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [demoAlgo, setDemoAlgo] = useState('kyber-512')
    const [demoResult, setDemoResult] = useState(null)
    const [demoLoading, setDemoLoading] = useState(false)

    const runBench = () => {
        setLoading(true)
        setError(null)
        runBenchmark(30)
            .then(setData)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }

    const tryDemo = () => {
        setDemoLoading(true)
        setDemoResult(null)
        runCryptoDemo(demoAlgo)
            .then(setDemoResult)
            .catch(e => setDemoResult({ error: e.message }))
            .finally(() => setDemoLoading(false))
    }

    // Prepare chart data
    const keygenData = data?.details?.map(d => ({ name: d.algorithm?.substring(0, 12), ms: d.avg_keygen_ms, safe: d.quantum_safe })) || []
    const encData = data?.details?.map(d => ({ name: d.algorithm?.substring(0, 12), ms: d.avg_encrypt_ms, safe: d.quantum_safe })) || []
    const sizeData = data?.details?.map(d => ({ name: d.algorithm?.substring(0, 12), key: d.key_size_bytes || 0, ct: d.ciphertext_overhead_bytes || 0, safe: d.quantum_safe })) || []

    const getRowTint = (qSafe) => qSafe ? 'bg-green-500/5' : 'bg-red-500/5'

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <h1 className="text-2xl font-bold">Cryptographic Benchmarks</h1>
                <button onClick={runBench} disabled={loading} className="flex items-center gap-2 px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    {loading ? 'Running...' : 'Run Benchmark'}
                </button>
            </div>

            {loading && <LoadingSpinner text="Benchmarking all algorithms (this may take a minute)..." />}
            {error && <div className="text-red-400 bg-red-500/10 p-4 rounded-xl">Error: {error}</div>}

            {data && (
                <>
                    {/* Comparison Table */}
                    <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-[var(--color-border)]">
                                    {['Algorithm', 'Type', 'Quantum Safe', 'Key Size', 'Ciphertext', 'Keygen (ms)', 'Encrypt (ms)', 'Decrypt (ms)'].map(h => (
                                        <th key={h} className="text-left px-4 py-3 font-medium text-[var(--color-text-secondary)]">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {(data.details || []).map((d, i) => (
                                    <tr key={i} className={`border-b border-[var(--color-border)] ${getRowTint(d.quantum_safe)}`}>
                                        <td className="px-4 py-3 font-mono font-medium">{d.algorithm}</td>
                                        <td className="px-4 py-3 text-[var(--color-text-secondary)]">{d.quantum_safe ? 'PQC' : 'Classical'}</td>
                                        <td className="px-4 py-3">{d.quantum_safe ? <ShieldCheck className="w-5 h-5 text-green-400" /> : <ShieldAlert className="w-5 h-5 text-red-400" />}</td>
                                        <td className="px-4 py-3 font-mono text-xs">{d.key_size_bytes} B</td>
                                        <td className="px-4 py-3 font-mono text-xs">{d.ciphertext_overhead_bytes} B</td>
                                        <td className="px-4 py-3 font-mono text-xs">{d.avg_keygen_ms?.toFixed(3)}</td>
                                        <td className="px-4 py-3 font-mono text-xs">{d.avg_encrypt_ms?.toFixed(3)}</td>
                                        <td className="px-4 py-3 font-mono text-xs">{d.avg_decrypt_ms?.toFixed(3)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {data.using_liboqs?.some(v => !v) && (
                            <div className="px-4 py-2 bg-yellow-500/5 border-t border-yellow-500/20 text-xs text-yellow-400">
                                ⚠ Simulated — PQC results use mathematical simulation. Install liboqs for real measurements.
                            </div>
                        )}
                    </div>

                    {/* Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                            <h3 className="text-sm font-semibold mb-3">Key Generation Time (ms)</h3>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={keygenData}><CartesianGrid strokeDasharray="3 3" stroke="#334155" /><XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 9 }} angle={-30} textAnchor="end" height={60} /><YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="ms" fill="#3b82f6" radius={[4, 4, 0, 0]} /></BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                            <h3 className="text-sm font-semibold mb-3">Encrypt/Encapsulate (ms)</h3>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={encData}><CartesianGrid strokeDasharray="3 3" stroke="#334155" /><XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 9 }} angle={-30} textAnchor="end" height={60} /><YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} /><Bar dataKey="ms" fill="#f97316" radius={[4, 4, 0, 0]} /></BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-5">
                            <h3 className="text-sm font-semibold mb-3">Key + Ciphertext Size (bytes)</h3>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={sizeData}><CartesianGrid strokeDasharray="3 3" stroke="#334155" /><XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 9 }} angle={-30} textAnchor="end" height={60} /><YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} /><Legend /><Bar dataKey="key" name="Key Size" fill="#22c55e" radius={[4, 4, 0, 0]} /><Bar dataKey="ct" name="Ciphertext" fill="#8b5cf6" radius={[4, 4, 0, 0]} /></BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}

            {/* Try It Yourself */}
            <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4">🔬 Try It Yourself</h2>
                <div className="flex flex-wrap gap-3 items-end">
                    <div>
                        <label className="text-sm text-[var(--color-text-muted)] mb-1 block">Algorithm</label>
                        <select value={demoAlgo} onChange={e => setDemoAlgo(e.target.value)} className="bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]">
                            {ALGO_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                    </div>
                    <button onClick={tryDemo} disabled={demoLoading} className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                        {demoLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        Run Demo
                    </button>
                </div>
                {demoResult && !demoResult.error && (
                    <div className="mt-4 bg-[var(--color-bg-primary)] rounded-lg p-4 font-mono text-xs space-y-1">
                        <p className="text-green-400">✓ {demoResult.algorithm || demoAlgo} — {demoResult.success ? 'SUCCESS' : 'FAILED'}</p>
                        <p>Key Generation: <span className="text-[var(--color-accent)]">{demoResult.key_gen_ms?.toFixed(3)} ms</span></p>
                        <p>Encrypt/Encap:  <span className="text-orange-400">{demoResult.encrypt_ms?.toFixed(3)} ms</span></p>
                        <p>Decrypt/Decap:  <span className="text-yellow-400">{demoResult.decrypt_ms?.toFixed(3)} ms</span></p>
                        <p>Public Key:     <span className="text-[var(--color-text-secondary)]">{demoResult.public_key_bytes} bytes</span></p>
                        {demoResult.ciphertext_bytes && <p>Ciphertext:     <span className="text-[var(--color-text-secondary)]">{demoResult.ciphertext_bytes} bytes</span></p>}
                        {demoResult.shared_secret_hex && <p>Shared Secret:  <span className="text-purple-400">{demoResult.shared_secret_hex}</span></p>}
                        {demoResult.note && <p className="text-yellow-400 mt-2">⚠ {demoResult.note}</p>}
                    </div>
                )}
                {demoResult?.error && <p className="mt-4 text-red-400">Error: {demoResult.error}</p>}
            </div>

            {/* Explainer Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[var(--color-bg-card)] border border-red-500/20 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2"><ShieldAlert className="w-5 h-5 text-red-400" /><h3 className="font-semibold text-red-400">Classical Crypto</h3></div>
                    <p className="text-sm text-[var(--color-text-secondary)]">RSA and ECC rely on mathematical problems (integer factorization, discrete logarithm) that quantum computers can solve efficiently using Shor's algorithm. A cryptographically relevant quantum computer could break RSA-2048 in hours.</p>
                </div>
                <div className="bg-[var(--color-bg-card)] border border-yellow-500/20 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2"><ShieldQuestion className="w-5 h-5 text-yellow-400" /><h3 className="font-semibold text-yellow-400">Hybrid Strategy</h3></div>
                    <p className="text-sm text-[var(--color-text-secondary)]">Hybrid key exchange combines ECDH with Kyber, deriving a session key from both shared secrets via HKDF. An attacker must break BOTH classical AND post-quantum algorithms — the safest transition path recommended by NIST.</p>
                </div>
                <div className="bg-[var(--color-bg-card)] border border-green-500/20 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-2"><ShieldCheck className="w-5 h-5 text-green-400" /><h3 className="font-semibold text-green-400">Post-Quantum (Kyber)</h3></div>
                    <p className="text-sm text-[var(--color-text-secondary)]">CRYSTALS-Kyber (ML-KEM), standardized by NIST in FIPS 203, is based on the Module Learning With Errors problem. Unlike RSA/ECC, no known quantum algorithm can efficiently solve lattice-based problems, providing long-term security.</p>
                </div>
            </div>
        </div>
    )
}
