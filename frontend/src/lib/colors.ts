/**
 * Deterministic cursor color assignment.
 * Given a userId string, always returns the same color.
 * This keeps each user's cursor color consistent across reconnects.
 */
export const CURSOR_COLORS = [
  '#f43f5e', // rose
  '#f97316', // orange
  '#eab308', // amber
  '#22c55e', // emerald
  '#06b6d4', // cyan
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#14b8a6', // teal
  '#a855f7', // purple
]

/**
 * Hashes a string to a number (simple djb2 variant).
 */
function hashString(str: string): number {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i)
  }
  return Math.abs(hash)
}

/**
 * Returns a consistent color for a given userId.
 * The same userId always maps to the same color.
 */
export function getUserColor(userId: string): string {
  return CURSOR_COLORS[hashString(userId) % CURSOR_COLORS.length]
}

/**
 * Returns initials from a display name (up to 2 chars).
 * e.g. "Alice Smith" → "AS", "Bob" → "B"
 */
export function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}
