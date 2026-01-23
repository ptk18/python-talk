import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@py-talk/shared'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import SignUp from '../views/SignUp.vue'
import Profile from '../views/Profile.vue'
import Settings from '../views/Settings.vue'

// Lazy-loaded views from codespace-app
const ConversationManager = () => import('../views/ConversationManager.vue')
const Workspace = () => import('../views/Workspace.vue')
const Run = () => import('../views/Run.vue')

// Lazy-loaded views from turtle-app
const TurtlePlayground = () => import('../views/TurtlePlayground.vue')

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
    path: '/conversation-manager',
    name: 'ConversationManager',
    component: ConversationManager,
    meta: { requiresAuth: true }
  },
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
  {
    path: '/history',
    redirect: '/conversation-manager'
  },
  // Routes from turtle-app
  {
    path: '/turtle-playground',
    name: 'TurtlePlayground',
    component: TurtlePlayground,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
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

