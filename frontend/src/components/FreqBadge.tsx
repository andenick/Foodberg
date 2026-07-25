import { FREQUENCY_LABEL, type Frequency } from '../arcanum/arkTransforms'

/**
 * The site's one update-frequency badge.
 *
 * Frequency is a first-class idea on Foodberg — "annual is too infrequent for
 * my chef friend to really dive in" — so the badge has to mean the same thing
 * on every page. It previously did not: the explorer coloured monthly blue and
 * annual grey, while Compare painted EVERY frequency emerald, which made an
 * annual series look like the recommended one. One component, one semantic
 * ramp: the finer the cadence, the warmer the badge; annual is deliberately
 * the quietest.
 *
 * Every tone carries an explicit light-mode pair. The kit ships both themes,
 * and a dark-only palette (light text on a low-alpha dark fill) renders as
 * pale-on-pale over the light theme's white page — legible in review, invisible
 * to half the audience.
 */
const TONE: Record<Frequency, string> = {
    daily: 'text-emerald-800 bg-emerald-100 dark:text-emerald-300 dark:bg-emerald-900/40',
    weekly: 'text-teal-800 bg-teal-100 dark:text-teal-300 dark:bg-teal-900/40',
    monthly: 'text-sky-800 bg-sky-100 dark:text-sky-300 dark:bg-sky-900/40',
    annual: 'text-ark-fg-dim bg-ark-tag',
}

export default function FreqBadge({ freq, className }: { freq: Frequency; className?: string }) {
    return (
        <span
            title={`Published ${FREQUENCY_LABEL[freq].toLowerCase()}`}
            className={`shrink-0 text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded ${TONE[freq]}${className ? ` ${className}` : ''}`}
        >
            {FREQUENCY_LABEL[freq]}
        </span>
    )
}
