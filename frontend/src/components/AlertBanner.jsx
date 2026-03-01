import { AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'

const severityColors = {
    CRITICAL: 'bg-red-500/15 border-red-500/30 text-red-300',
    HIGH: 'bg-orange-500/15 border-orange-500/30 text-orange-300',
    MEDIUM: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-300',
    INFO: 'bg-blue-500/15 border-blue-500/30 text-blue-300',
}

export default function AlertBanner({ severity = 'CRITICAL', title, message, onDismiss }) {
    const [visible, setVisible] = useState(true)
    if (!visible) return null

    const colors = severityColors[severity] || severityColors.INFO

    return (
        <div className={`flex items-start gap-3 rounded-xl border p-4 ${colors} animate-fade-in`}>
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm">{title}</p>
                {message && <p className="text-sm opacity-80 mt-0.5">{message}</p>}
            </div>
            <button
                onClick={() => { setVisible(false); onDismiss?.() }}
                className="p-1 rounded hover:bg-white/10 shrink-0"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    )
}
