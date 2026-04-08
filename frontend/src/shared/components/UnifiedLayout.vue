<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar />
    <AppSidebar
      ref="appSidebarRef"
      :app-id="appId"
      :app-name="appName"
      :app-icon="appIcon"
      :app-type="appType"
      :current-file="currentFile"
      @insert-method="$emit('insert-method', $event)"
      @select-file="$emit('select-file', $event)"
    />
    <!-- Mobile/Tablet toggle button for AppSidebar -->
    <button class="app-sidebar-toggle" @click="openAppSidebar" :title="'Methods & Files'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="16" y1="13" x2="8" y2="13"></line>
        <line x1="16" y1="17" x2="8" y2="17"></line>
      </svg>
    </button>
    <main class="unified-main">
      <div class="unified-layout">
        <div class="unified-layout__container">
          <!-- Left Column: Code Editor + Debug -->
          <div class="unified-layout__editor-column">
            <div class="unified-layout__editor-area">
              <slot name="editor" />
            </div>
            <slot name="debug" />
          </div>

          <!-- Right Column: Output + Command Input -->
          <div class="unified-layout__output-column">
            <slot name="output" />
            <slot name="command" />
          </div>
        </div>

        <!-- Overlays: StatusBar, Alerts, Dialogs -->
        <slot name="overlays" />
      </div>
    </main>
  </div>
</template>

<script>
import { ref } from 'vue'
import TopToolbar from '@/shared/components/TopToolbar.vue'
import Sidebar from '@/shared/components/Sidebar.vue'
import AppSidebar from '@/shared/components/AppSidebar.vue'

export default {
  name: 'UnifiedLayout',
  components: {
    TopToolbar,
    Sidebar,
    AppSidebar
  },
  props: {
    appId: {
      type: [Number, String],
      default: null
    },
    appName: {
      type: String,
      default: ''
    },
    appIcon: {
      type: String,
      default: null
    },
    appType: {
      type: String,
      default: 'codespace'
    },
    currentFile: {
      type: String,
      default: null
    }
  },
  emits: ['insert-method', 'select-file'],
  setup() {
    const appSidebarRef = ref(null)

    const openAppSidebar = () => {
      appSidebarRef.value?.openDrawer()
    }

    return {
      appSidebarRef,
      openAppSidebar
    }
  }
}
</script>

<style scoped>
.unified-main {
  margin-left: var(--sidebar-total);
  margin-top: var(--toolbar-height);
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
  height: calc(100vh - var(--toolbar-height));
  max-height: calc(100vh - var(--toolbar-height));
  overflow: hidden;
}

.unified-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  position: relative;
}

.unified-layout__container {
  display: flex;
  gap: 16px;
  padding: 20px;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  box-sizing: border-box;
  flex: 1;
  min-height: 0;
}

.unified-layout__editor-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
  min-height: 0;
}

.unified-layout__editor-area {
  flex: 2;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.unified-layout__output-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  min-height: 0;
}

/* Toggle button for AppSidebar - hidden on desktop */
.app-sidebar-toggle {
  display: none;
}

/* Tablet: stack layout, show toggle */
@media (max-width: 1024px) {
  .app-sidebar-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    bottom: 20px;
    right: 16px;
    width: 48px;
    height: 48px;
    background: #ffffff;
    color: var(--color-primary);
    border: 2px solid var(--color-border);
    border-radius: 50%;
    cursor: pointer;
    z-index: var(--z-dropdown);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .app-sidebar-toggle:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    transform: scale(1.08);
  }

  .app-sidebar-toggle:active {
    transform: scale(0.95);
  }
  .unified-layout__editor-area {
    flex: 6;
    min-height: 450px;
  }

  .unified-layout__editor-column {
    gap: 8px;
  }

  .unified-main {
    margin-left: var(--sidebar-width);
  }

  .unified-layout__container {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
    padding: 16px;
  }

  .unified-layout__editor-column,
  .unified-layout__output-column {
    flex: none;
  }

  .unified-layout__editor-column {
    min-height: 70vh;
  }

  .unified-layout__output-column {
    min-height: 400px;
  }
}

/* Mobile */
@media (max-width: 768px) {
  .unified-main {
    margin-left: 0;
    height: auto;
    max-height: none;
    min-height: calc(100vh - 50px);
  }

  .unified-layout {
    height: auto;
    max-height: none;
    overflow: visible;
  }

  .unified-layout__container {
    flex-direction: column;
    padding: 12px;
    gap: 12px;
    height: auto;
    max-height: none;
    overflow: visible;
  }

  .unified-layout__editor-column {
    min-height: 65vh;
    gap: 6px;
  }

  .unified-layout__editor-area {
    flex: 6;
    min-height: 400px;
  }

  .unified-layout__output-column {
    min-height: 350px;
  }
}

/* Small mobile */
@media (max-width: 480px) {
  .unified-layout__container {
    padding: 8px;
    gap: 8px;
  }

  .unified-layout__editor-column {
    min-height: 60vh;
  }

  .unified-layout__editor-area {
    min-height: 350px;
  }

  .unified-layout__output-column {
    min-height: 300px;
  }
}
</style>
