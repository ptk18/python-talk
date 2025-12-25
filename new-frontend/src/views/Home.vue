<template>
  <div class="app-container">
    <Sidebar />
    <main class="main-content">
      <div class="content-area">
        <section class="featured-section">
          <h2 class="section-title">Featured Apps</h2>
          <div class="app-grid">
            <AppCard
              v-for="app in featuredApps"
              :key="app.id"
              :app="app"
              @click="handleAppClick(app)"
            />
          </div>
        </section>

        <section class="functions-section">
          <h2 class="section-title">System Functions</h2>
          <div class="functions-table-container">
            <table class="functions-table">
              <thead>
                <tr>
                  <th class="col-name">Function Name</th>
                  <th class="col-description">Description</th>
                  <th class="col-file">File</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="func in functions"
                  :key="func.id"
                  class="function-row"
                >
                  <td class="function-name-cell">
                    <span class="function-name">{{ func.name }}</span>
                  </td>
                  <td class="function-description-cell">
                    <span class="function-description">{{ func.description }}</span>
                  </td>
                  <td class="function-file-cell">
                    <span class="function-file">{{ func.file }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="category-section" v-for="category in categories" :key="category.name">
          <h2 class="section-title">{{ category.name }}</h2>
          <div class="app-grid">
            <AppCard
              v-for="app in category.apps"
              :key="app.id"
              :app="app"
              @click="handleAppClick(app)"
            />
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import Sidebar from '../components/Sidebar.vue'
import AppCard from '../components/AppCard.vue'
import codeGeneratorIcon from '../assets/F-code-generator.png'
import smartHomeIcon from '../assets/F-smart-home.png'

export default {
  name: 'Home',
  components: {
    Sidebar,
    AppCard
  },
  setup() {
    const router = useRouter()

    const handleAppClick = (app) => {
      if (app.route) {
        router.push(app.route)
      } else if (app.url) {
        window.open(app.url, '_blank')
      }
    }

    return {
      handleAppClick
    }
  },
  data() {
    return {
      searchQuery: '',
      featuredApps: [
        {
          id: 1,
          name: 'PyTalk Workspace',
          icon: codeGeneratorIcon,
          category: 'Code Assistant',
          rating: 4.5,
          route: '/conversation-manager'
        },
        {
          id: 2,
          name: 'Smart Home',
          icon: smartHomeIcon,
          category: 'Connect to your home',
          rating: 4.7
        },
        {
          id: 3,
          name: 'ReflexTest',
          icon: '💬',
          category: 'Entertainment',
          rating: 4.6,
          url: 'http://localhost:3010/'
        }
      ],
      functions: [
        {
          id: 1,
          name: 'Voice Recognition',
          description: 'Convert speech to text using advanced AI models',
          file: 'speech_recognition.py'
        },
        {
          id: 2,
          name: 'Code Execution',
          description: 'Run Python code and see results in real-time',
          file: 'code_runner.py'
        },
        {
          id: 3,
          name: 'Chat Assistant',
          description: 'Interactive AI chat for coding assistance',
          file: 'chat_handler.py'
        },
        {
          id: 4,
          name: 'Function Extraction',
          description: 'Extract and save functions from conversations',
          file: 'function_extractor.py'
        },
        {
          id: 5,
          name: 'Code Analysis',
          description: 'Analyze code for errors and improvements',
          file: 'code_analyzer.py'
        },
        {
          id: 6,
          name: 'History Management',
          description: 'View and manage your chat and code history',
          file: 'history_manager.py'
        }
      ],
      categories: []
    }
  }
}
</script>

<style scoped>
.functions-section {
  margin-bottom: 48px;
}

.section-title {
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  margin-bottom: 20px;
}

.functions-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.functions-table {
  width: 100%;
  border-collapse: collapse;
}

.functions-table thead {
  background: #fafafa;
  border-bottom: 2px solid #e8e8e8;
}

.functions-table th {
  padding: 16px 20px;
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.functions-table th.col-name {
  width: 200px;
}

.functions-table th.col-description {
  width: auto;
}

.functions-table th.col-file {
  width: 200px;
}

.function-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #f0f0f0;
}

.function-row:hover {
  background: #f8f9fa;
}

.function-row:last-child {
  border-bottom: none;
}

.function-name-cell {
  padding: 16px 20px;
}

.function-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  font-family: 'Jaldi', sans-serif;
}

.function-description-cell {
  padding: 16px 20px;
}

.function-description {
  font-size: 14px;
  color: #666;
  font-family: 'Jaldi', sans-serif;
  line-height: 1.5;
}

.function-file-cell {
  padding: 16px 20px;
}

.function-file {
  font-size: 14px;
  color: #024A14;
  font-family: 'Courier New', monospace;
  font-weight: 500;
  background: #f0f7f2;
  padding: 4px 12px;
  border-radius: 6px;
  display: inline-block;
}

@media (max-width: 768px) {
  .functions-table-container {
    overflow-x: auto;
  }

  .functions-table {
    min-width: 600px;
  }

  .functions-table th,
  .functions-table td {
    padding: 12px 16px;
    font-size: 13px;
  }

  .function-name {
    font-size: 15px;
  }

  .function-description {
    font-size: 13px;
  }

  .function-file {
    font-size: 12px;
  }

  .section-title {
    font-size: 22px;
  }
}
</style>
