// src/composables/useNotificationSettings.ts
import { computed, ref } from 'vue'

import { z } from 'zod'

import { notificationSettingsUpdateSchema } from '@/types/website'
import type {
  NotificationChannel,
  NotificationSettingsResponse,
  NotificationSettingsUpdate,
} from '@/types/website'

export function useNotificationSettings(initialData?: NotificationSettingsResponse | null) {
  const formData = ref<NotificationSettingsUpdate>({
    email_address: initialData?.email_address || '',
    email_enabled: initialData?.email_enabled ?? true,
    telegram_chat_id: initialData?.telegram_chat_id || '',
    telegram_enabled: initialData?.telegram_enabled ?? false,
    telegram_bot_token: initialData?.telegram_bot_token || '',
  })

  const errors = ref<Record<string, string>>({})
  const isSubmitting = ref(false)
  const isTestingEmail = ref(false)
  const isTestingTelegram = ref(false)

  const validate = () => {
    errors.value = {}

    try {
      notificationSettingsUpdateSchema.parse(formData.value)
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

  const validateField = (field: keyof NotificationSettingsUpdate) => {
    // Clear previous error for this field
    delete errors.value[field]

    try {
      const fieldSchema = notificationSettingsUpdateSchema.shape[field]
      if (fieldSchema) {
        fieldSchema.parse(formData.value[field])
      }
      return true
    } catch (error) {
      if (error instanceof z.ZodError) {
        errors.value[field] = error.errors[0]?.message || 'Invalid value'
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
        email_address: initialData.email_address || '',
        email_enabled: initialData.email_enabled ?? true,
        telegram_chat_id: initialData.telegram_chat_id || '',
        telegram_enabled: initialData.telegram_enabled ?? false,
        telegram_bot_token: initialData.telegram_bot_token || '',
      }
    } else {
      formData.value = {
        email_address: '',
        email_enabled: true,
        telegram_chat_id: '',
        telegram_enabled: false,
        telegram_bot_token: '',
      }
    }
    clearErrors()
  }

  const isDirty = computed(() => {
    if (!initialData) return true

    return (
      formData.value.email_address !== (initialData.email_address || '') ||
      formData.value.email_enabled !== (initialData.email_enabled ?? true) ||
      formData.value.telegram_chat_id !== (initialData.telegram_chat_id || '') ||
      formData.value.telegram_enabled !== (initialData.telegram_enabled ?? false) ||
      formData.value.telegram_bot_token !== (initialData.telegram_bot_token || '')
    )
  })

  // Computed validation states
  const isEmailConfigured = computed(() => {
    return !!(formData.value.email_address && formData.value.email_enabled)
  })

  const isTelegramConfigured = computed(() => {
    return !!(
      formData.value.telegram_chat_id &&
      formData.value.telegram_bot_token &&
      formData.value.telegram_enabled
    )
  })

  const hasAnyNotifications = computed(() => {
    return isEmailConfigured.value || isTelegramConfigured.value
  })

  // Helper functions for testing notifications
  const setTestingState = (channel: NotificationChannel, testing: boolean) => {
    if (channel === 'email') {
      isTestingEmail.value = testing
    } else if (channel === 'telegram') {
      isTestingTelegram.value = testing
    }
  }

  const isTestingChannel = (channel: NotificationChannel) => {
    return channel === 'email' ? isTestingEmail.value : isTestingTelegram.value
  }

  return {
    formData,
    errors,
    isSubmitting,
    isTestingEmail,
    isTestingTelegram,
    validate,
    validateField,
    getFieldError,
    hasFieldError,
    clearErrors,
    reset,
    isDirty,
    isEmailConfigured,
    isTelegramConfigured,
    hasAnyNotifications,
    setTestingState,
    isTestingChannel,
  }
}
