import { authGuard } from '@auth0/auth0-vue'
import { createRouter, createWebHistory } from 'vue-router'

import type { BreadcrumbItem } from '@/stores/breadcrumb'

// Extend route meta to include breadcrumbs and layout
declare module 'vue-router' {
  interface RouteMeta {
    breadcrumbs?: BreadcrumbItem[]
    layout?: 'preauth' | 'postauth' | 'minimal'
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Layout wrappers as parent routes
    {
      path: '/',
      name: 'preauth-layout',
      component: () => import('@/layout/PreAuthLayout.vue'),
      children: [
        {
          path: '',
          name: 'landing',
          component: () => import('@/views/preauth/LandingView.vue'),
        },
        {
          path: 'about',
          name: 'about',
          component: () => import('@/views/preauth/AboutView.vue'),
        },
      ],
    },
    {
      path: '/app',
      name: 'postauth-layout',
      redirect: { name: 'home' },
      component: () => import('@/layout/PostAuthLayout.vue'),
      beforeEnter: authGuard,
      children: [
        {
          path: 'home',
          name: 'home',
          redirect: { name: 'website-dashboard' },
        },
        {
          path: 'examples',
          name: 'examples',
          component: () => import('@/views/examples/ExamplesOverviewView.vue'),
          meta: {
            breadcrumbs: [{ title: 'Home', to: { name: 'home' } }, { title: 'Examples' }],
          },
        },
        {
          path: 'test',
          name: 'test',
          component: () => import('@/views/examples/ApiExampleView.vue'),
          meta: {
            breadcrumbs: [
              { title: 'Home', to: { name: 'home' } },
              { title: 'Examples', to: { name: 'examples' } },
              { title: 'API Example' },
            ],
          },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/UserSettingsView.vue'),
          meta: {
            breadcrumbs: [{ title: 'Home', to: { name: 'home' } }, { title: 'Settings' }],
          },
        },
        // Website Monitoring Routes
        {
          path: 'dashboard',
          name: 'website-dashboard',
          component: () => import('@/views/WebsiteDashboardView.vue'),
          meta: {
            breadcrumbs: [{ title: 'Home', to: { name: 'home' } }, { title: 'Dashboard' }],
          },
        },
        {
          path: 'websites',
          name: 'websites',
          component: () => import('@/views/WebsitesManagementView.vue'),
          meta: {
            breadcrumbs: [{ title: 'Home', to: { name: 'home' } }, { title: 'Websites' }],
          },
        },
        {
          path: 'websites/:id',
          name: 'website-detail',
          component: () => import('@/views/WebsiteDetailView.vue'),
          meta: {
            breadcrumbs: [
              { title: 'Home', to: { name: 'home' } },
              { title: 'Websites', to: { name: 'websites' } },
              { title: 'Website Details' },
            ],
          },
        },
        {
          path: 'notifications',
          name: 'notification-settings',
          component: () => import('@/views/NotificationSettingsView.vue'),
          meta: {
            breadcrumbs: [{ title: 'Home', to: { name: 'home' } }, { title: 'Notifications' }],
          },
        },
        {
          path: 'breadcrumb-examples',
          name: 'breadcrumb-examples',
          component: () => import('@/views/examples/BreadcrumbExamplesView.vue'),
          meta: {
            breadcrumbs: [
              { title: 'Home', to: { name: 'home' } },
              { title: 'Examples', to: { name: 'examples' } },
              { title: 'Breadcrumb Examples' },
            ],
          },
        },
        {
          path: 'layout-demo',
          name: 'layout-demo',
          component: () => import('@/views/examples/LayoutDemoView.vue'),
          meta: {
            breadcrumbs: [
              { title: 'Home', to: { name: 'home' } },
              { title: 'Examples', to: { name: 'examples' } },
              { title: 'Layout Demo' },
            ],
          },
        },
      ],
    },
    {
      path: '/',
      name: 'no-layout',
      redirect: { name: 'landing' },
      component: () => import('@/layout/NoLayout.vue'),
      children: [
        {
          path: '404',
          name: 'not-found',
          component: () => import('@/views/NotFoundView.vue'),
        },
      ],
    },

    // Catch-all route - redirect to 404 in no layout
    {
      path: '/:pathMatch(.*)*',
      redirect: { name: 'not-found' },
    },
  ],
})

export default router
