import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import ConversationManager from '../views/ConversationManager.vue'
import Workspace from '../views/Workspace.vue'
import TurtlePlayground from '../views/TurtlePlayground.vue'
import History from '../views/History.vue'
import Login from '../views/Login.vue'
import SignUp from '../views/SignUp.vue'
import Profile from '../views/Profile.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/conversation-manager',
    name: 'ConversationManager',
    component: ConversationManager
  },
  {
    path: '/workspace',
    name: 'Workspace',
    component: Workspace
  },
  {
    path: '/turtle-playground',
    name: 'TurtlePlayground',
    component: TurtlePlayground
  },
  {
    path: '/history',
    name: 'History',
    component: History
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/signup',
    name: 'SignUp',
    component: SignUp
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

