import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@py-talk/shared'
import Home from '@/features/home/HomeView.vue'
import Login from '@/features/auth/LoginView.vue'
import SignUp from '@/features/auth/SignUpView.vue'
import Profile from '@/features/profile/ProfileView.vue'
import Settings from '@/features/settings/SettingsView.vue'

// Lazy-loaded feature views
const Workspace = () => import('@/features/codespace/WorkspaceView.vue')
const Run = () => import('@/features/run/RunView.vue')
const TurtlePlayground = () => import('@/features/turtle/TurtlePlaygroundView.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/signup',
    name: 'SignUp',
    component: SignUp,
    meta: { requiresAuth: false }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  // Routes from codespace-app
  {
    path: '/workspace',
    name: 'Workspace',
    component: Workspace,
    meta: { requiresAuth: true }
  },
  {
    path: '/run',
    name: 'Run',
    component: Run,
    meta: { requiresAuth: true }
  },
  // Routes from turtle-app
  {
    path: '/turtle-playground/:appId?',
    name: 'TurtlePlayground',
    component: TurtlePlayground,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory('/pytalk/'),
  routes
})

router.beforeEach((to, from, next) => {
  const { user } = useAuth()

  if (to.meta.requiresAuth && !user.value) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/signup') && user.value) {
    next('/')
  } else {
    next()
  }
})

export default router

