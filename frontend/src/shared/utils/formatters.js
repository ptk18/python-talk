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
  const lang = localStorage.getItem('language') || 'en'

  const greetings = {
    en: {
      morning: [
        'Good morning! Ready to code?',
        'Hey there! Let\'s start the day right.',
        'Morning! What are we building today?'
      ],
      afternoon: [
        'Hey there! Let\'s build something great.',
        'Good afternoon! Ready to code?',
        'Hi! What shall we create today?'
      ],
      evening: [
        'Good evening! Let\'s code something awesome.',
        'Evening! What are we working on?',
        'Hey! Ready for some coding?'
      ],
      default: [
        'Welcome back! Let\'s get started.',
        'Hey! Ready to code?',
        'Let\'s build something great!'
      ]
    },
    th: {
      morning: [
        'สวัสดีตอนเช้า! พร้อมเขียนโค้ดไหม?',
        'สวัสดี! มาเริ่มวันใหม่กันเถอะ',
        'สวัสดีตอนเช้า! วันนี้จะสร้างอะไรดี?'
      ],
      afternoon: [
        'สวัสดี! มาสร้างอะไรดีๆ กัน',
        'สวัสดีตอนบ่าย! พร้อมเขียนโค้ดไหม?',
        'สวัสดี! วันนี้จะสร้างอะไรดี?'
      ],
      evening: [
        'สวัสดีตอนเย็น! มาเขียนโค้ดกัน',
        'สวัสดีตอนเย็น! จะทำอะไรดี?',
        'สวัสดี! พร้อมเขียนโค้ดไหม?'
      ],
      default: [
        'ยินดีต้อนรับกลับมา! เริ่มกันเลย',
        'สวัสดี! พร้อมเขียนโค้ดไหม?',
        'มาสร้างอะไรดีๆ กัน!'
      ]
    }
  }

  const g = greetings[lang] || greetings.en

  if (hour >= 5 && hour < 12) return randomChoice(g.morning)
  if (hour >= 12 && hour < 17) return randomChoice(g.afternoon)
  if (hour >= 17 && hour < 21) return randomChoice(g.evening)
  return randomChoice(g.default)
}
