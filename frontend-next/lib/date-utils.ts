export function formatDistanceToNow(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60,
    second: 1,
  }

  for (const [key, value] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / value)
    if (interval >= 1) {
      return `${interval} ${key}${interval !== 1 ? 's' : ''} ago`
    }
  }

  return 'just now'
}
