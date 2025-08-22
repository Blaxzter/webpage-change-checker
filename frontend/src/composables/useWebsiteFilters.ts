// src/composables/useWebsiteFilters.ts
import { computed, ref, watch } from 'vue'

import { useRoute, useRouter } from 'vue-router'

import type { CheckFilters, WebsiteFilters } from '@/types/website'

export function useWebsiteFilters() {
  const route = useRoute()
  const router = useRouter()

  const filters = ref<WebsiteFilters>({
    search: (route.query.search as string) || '',
    status: (route.query.status as 'all' | 'active' | 'inactive') || 'all',
    hasChanges: route.query.hasChanges ? route.query.hasChanges === 'true' : undefined,
  })

  const hasActiveFilters = computed(
    () =>
      filters.value.search !== '' ||
      filters.value.status !== 'all' ||
      filters.value.hasChanges !== undefined,
  )

  const clearFilters = () => {
    filters.value = {
      search: '',
      status: 'all',
      hasChanges: undefined,
    }
  }

  // Update URL query parameters when filters change
  watch(
    filters,
    (newFilters) => {
      const query: Record<string, string> = {}

      if (newFilters.search) query.search = newFilters.search
      if (newFilters.status && newFilters.status !== 'all') query.status = newFilters.status
      if (newFilters.hasChanges !== undefined) query.hasChanges = newFilters.hasChanges.toString()

      router.replace({ query })
    },
    { deep: true },
  )

  return {
    filters,
    hasActiveFilters,
    clearFilters,
  }
}

export function useCheckFilters() {
  const route = useRoute()
  const router = useRouter()

  const filters = ref<CheckFilters>({
    status: (route.query.checkStatus as any) || 'all',
    hasChanges: route.query.checkHasChanges ? route.query.checkHasChanges === 'true' : undefined,
    dateFrom: (route.query.dateFrom as string) || '',
    dateTo: (route.query.dateTo as string) || '',
  })

  const hasActiveFilters = computed(
    () =>
      filters.value.status !== 'all' ||
      filters.value.hasChanges !== undefined ||
      filters.value.dateFrom !== '' ||
      filters.value.dateTo !== '',
  )

  const clearFilters = () => {
    filters.value = {
      status: 'all',
      hasChanges: undefined,
      dateFrom: '',
      dateTo: '',
    }
  }

  // Quick filter presets
  const setQuickFilter = (preset: 'today' | 'week' | 'month' | 'changes-only') => {
    const now = new Date()

    switch (preset) {
      case 'today':
        filters.value.dateFrom = now.toISOString().split('T')[0]
        filters.value.dateTo = ''
        break
      case 'week':
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        filters.value.dateFrom = weekAgo.toISOString().split('T')[0]
        filters.value.dateTo = ''
        break
      case 'month':
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        filters.value.dateFrom = monthAgo.toISOString().split('T')[0]
        filters.value.dateTo = ''
        break
      case 'changes-only':
        filters.value.hasChanges = true
        break
    }
  }

  // Update URL query parameters when filters change
  watch(
    filters,
    (newFilters) => {
      const query: Record<string, string> = { ...route.query }

      if (newFilters.status && newFilters.status !== 'all') {
        query.checkStatus = newFilters.status
      } else {
        delete query.checkStatus
      }

      if (newFilters.hasChanges !== undefined) {
        query.checkHasChanges = newFilters.hasChanges.toString()
      } else {
        delete query.checkHasChanges
      }

      if (newFilters.dateFrom) {
        query.dateFrom = newFilters.dateFrom
      } else {
        delete query.dateFrom
      }

      if (newFilters.dateTo) {
        query.dateTo = newFilters.dateTo
      } else {
        delete query.dateTo
      }

      router.replace({ query })
    },
    { deep: true },
  )

  return {
    filters,
    hasActiveFilters,
    clearFilters,
    setQuickFilter,
  }
}
