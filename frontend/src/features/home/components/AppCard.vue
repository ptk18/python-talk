<template>
  <div class="app-card" @click="handleCardClick">
    <!-- Favorite button -->
    <button
      class="favorite-button"
      :class="{ 'is-favorited': isFavorited }"
      @click.stop="handleFavoriteClick"
      :title="isFavorited ? 'Remove from favorites' : 'Add to favorites'"
    >
      <svg
        class="heart-icon"
        viewBox="0 0 24 24"
        :fill="isFavorited ? 'currentColor' : 'none'"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
    </button>

    <!-- 3-dots menu for user apps -->
    <div v-if="app.isUserApp" class="menu-container" @click.stop>
      <button class="menu-button" @click="toggleMenu">
        <span class="dots">&#8942;</span>
      </button>
      <div v-if="showMenu" class="menu-dropdown">
        <button class="menu-item" @click="handleEdit">
          <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Edit
        </button>
        <button class="menu-item menu-item-danger" @click="handleDelete">
          <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
          Delete
        </button>
      </div>
    </div>

    <div class="app-icon">
      <img v-if="isImageIcon" :src="app.icon" :alt="app.name" class="app-icon-img" />
      <span v-else>{{ app.icon }}</span>
    </div>
    <div class="app-info">
      <h3 class="app-name">{{ app.name }}</h3>
      <div class="app-category">{{ app.category }}</div>
    </div>
    <button
      class="install-btn"
      :style="buttonStyle"
      @click.stop="handleButtonClick"
    >Deploy</button>
  </div>
</template>

<script>
export default {
  name: 'AppCard',
  props: {
    app: {
      type: Object,
      required: true
    },
    isFavorited: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showMenu: false
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
    },
    buttonStyle() {
      // Use app-specific color if provided, otherwise use default green
      if (this.app.themeColor) {
        return {
          background: `linear-gradient(180deg, ${this.app.themeColor} 0%, ${this.app.themeColorDark || this.app.themeColor} 100%)`
        }
      }
      return {}
    }
  },
  emits: ['click', 'edit', 'delete', 'toggle-favorite'],
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
    },
    toggleMenu() {
      this.showMenu = !this.showMenu
    },
    handleEdit() {
      this.showMenu = false
      this.$emit('edit', this.app)
    },
    handleDelete() {
      this.showMenu = false
      this.$emit('delete', this.app)
    },
    handleFavoriteClick() {
      this.$emit('toggle-favorite', this.app)
    },
    closeMenuOnOutsideClick(event) {
      // Close menu if clicked outside
      if (this.showMenu && !this.$el.contains(event.target)) {
        this.showMenu = false
      }
    }
  },
  mounted() {
    // Close menu when clicking outside
    document.addEventListener('click', this.closeMenuOnOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeMenuOnOutsideClick)
  }
}
</script>

<style scoped>
.app-card {
  position: relative;
}

.app-icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 16px;
}

.menu-container {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
}

.menu-button {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s ease;
}

.menu-button:hover {
  background: white;
  box-shadow: 0 3px 6px rgba(0,0,0,0.15);
}

.dots {
  font-size: 16px;
  color: #666;
  line-height: 1;
}

.menu-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  overflow: hidden;
  min-width: 120px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  text-align: left;
  transition: background-color 0.15s ease;
}

.menu-item:hover {
  background: #f5f5f5;
}

.menu-item-danger:hover {
  background: #ffebee;
  color: #d32f2f;
}

.menu-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.favorite-button {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s ease;
  color: #999;
}

.favorite-button:hover {
  background: white;
  box-shadow: 0 3px 6px rgba(0,0,0,0.15);
  color: #1a1a1a;
  transform: scale(1.1);
}

.favorite-button.is-favorited {
  color: #1a1a1a;
}

.favorite-button.is-favorited:hover {
  color: #333;
}

.heart-icon {
  width: 18px;
  height: 18px;
}
</style>
