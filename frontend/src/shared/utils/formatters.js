export function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

export function getGreeting() {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'Good Morning, Sir'
  if (hour >= 12 && hour < 17) return 'Good Afternoon, Sir'
  if (hour >= 17 && hour < 21) return 'Good Evening, Sir'
  return 'Welcome, Sir'
}
