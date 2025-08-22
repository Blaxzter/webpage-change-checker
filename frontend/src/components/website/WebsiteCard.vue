<!-- src/components/website/WebsiteCard.vue -->
<template>
  <Card class="overflow-hidden hover:shadow-lg transition-shadow">
    <CardHeader class="pb-3">
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <CardTitle class="text-lg truncate">{{ website.name }}</CardTitle>
          <CardDescription class="mt-1">
            <a
              :href="website.url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-blue-600 hover:text-blue-800 hover:underline truncate block"
            >
              {{ website.url }}
            </a>
          </CardDescription>
        </div>
        <Badge :variant="website.is_active ? 'default' : 'secondary'">
          {{ website.is_active ? 'Active' : 'Inactive' }}
        </Badge>
      </div>
    </CardHeader>

    <CardContent class="pb-3">
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-muted-foreground">Check Interval:</span>
          <div class="font-medium">{{ formatInterval(website.check_interval_minutes || 60) }}</div>
        </div>
        <div>
          <span class="text-muted-foreground">Notifications:</span>
          <div class="flex gap-1 mt-1">
            <Badge v-if="website.email_notifications" variant="outline" class="text-xs">
              Email
            </Badge>
            <Badge v-if="website.telegram_notifications" variant="outline" class="text-xs">
              Telegram
            </Badge>
            <span
              v-if="!website.email_notifications && !website.telegram_notifications"
              class="text-muted-foreground text-xs"
            >
              None
            </span>
          </div>
        </div>
      </div>

      <!-- Last check info if available -->
      <div v-if="lastCheckAt || lastChangeAt" class="mt-3 pt-3 border-t">
        <div class="grid grid-cols-1 gap-2 text-sm">
          <div v-if="lastCheckAt">
            <span class="text-muted-foreground">Last Check:</span>
            <div class="font-medium">{{ formatRelativeTime(lastCheckAt) }}</div>
          </div>
          <div v-if="lastChangeAt">
            <span class="text-muted-foreground">Last Change:</span>
            <div class="font-medium text-orange-600">{{ formatRelativeTime(lastChangeAt) }}</div>
          </div>
        </div>
      </div>

      <!-- Ignore selectors info -->
      <div v-if="website.ignore_selectors && website.ignore_selectors.length > 0" class="mt-3">
        <span class="text-muted-foreground text-xs">
          {{ website.ignore_selectors.length }} CSS selector(s) ignored
        </span>
      </div>
    </CardContent>

    <CardFooter v-if="showActions" class="pt-0 flex gap-2">
      <Button variant="outline" size="sm" @click="$emit('view', website)" class="flex-1">
        <EyeIcon class="h-4 w-4 mr-1" />
        View
      </Button>
      <Button variant="outline" size="sm" @click="$emit('edit', website)">
        <EditIcon class="h-4 w-4 mr-1" />
        Edit
      </Button>
      <Button
        variant="outline"
        size="sm"
        @click="$emit('check', website.id)"
        :disabled="isChecking"
      >
        <RefreshCwIcon class="h-4 w-4 mr-1" :class="{ 'animate-spin': isChecking }" />
        Check
      </Button>
      <Button variant="destructive" size="sm" @click="$emit('delete', website.id)">
        <TrashIcon class="h-4 w-4" />
      </Button>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { EditIcon, EyeIcon, RefreshCwIcon, TrashIcon } from 'lucide-vue-next'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

import type { WebsiteResponse } from '@/types/website'

interface Props {
  website: WebsiteResponse
  showActions?: boolean
  isChecking?: boolean
  lastCheckAt?: string | null
  lastChangeAt?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
  isChecking: false,
})

defineEmits<{
  view: [website: WebsiteResponse]
  edit: [website: WebsiteResponse]
  check: [websiteId: string]
  delete: [websiteId: string]
}>()

const formatInterval = (minutes: number): string => {
  if (minutes < 60) {
    return `${minutes} min`
  } else if (minutes < 1440) {
    const hours = Math.floor(minutes / 60)
    return `${hours} hour${hours > 1 ? 's' : ''}`
  } else {
    const days = Math.floor(minutes / 1440)
    return `${days} day${days > 1 ? 's' : ''}`
  }
}

const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) {
    return 'Just now'
  } else if (diffMins < 60) {
    return `${diffMins} min ago`
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  } else {
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }
}
</script>
