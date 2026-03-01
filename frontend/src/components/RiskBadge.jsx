import { AlertTriangle, ArrowUp, Info, CheckCircle, Skull } from 'lucide-react'

const RISK_STYLES = {
    CRITICAL: { bg: 'bg-[var(--color-critical)]/15', border: 'border-[var(--color-critical)]/30', text: 'text-[var(--color-critical)]', icon: Skull, label: '⚠ CRITICAL' },
    HIGH: { bg: 'bg-[var(--color-high)]/15', border: 'border-[var(--color-high)]/30', text: 'text-[var(--color-high)]', icon: AlertTriangle, label: '↑ HIGH' },
    MEDIUM: { bg: 'bg-[var(--color-medium)]/15', border: 'border-[var(--color-medium)]/30', text: 'text-[var(--color-medium)]', icon: Info, label: '~ MEDIUM' },
    LOW: { bg: 'bg-[var(--color-low)]/15', border: 'border-[var(--color-low)]/30', text: 'text-[var(--color-low)]', icon: CheckCircle, label: '✓ LOW' },
}

export default function RiskBadge({ level, size = 'md' }) {
    const style = RISK_STYLES[level] || RISK_STYLES.LOW
    const Icon = style.icon
    const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : size === 'lg' ? 'px-4 py-2 text-base' : 'px-3 py-1 text-sm'

    return (
        <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${style.bg} ${style.border} ${style.text} ${sizeClasses} ${level === 'CRITICAL' ? 'animate-pulse-glow' : ''}`}>
            <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
            {style.label}
        </span>
    )
}
