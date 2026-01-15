<template>
  <div></div>
</template>

<script>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    onMounted(() => {
      router.replace('/turtle-playground')
    })
    return {}
  }
}
</script>
