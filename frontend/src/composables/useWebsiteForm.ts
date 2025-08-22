// src/composables/useWebsiteForm.ts
import { computed, ref } from 'vue'

import { z } from 'zod'

import { websiteCreateSchema, websiteUpdateSchema } from '@/types/website'
import type { WebsiteCreate, WebsiteResponse, WebsiteUpdate } from '@/types/website'

export function useWebsiteForm(initialData?: Partial<WebsiteResponse>) {
  const isEditing = computed(() => !!initialData?.id)

  const formData = ref<WebsiteCreate>({
    name: initialData?.name || '',
    url: initialData?.url || '',
    check_interval_minutes: initialData?.check_interval_minutes || 60,
    is_active: initialData?.is_active ?? true,
    ignore_selectors: initialData?.ignore_selectors || [],
    email_notifications: initialData?.email_notifications ?? true,
    telegram_notifications: initialData?.telegram_notifications ?? false,
  })

  const errors = ref<Record<string, string>>({})
  const isSubmitting = ref(false)

  // Common check intervals
  const intervalOptions = [
    { label: '5 minutes', value: 5 },
    { label: '15 minutes', value: 15 },
    { label: '30 minutes', value: 30 },
    { label: '1 hour', value: 60 },
    { label: '2 hours', value: 120 },
    { label: '6 hours', value: 360 },
    { label: '12 hours', value: 720 },
    { label: '1 day', value: 1440 },
    { label: '1 week', value: 10080 },
  ]

  const validate = () => {
    errors.value = {}

    try {
      const schema = isEditing.value ? websiteUpdateSchema : websiteCreateSchema
      schema.parse(formData.value)
      return true
    } catch (error) {
      if (error instanceof z.ZodError) {
        error.errors.forEach((err) => {
          const field = err.path.join('.')
          errors.value[field] = err.message
        })
      }
      return false
    }
  }

  const getFieldError = (field: string) => {
    return errors.value[field] || ''
  }

  const hasFieldError = (field: string) => {
    return !!errors.value[field]
  }

  const clearErrors = () => {
    errors.value = {}
  }

  const reset = () => {
    if (initialData) {
      formData.value = {
        name: initialData.name || '',
        url: initialData.url || '',
        check_interval_minutes: initialData.check_interval_minutes || 60,
        is_active: initialData.is_active ?? true,
        ignore_selectors: initialData.ignore_selectors || [],
        email_notifications: initialData.email_notifications ?? true,
        telegram_notifications: initialData.telegram_notifications ?? false,
      }
    } else {
      formData.value = {
        name: '',
        url: '',
        check_interval_minutes: 60,
        is_active: true,
        ignore_selectors: [],
        email_notifications: true,
        telegram_notifications: false,
      }
    }
    clearErrors()
  }

  // Helper to add/remove ignore selectors
  const addIgnoreSelector = (selector: string) => {
    if (selector.trim() && !formData.value.ignore_selectors?.includes(selector.trim())) {
      if (!formData.value.ignore_selectors) {
        formData.value.ignore_selectors = []
      }
      formData.value.ignore_selectors.push(selector.trim())
    }
  }

  const removeIgnoreSelector = (index: number) => {
    if (
      formData.value.ignore_selectors &&
      index >= 0 &&
      index < formData.value.ignore_selectors.length
    ) {
      formData.value.ignore_selectors.splice(index, 1)
    }
  }

  // Convert to update data for PATCH requests
  const getUpdateData = (): WebsiteUpdate => {
    if (!isEditing.value) {
      throw new Error('Cannot get update data for new website')
    }

    return {
      name: formData.value.name,
      url: formData.value.url,
      check_interval_minutes: formData.value.check_interval_minutes,
      is_active: formData.value.is_active,
      ignore_selectors: formData.value.ignore_selectors,
      email_notifications: formData.value.email_notifications,
      telegram_notifications: formData.value.telegram_notifications,
    }
  }

  const isDirty = computed(() => {
    if (!initialData) return true

    return (
      formData.value.name !== (initialData.name || '') ||
      formData.value.url !== (initialData.url || '') ||
      formData.value.check_interval_minutes !== (initialData.check_interval_minutes || 60) ||
      formData.value.is_active !== (initialData.is_active ?? true) ||
      JSON.stringify(formData.value.ignore_selectors) !==
        JSON.stringify(initialData.ignore_selectors || []) ||
      formData.value.email_notifications !== (initialData.email_notifications ?? true) ||
      formData.value.telegram_notifications !== (initialData.telegram_notifications ?? false)
    )
  })

  return {
    formData,
    errors,
    isSubmitting,
    isEditing,
    intervalOptions,
    validate,
    getFieldError,
    hasFieldError,
    clearErrors,
    reset,
    addIgnoreSelector,
    removeIgnoreSelector,
    getUpdateData,
    isDirty,
  }
}
