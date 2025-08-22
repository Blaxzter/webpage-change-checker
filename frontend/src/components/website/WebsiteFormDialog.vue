<!-- src/components/website/WebsiteFormDialog.vue -->
<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>
          {{ isEditing ? 'Edit Website' : 'Add New Website' }}
        </DialogTitle>
        <DialogDescription>
          Configure your website monitoring settings. Changes are saved automatically.
        </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Basic Information -->
        <div class="space-y-4">
          <div>
            <Label htmlFor="name">Website Name *</Label>
            <Input
              id="name"
              v-model="formData.name"
              placeholder="My Website"
              :class="{ 'border-red-500': hasFieldError('name') }"
            />
            <div v-if="hasFieldError('name')" class="text-sm text-red-600 mt-1">
              {{ getFieldError('name') }}
            </div>
          </div>

          <div>
            <Label htmlFor="url">Website URL *</Label>
            <Input
              id="url"
              v-model="formData.url"
              type="url"
              placeholder="https://example.com"
              :class="{ 'border-red-500': hasFieldError('url') }"
            />
            <div v-if="hasFieldError('url')" class="text-sm text-red-600 mt-1">
              {{ getFieldError('url') }}
            </div>
          </div>
        </div>

        <!-- Monitoring Settings -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium">Monitoring Settings</h3>

          <div>
            <Label htmlFor="interval">Check Interval</Label>
            <select
              id="interval"
              v-model="formData.check_interval_minutes"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option v-for="option in intervalOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <div class="flex items-center space-x-2">
            <input
              id="active"
              v-model="formData.is_active"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="active">Enable monitoring</Label>
          </div>
        </div>

        <!-- Ignore Selectors -->
        <div class="space-y-4">
          <div>
            <Label>CSS Selectors to Ignore</Label>
            <p class="text-sm text-muted-foreground">
              Specify CSS selectors for elements that should be ignored during change detection.
            </p>
          </div>

          <div class="space-y-2">
            <div
              v-for="(selector, index) in formData.ignore_selectors || []"
              :key="index"
              class="flex items-center gap-2"
            >
              <Input :value="selector" readonly class="flex-1" />
              <Button
                type="button"
                variant="outline"
                size="sm"
                @click="removeIgnoreSelector(index)"
              >
                <TrashIcon class="h-4 w-4" />
              </Button>
            </div>

            <div class="flex items-center gap-2">
              <Input
                v-model="newSelector"
                placeholder=".timestamp, #dynamic-content"
                class="flex-1"
                @keyup.enter="addNewSelector"
              />
              <Button
                type="button"
                variant="outline"
                @click="addNewSelector"
                :disabled="!newSelector.trim()"
              >
                <PlusIcon class="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
          </div>
        </div>

        <!-- Notification Settings -->
        <div class="space-y-4">
          <h3 class="text-lg font-medium">Notifications</h3>

          <div class="flex items-center space-x-2">
            <input
              id="email"
              v-model="formData.email_notifications"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="email">Send email notifications</Label>
          </div>

          <div class="flex items-center space-x-2">
            <input
              id="telegram"
              v-model="formData.telegram_notifications"
              type="checkbox"
              class="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="telegram">Send Telegram notifications</Label>
          </div>

          <div class="text-sm text-muted-foreground">
            Configure notification settings in your account preferences.
          </div>
        </div>

        <!-- Form Actions -->
        <DialogFooter>
          <Button type="button" variant="outline" @click="handleCancel" :disabled="isSubmitting">
            Cancel
          </Button>
          <Button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving...' : isEditing ? 'Update Website' : 'Create Website' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

import { PlusIcon, TrashIcon } from 'lucide-vue-next'

import { useWebsiteForm } from '@/composables/useWebsiteForm'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

import type { WebsiteResponse } from '@/types/website'

interface Props {
  open: boolean
  website?: WebsiteResponse | null
}

const props = withDefaults(defineProps<Props>(), {
  website: null,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: [website: WebsiteResponse]
  error: [error: string]
}>()

const isOpen = ref(props.open)
const newSelector = ref('')

const {
  formData,
  isSubmitting,
  isEditing,
  intervalOptions,
  validate,
  getFieldError,
  hasFieldError,
  reset,
  addIgnoreSelector,
  removeIgnoreSelector,
  getUpdateData,
  isDirty,
} = useWebsiteForm(props.website)

// Watch for dialog open/close
watch(
  () => props.open,
  (newValue) => {
    isOpen.value = newValue
    if (newValue) {
      reset() // Reset form when dialog opens
    }
  },
)

watch(isOpen, (newValue) => {
  emit('update:open', newValue)
})

// Watch for website prop changes
watch(
  () => props.website,
  () => {
    reset()
  },
)

const addNewSelector = () => {
  if (newSelector.value.trim()) {
    addIgnoreSelector(newSelector.value.trim())
    newSelector.value = ''
  }
}

const handleSubmit = async () => {
  if (!validate()) {
    return
  }

  isSubmitting.value = true

  try {
    // Import store here to avoid circular dependencies
    const { useWebsiteStore } = await import('@/stores/website')
    const websiteStore = useWebsiteStore()

    let result: WebsiteResponse

    if (isEditing.value && props.website) {
      result = await websiteStore.updateWebsite(props.website.id, getUpdateData())
    } else {
      result = await websiteStore.createWebsite(formData.value)
    }

    emit('success', result)
    isOpen.value = false
  } catch (error: any) {
    emit('error', error.message || 'Failed to save website')
  } finally {
    isSubmitting.value = false
  }
}

const handleCancel = () => {
  if (isDirty.value) {
    if (confirm('You have unsaved changes. Are you sure you want to cancel?')) {
      isOpen.value = false
    }
  } else {
    isOpen.value = false
  }
}
</script>
