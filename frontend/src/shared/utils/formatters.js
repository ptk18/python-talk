export function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)]
}

export function getGreeting() {
  const hour = new Date().getHours()

  const morningGreetings = [
    'Good morning! Ready to code?',
    'Hey there! Let\'s start the day right.',
    'Morning! What are we building today?'
  ]

  const afternoonGreetings = [
    'Hey there! Let\'s build something great.',
    'Good afternoon! Ready to code?',
    'Hi! What shall we create today?'
  ]

  const eveningGreetings = [
    'Good evening! Let\'s code something awesome.',
    'Evening! What are we working on?',
    'Hey! Ready for some coding?'
  ]

  const defaultGreetings = [
    'Welcome back! Let\'s get started.',
    'Hey! Ready to code?',
    'Let\'s build something great!'
  ]

  if (hour >= 5 && hour < 12) return randomChoice(morningGreetings)
  if (hour >= 12 && hour < 17) return randomChoice(afternoonGreetings)
  if (hour >= 17 && hour < 21) return randomChoice(eveningGreetings)
  return randomChoice(defaultGreetings)
}
