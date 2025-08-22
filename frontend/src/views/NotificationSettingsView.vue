<!-- src/views/NotificationSettingsView.vue -->
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-3xl font-bold">Notification Settings</h1>
      <p class="text-muted-foreground">
        Configure how you want to be notified about website changes
      </p>
    </div>

    <!-- Settings Form -->
    <form @submit.prevent="handleSubmit" class="space-y-8">
      <!-- Email Notifications -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <MailIcon class="h-5 w-5 text-blue-600" />
            Email Notifications
          </CardTitle>
          <CardDescription>
            Receive email alerts when changes are detected on your monitored websites
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-center space-x-2">
            <input
              id="email-enabled"
              v-model="formData.email_enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="email-enabled">Enable email notifications</Label>
          </div>

          <div v-if="formData.email_enabled">
            <Label htmlFor="email-address">Email Address</Label>
            <Input
              id="email-address"
              v-model="formData.email_address"
              type="email"
              placeholder="your-email@example.com"
              :class="{ 'border-red-500': hasFieldError('email_address') }"
            />
            <div v-if="hasFieldError('email_address')" class="text-sm text-red-600 mt-1">
              {{ getFieldError('email_address') }}
            </div>
            <div class="text-sm text-muted-foreground mt-1">
              This email address will receive notifications about website changes
            </div>
          </div>

          <!-- Test Email Button -->
          <div v-if="formData.email_enabled && isEmailConfigured" class="pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              @click="testEmailNotification"
              :disabled="isTestingEmail"
            >
              <MailIcon class="h-4 w-4 mr-2" />
              {{ isTestingEmail ? 'Sending...' : 'Send Test Email' }}
            </Button>
            <p class="text-sm text-muted-foreground mt-2">
              Send a test notification to verify your email settings
            </p>
          </div>
        </CardContent>
      </Card>

      <!-- Telegram Notifications -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <MessageSquareIcon class="h-5 w-5 text-green-600" />
            Telegram Notifications
          </CardTitle>
          <CardDescription>
            Get instant notifications on Telegram when your websites change
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-center space-x-2">
            <input
              id="telegram-enabled"
              v-model="formData.telegram_enabled"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="telegram-enabled">Enable Telegram notifications</Label>
          </div>

          <div v-if="formData.telegram_enabled" class="space-y-4">
            <!-- Setup Instructions -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 class="font-medium mb-2">Telegram Setup Instructions:</h4>
              <ol class="list-decimal list-inside space-y-1 text-sm">
                <li>Create a Telegram bot by messaging <strong>@BotFather</strong></li>
                <li>Copy the bot token provided by BotFather</li>
                <li>Start a conversation with your bot</li>
                <li>Send a message to your bot, then visit this URL to get your chat ID:</li>
              </ol>
              <div
                v-if="formData.telegram_bot_token"
                class="mt-2 p-2 bg-white border rounded font-mono text-xs break-all"
              >
                https://api.telegram.org/bot{{ formData.telegram_bot_token }}/getUpdates
              </div>
            </div>

            <div>
              <Label htmlFor="telegram-bot-token">Bot Token</Label>
              <Input
                id="telegram-bot-token"
                v-model="formData.telegram_bot_token"
                type="password"
                placeholder="123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh"
                :class="{ 'border-red-500': hasFieldError('telegram_bot_token') }"
              />
              <div v-if="hasFieldError('telegram_bot_token')" class="text-sm text-red-600 mt-1">
                {{ getFieldError('telegram_bot_token') }}
              </div>
              <div class="text-sm text-muted-foreground mt-1">
                The bot token provided by @BotFather
              </div>
            </div>

            <div>
              <Label htmlFor="telegram-chat-id">Chat ID</Label>
              <Input
                id="telegram-chat-id"
                v-model="formData.telegram_chat_id"
                placeholder="123456789"
                :class="{ 'border-red-500': hasFieldError('telegram_chat_id') }"
              />
              <div v-if="hasFieldError('telegram_chat_id')" class="text-sm text-red-600 mt-1">
                {{ getFieldError('telegram_chat_id') }}
              </div>
              <div class="text-sm text-muted-foreground mt-1">
                Your Telegram chat ID (can be found in the bot getUpdates response)
              </div>
            </div>

            <!-- Test Telegram Button -->
            <div v-if="isTelegramConfigured" class="pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                @click="testTelegramNotification"
                :disabled="isTestingTelegram"
              >
                <MessageSquareIcon class="h-4 w-4 mr-2" />
                {{ isTestingTelegram ? 'Sending...' : 'Send Test Message' }}
              </Button>
              <p class="text-sm text-muted-foreground mt-2">
                Send a test notification to verify your Telegram settings
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Summary -->
      <Card>
        <CardHeader>
          <CardTitle>Notification Summary</CardTitle>
          <CardDescription> Review your current notification settings </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm">Email notifications:</span>
              <Badge :variant="isEmailConfigured ? 'default' : 'secondary'">
                {{ isEmailConfigured ? 'Configured' : 'Not configured' }}
              </Badge>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm">Telegram notifications:</span>
              <Badge :variant="isTelegramConfigured ? 'default' : 'secondary'">
                {{ isTelegramConfigured ? 'Configured' : 'Not configured' }}
              </Badge>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm">Total notification channels:</span>
              <Badge variant="outline">
                {{ (isEmailConfigured ? 1 : 0) + (isTelegramConfigured ? 1 : 0) }} active
              </Badge>
            </div>
          </div>

          <div
            v-if="!hasAnyNotifications"
            class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
          >
            <div class="flex items-center gap-2">
              <AlertTriangleIcon class="h-5 w-5 text-yellow-600" />
              <span class="font-medium text-yellow-800">No notifications configured</span>
            </div>
            <p class="text-sm text-yellow-700 mt-1">
              You won't receive any alerts about website changes. Consider enabling at least one
              notification method.
            </p>
          </div>
        </CardContent>
      </Card>

      <!-- Form Actions -->
      <div class="flex gap-4">
        <Button type="submit" :disabled="isSubmitting || !isDirty">
          {{ isSubmitting ? 'Saving...' : 'Save Settings' }}
        </Button>
        <Button type="button" variant="outline" @click="reset" :disabled="isSubmitting">
          Reset
        </Button>
      </div>
    </form>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="fixed bottom-4 right-4 z-50">
      <Card class="bg-green-50 border-green-200">
        <CardContent class="p-4 flex items-center gap-2">
          <CheckCircleIcon class="h-5 w-5 text-green-600" />
          <span class="text-green-700">{{ successMessage }}</span>
          <Button variant="ghost" size="sm" @click="successMessage = ''" class="ml-auto">
            <XIcon class="h-4 w-4" />
          </Button>
        </CardContent>
      </Card>
    </div>

    <div v-if="error" class="fixed bottom-4 right-4 z-50">
      <Card class="bg-red-50 border-red-200">
        <CardContent class="p-4 flex items-center gap-2">
          <AlertCircleIcon class="h-5 w-5 text-red-600" />
          <span class="text-red-700">{{ error }}</span>
          <Button variant="ghost" size="sm" @click="clearError" class="ml-auto">
            <XIcon class="h-4 w-4" />
          </Button>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import {
  AlertCircleIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  MailIcon,
  MessageSquareIcon,
  XIcon,
} from 'lucide-vue-next'
import { storeToRefs } from 'pinia'

import { useWebsiteStore } from '@/stores/website'

import { useNotificationSettings } from '@/composables/useNotificationSettings'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const websiteStore = useWebsiteStore()
const { notificationSettings, notificationLoading, error } = storeToRefs(websiteStore)

const {
  formData,
  isSubmitting,
  validate,
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
} = useNotificationSettings(notificationSettings.value)

const successMessage = ref('')
const isTestingEmail = ref(false)
const isTestingTelegram = ref(false)

const handleSubmit = async () => {
  if (!validate()) {
    return
  }

  isSubmitting.value = true

  try {
    await websiteStore.updateNotificationSettings(formData.value)
    successMessage.value = 'Notification settings saved successfully'
    clearErrors()
  } catch (err: any) {
    console.error('Failed to save notification settings:', err)
  } finally {
    isSubmitting.value = false
  }
}

const testEmailNotification = async () => {
  isTestingEmail.value = true
  setTestingState('email', true)

  try {
    await websiteStore.testNotification('email')
    successMessage.value = 'Test email sent successfully! Check your inbox.'
  } catch (err: any) {
    console.error('Failed to send test email:', err)
  } finally {
    isTestingEmail.value = false
    setTestingState('email', false)
  }
}

const testTelegramNotification = async () => {
  isTestingTelegram.value = true
  setTestingState('telegram', true)

  try {
    await websiteStore.testNotification('telegram')
    successMessage.value = 'Test Telegram message sent successfully!'
  } catch (err: any) {
    console.error('Failed to send test Telegram message:', err)
  } finally {
    isTestingTelegram.value = false
    setTestingState('telegram', false)
  }
}

const clearError = () => {
  websiteStore.clearError()
}

onMounted(async () => {
  await websiteStore.fetchNotificationSettings()
})
</script>
