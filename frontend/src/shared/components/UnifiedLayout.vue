<template>
  <div class="app-container">
    <TopToolbar />
    <Sidebar />
    <AppSidebar
      :app-id="appId"
      :app-name="appName"
      :app-icon="appIcon"
      :app-type="appType"
      :current-file="currentFile"
      @insert-method="$emit('insert-method', $event)"
      @select-file="$emit('select-file', $event)"
    />
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
  emits: ['insert-method', 'select-file']
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

@media (max-width: 1024px) {
  .unified-main {
    margin-left: var(--sidebar-width);
  }

  .unified-layout__container {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
  }

  .unified-layout__editor-column,
  .unified-layout__output-column {
    flex: none;
  }

  .unified-layout__editor-column {
    min-height: 300px;
  }

  .unified-layout__output-column {
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .unified-main {
    margin-left: 0;
  }

  .unified-layout__container {
    padding: 12px;
    gap: 12px;
  }
}
</style>
