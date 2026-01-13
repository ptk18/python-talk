import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import SignUp from '../views/SignUp.vue'
import Profile from '../views/Profile.vue'

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

