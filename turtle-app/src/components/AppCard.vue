<template>
  <div class="app-card" @click="handleCardClick">
    <div class="app-icon">
      <img v-if="isImageIcon" :src="app.icon" :alt="app.name" class="app-icon-img" />
      <span v-else>{{ app.icon }}</span>
    </div>
    <div class="app-info">
      <h3 class="app-name">{{ app.name }}</h3>
      <div class="app-category">{{ app.category }}</div>
    </div>
    <button class="install-btn" @click.stop="handleButtonClick">Get</button>
  </div>
</template>

<script>
export default {
  name: 'AppCard',
  props: {
    app: {
      type: Object,
      required: true
    }
  },
  computed: {
    isImageIcon() {
      // Check if icon is an image (string path or imported module)
      return typeof this.app.icon === 'string' &&
             (this.app.icon.endsWith('.png') ||
              this.app.icon.endsWith('.jpg') ||
              this.app.icon.endsWith('.jpeg') ||
              this.app.icon.endsWith('.svg') ||
              this.app.icon.startsWith('/') ||
              this.app.icon.startsWith('data:')) ||
             (typeof this.app.icon === 'object' && this.app.icon !== null)
    }
  },
  emits: ['click'],
  methods: {
    handleCardClick() {
      this.$emit('click', this.app)
    },
    handleButtonClick() {
      if (this.app.url) {
        window.open(this.app.url, '_blank')
      } else if (this.app.route) {
        this.$router.push(this.app.route)
      } else {
        console.warn('No URL or route defined for app:', this.app.name)
      }
    }
  }
}
</script>

<style scoped>
.app-icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 16px;
}
</style>

