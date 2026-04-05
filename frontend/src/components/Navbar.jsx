import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Shield, LayoutDashboard, Server, MapPin, Gauge, GitBranch, Upload, Menu, X, FlaskConical } from 'lucide-react'
import { fetchModelInfo } from '../api/apiClient'

const NAV_ITEMS = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/devices', label: 'Devices', icon: Server },
    { path: '/heatmap', label: 'Heatmap', icon: MapPin },
    { path: '/benchmarks', label: 'Benchmarks', icon: Gauge },
    { path: '/migration', label: 'Migration', icon: GitBranch },
    { path: '/upload', label: 'Upload', icon: Upload },
    { path: '/iot-lab', label: 'IoT Lab', icon: FlaskConical },
]

export default function Navbar() {
    const location = useLocation()
    const [modelInfo, setModelInfo] = useState(null)
    const [mobileOpen, setMobileOpen] = useState(false)

    useEffect(() => {
        fetchModelInfo().then(setModelInfo).catch(() => { })
    }, [])

    return (
        <nav className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-bg-card)]/80 backdrop-blur-xl">
            <div className="max-w-[1440px] mx-auto px-4 sm:px-6">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2 shrink-0 group">
                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[var(--color-accent)] to-blue-700 flex items-center justify-center shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow">
                            <Shield className="w-5 h-5 text-white" />
                        </div>
                        <div className="hidden sm:block">
                            <span className="text-lg font-bold bg-gradient-to-r from-[var(--color-accent)] to-blue-300 bg-clip-text text-transparent">
                                QuantumGuard
                            </span>
                            <span className="text-lg font-light text-[var(--color-text-secondary)] ml-1">AI</span>
                        </div>
                    </Link>

                    {/* Desktop nav */}
                    <div className="hidden md:flex items-center gap-1">
                        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
                            const active = location.pathname === path
                            return (
                                <Link
                                    key={path}
                                    to={path}
                                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${active
                                        ? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
                                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-white/5'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    {label}
                                </Link>
                            )
                        })}
                    </div>

                    {/* Right side */}
                    <div className="flex items-center gap-3">
                        {modelInfo && modelInfo.model_type && (
                            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--color-low)]/10 border border-[var(--color-low)]/20">
                                <div className="w-2 h-2 rounded-full bg-[var(--color-low)] animate-pulse" />
                                <span className="text-xs font-medium text-[var(--color-low)]">
                                    {modelInfo.model_type.split(' ')[0]} Model | {((modelInfo.accuracy || 0) * 100).toFixed(1)}%
                                </span>
                            </div>
                        )}
                        <button
                            className="md:hidden p-2 rounded-lg hover:bg-white/5"
                            onClick={() => setMobileOpen(!mobileOpen)}
                        >
                            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                    </div>
                </div>

                {/* Mobile nav */}
                {mobileOpen && (
                    <div className="md:hidden pb-4 border-t border-[var(--color-border)] mt-2 pt-3 animate-fade-in">
                        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
                            const active = location.pathname === path
                            return (
                                <Link
                                    key={path}
                                    to={path}
                                    onClick={() => setMobileOpen(false)}
                                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${active
                                        ? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
                                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                                        }`}
                                >
                                    <Icon className="w-4 h-4" />
                                    {label}
                                </Link>
                            )
                        })}
                    </div>
                )}
            </div>
        </nav>
    )
}
