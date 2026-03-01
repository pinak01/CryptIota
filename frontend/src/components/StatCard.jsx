export default function StatCard({ icon: Icon, value, label, color = 'blue', trend, pulse }) {
    const colorMap = {
        blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/20 text-blue-400',
        red: 'from-red-500/20 to-red-600/5 border-red-500/20 text-red-400',
        orange: 'from-orange-500/20 to-orange-600/5 border-orange-500/20 text-orange-400',
        green: 'from-green-500/20 to-green-600/5 border-green-500/20 text-green-400',
        purple: 'from-purple-500/20 to-purple-600/5 border-purple-500/20 text-purple-400',
    }
    const classes = colorMap[color] || colorMap.blue
    const iconColorMap = { blue: 'text-blue-400', red: 'text-red-400', orange: 'text-orange-400', green: 'text-green-400', purple: 'text-purple-400' }

    return (
        <div className={`relative overflow-hidden rounded-xl bg-gradient-to-br ${classes} border p-5 transition-transform hover:scale-[1.02] ${pulse ? 'animate-pulse-glow' : ''}`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-1">{label}</p>
                    <p className="text-3xl font-bold text-[var(--color-text-primary)]">{value}</p>
                    {trend !== undefined && (
                        <p className={`text-xs mt-1 ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% from last scan
                        </p>
                    )}
                </div>
                {Icon && (
                    <div className={`p-3 rounded-lg bg-white/5 ${iconColorMap[color]}`}>
                        <Icon className="w-6 h-6" />
                    </div>
                )}
            </div>
            <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full bg-white/[0.03]" />
        </div>
    )
}
