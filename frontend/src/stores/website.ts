// src/stores/website.ts
import { computed, ref } from 'vue'

import { defineStore } from 'pinia'

import { useAuthenticatedClient } from '@/composables/useAuthenticatedClient'

import type {
  CheckTrigger,
  DashboardResponse,
  NotificationChannel,
  NotificationSettingsResponse,
  NotificationSettingsUpdate,
  WebsiteCheckListResponse,
  WebsiteCheckResponse,
  WebsiteCreate,
  WebsiteListResponse,
  WebsiteResponse,
  WebsiteUpdate,
  WebsiteWithChecks,
} from '@/client/types.gen'
import type { CheckFilters, PaginationState, WebsiteFilters } from '@/types/website'

export const useWebsiteStore = defineStore('website', () => {
  // State
  const websites = ref<WebsiteResponse[]>([])
  const currentWebsite = ref<WebsiteWithChecks | null>(null)
  const checks = ref<WebsiteCheckResponse[]>([])
  const dashboardData = ref<DashboardResponse | null>(null)
  const notificationSettings = ref<NotificationSettingsResponse | null>(null)

  const loading = ref(false)
  const checkLoading = ref(false)
  const dashboardLoading = ref(false)
  const notificationLoading = ref(false)
  const error = ref<string | null>(null)

  const pagination = ref<PaginationState>({
    page: 1,
    perPage: 20,
    total: 0,
    totalPages: 0,
  })

  const checkPagination = ref<PaginationState>({
    page: 1,
    perPage: 50,
    total: 0,
    totalPages: 0,
  })

  const filters = ref<WebsiteFilters>({})
  const checkFilters = ref<CheckFilters>({})

  // API client
  const { get, post, patch, delete: del, put } = useAuthenticatedClient()

  // Getters
  const activeWebsites = computed(() => websites.value.filter((w) => w.is_active))

  const inactiveWebsites = computed(() => websites.value.filter((w) => !w.is_active))

  const filteredWebsites = computed(() => {
    let filtered = websites.value

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      filtered = filtered.filter(
        (w) => w.name.toLowerCase().includes(search) || w.url.toLowerCase().includes(search),
      )
    }

    if (filters.value.status === 'active') {
      filtered = filtered.filter((w) => w.is_active)
    } else if (filters.value.status === 'inactive') {
      filtered = filtered.filter((w) => !w.is_active)
    }

    return filtered
  })

  const recentChanges = computed(() => dashboardData.value?.recent_changes || [])

  const failingWebsites = computed(() => dashboardData.value?.failing_websites || [])

  const stats = computed(() => dashboardData.value?.stats)

  // Actions
  const fetchWebsites = async (page = 1, resetList = true): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      // Defensive check for pagination values
      const perPage = pagination.value.perPage || 20
      const params = new URLSearchParams({
        skip: ((page - 1) * perPage).toString(),
        limit: perPage.toString(),
      })

      const response = (await get({
        url: `/api/v1/websites/?${params}`,
      })) as WebsiteListResponse

      if (resetList) {
        websites.value = response.items
      } else {
        websites.value.push(...response.items)
      }

      pagination.value = {
        page: response.page,
        perPage: response.per_page,
        total: response.total,
        totalPages: response.pages,
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch websites'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createWebsite = async (websiteData: WebsiteCreate): Promise<WebsiteResponse> => {
    loading.value = true
    error.value = null

    try {
      const newWebsite = (await post({
        url: '/api/v1/websites/',
        body: websiteData,
      })) as WebsiteResponse

      websites.value.unshift(newWebsite)
      pagination.value.total += 1

      return newWebsite
    } catch (err: any) {
      error.value = err.message || 'Failed to create website'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateWebsite = async (
    websiteId: string,
    websiteData: WebsiteUpdate,
  ): Promise<WebsiteResponse> => {
    loading.value = true
    error.value = null

    try {
      const updatedWebsite = (await patch({
        url: `/api/v1/websites/${websiteId}`,
        body: websiteData,
      })) as WebsiteResponse

      const index = websites.value.findIndex((w) => w.id === websiteId)
      if (index !== -1) {
        websites.value[index] = updatedWebsite
      }

      if (currentWebsite.value?.id === websiteId) {
        // Update current website while preserving checks
        currentWebsite.value = {
          ...updatedWebsite,
          recent_checks: currentWebsite.value.recent_checks,
          last_check_at: currentWebsite.value.last_check_at,
          last_change_at: currentWebsite.value.last_change_at,
        }
      }

      return updatedWebsite
    } catch (err: any) {
      error.value = err.message || 'Failed to update website'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteWebsite = async (websiteId: string): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      await del({
        url: `/api/v1/websites/${websiteId}`,
      })

      websites.value = websites.value.filter((w) => w.id !== websiteId)
      pagination.value.total -= 1

      if (currentWebsite.value?.id === websiteId) {
        currentWebsite.value = null
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete website'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchWebsiteDetails = async (
    websiteId: string,
    includeChecks = 10,
  ): Promise<WebsiteWithChecks> => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        include_checks: includeChecks.toString(),
      })

      const website = (await get({
        url: `/api/v1/websites/${websiteId}?${params}`,
      })) as WebsiteWithChecks

      currentWebsite.value = website
      return website
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch website details'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchWebsiteChecks = async (
    websiteId: string,
    page = 1,
    resetList = true,
  ): Promise<void> => {
    checkLoading.value = true
    error.value = null

    try {
      // Defensive check for pagination values
      const perPage = checkPagination.value.perPage || 50
      const params = new URLSearchParams({
        skip: ((page - 1) * perPage).toString(),
        limit: perPage.toString(),
      })

      const response = (await get({
        url: `/api/v1/websites/${websiteId}/checks?${params}`,
      })) as WebsiteCheckListResponse

      if (resetList) {
        checks.value = response.items
      } else {
        checks.value.push(...response.items)
      }

      checkPagination.value = {
        page: response.page,
        perPage: response.per_page,
        total: response.total,
        totalPages: response.pages,
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch website checks'
      throw err
    } finally {
      checkLoading.value = false
    }
  }

  const triggerManualCheck = async (websiteIds?: string[]): Promise<void> => {
    checkLoading.value = true
    error.value = null

    try {
      const triggerData: CheckTrigger = {
        website_ids: websiteIds || null,
      }

      await post({
        url: '/api/v1/websites/check',
        body: triggerData,
      })

      // Refresh current data after triggering check
      if (currentWebsite.value) {
        await fetchWebsiteDetails(currentWebsite.value.id, 10)
      } else {
        await fetchWebsites(pagination.value.page, true)
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to trigger manual check'
      throw err
    } finally {
      checkLoading.value = false
    }
  }

  const fetchDashboardStats = async (): Promise<void> => {
    dashboardLoading.value = true
    error.value = null

    try {
      const response = (await get({
        url: '/api/v1/websites/dashboard/stats',
      })) as DashboardResponse

      dashboardData.value = response
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch dashboard stats'
      throw err
    } finally {
      dashboardLoading.value = false
    }
  }

  const fetchNotificationSettings = async (): Promise<NotificationSettingsResponse> => {
    notificationLoading.value = true
    error.value = null

    try {
      const response = (await get({
        url: '/api/v1/websites/settings/notifications',
      })) as NotificationSettingsResponse

      notificationSettings.value = response
      return response
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch notification settings'
      throw err
    } finally {
      notificationLoading.value = false
    }
  }

  const updateNotificationSettings = async (
    settings: NotificationSettingsUpdate,
  ): Promise<NotificationSettingsResponse> => {
    notificationLoading.value = true
    error.value = null

    try {
      const response = (await put({
        url: '/api/v1/websites/settings/notifications',
        body: settings,
      })) as NotificationSettingsResponse

      notificationSettings.value = response
      return response
    } catch (err: any) {
      error.value = err.message || 'Failed to update notification settings'
      throw err
    } finally {
      notificationLoading.value = false
    }
  }

  const testNotification = async (channel: NotificationChannel): Promise<void> => {
    notificationLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        channel,
      })

      await post({
        url: `/api/v1/websites/settings/notifications/test?${params}`,
      })
    } catch (err: any) {
      error.value = err.message || 'Failed to send test notification'
      throw err
    } finally {
      notificationLoading.value = false
    }
  }

  // Utility actions
  const clearError = () => {
    error.value = null
  }

  const setFilters = (newFilters: Partial<WebsiteFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const setCheckFilters = (newFilters: Partial<CheckFilters>) => {
    checkFilters.value = { ...checkFilters.value, ...newFilters }
  }

  const clearFilters = () => {
    filters.value = {}
  }

  const clearCheckFilters = () => {
    checkFilters.value = {}
  }

  return {
    // State
    websites,
    currentWebsite,
    checks,
    dashboardData,
    notificationSettings,
    loading,
    checkLoading,
    dashboardLoading,
    notificationLoading,
    error,
    pagination,
    checkPagination,
    filters,
    checkFilters,

    // Getters
    activeWebsites,
    inactiveWebsites,
    filteredWebsites,
    recentChanges,
    failingWebsites,
    stats,

    // Actions
    fetchWebsites,
    createWebsite,
    updateWebsite,
    deleteWebsite,
    fetchWebsiteDetails,
    fetchWebsiteChecks,
    triggerManualCheck,
    fetchDashboardStats,
    fetchNotificationSettings,
    updateNotificationSettings,
    testNotification,
    clearError,
    setFilters,
    setCheckFilters,
    clearFilters,
    clearCheckFilters,
  }
})
