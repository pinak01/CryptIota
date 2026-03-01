export default function LoadingSpinner({ text = 'Loading...' }) {
    return (
        <div className="flex flex-col items-center justify-center py-20 gap-4 animate-fade-in">
            <div className="relative w-12 h-12">
                <div className="absolute inset-0 rounded-full border-2 border-[var(--color-border)]" />
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[var(--color-accent)] animate-spin" />
            </div>
            <p className="text-sm text-[var(--color-text-secondary)]">{text}</p>
        </div>
    )
}

export function SkeletonCard() {
    return (
        <div className="rounded-xl bg-[var(--color-bg-card)] border border-[var(--color-border)] p-5">
            <div className="skeleton h-4 w-24 mb-3" />
            <div className="skeleton h-8 w-16 mb-2" />
            <div className="skeleton h-3 w-32" />
        </div>
    )
}

export function SkeletonTable({ rows = 5, cols = 6 }) {
    return (
        <div className="space-y-2">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex gap-4">
                    {Array.from({ length: cols }).map((_, j) => (
                        <div key={j} className="skeleton h-8 flex-1" />
                    ))}
                </div>
            ))}
        </div>
    )
}
