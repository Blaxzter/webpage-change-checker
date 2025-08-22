<!-- src/components/website/WebsiteCheckCard.vue -->
<template>
  <Card class="overflow-hidden">
    <CardHeader class="pb-3">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <Badge :variant="getStatusVariant(check.status)">
              {{ getStatusLabel(check.status) }}
            </Badge>
            <Badge v-if="check.changes_detected" variant="destructive" class="text-xs">
              Changes Detected
            </Badge>
          </div>
          <CardDescription class="mt-1">
            {{ formatDateTime(check.created_at) }}
          </CardDescription>
        </div>
        <div v-if="check.response_time_ms" class="text-right">
          <div class="text-sm font-medium">{{ check.response_time_ms }}ms</div>
          <div class="text-xs text-muted-foreground">Response Time</div>
        </div>
      </div>
    </CardHeader>

    <CardContent>
      <!-- Change Summary -->
      <div v-if="check.change_summary" class="mb-3">
        <div class="text-sm font-medium text-muted-foreground mb-1">Changes Detected:</div>
        <div class="text-sm bg-orange-50 border border-orange-200 rounded-md p-2">
          {{ check.change_summary }}
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="check.error_message" class="mb-3">
        <div class="text-sm font-medium text-muted-foreground mb-1">Error:</div>
        <div class="text-sm bg-red-50 border border-red-200 rounded-md p-2 text-red-700">
          {{ check.error_message }}
        </div>
      </div>

      <!-- Technical Details -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div v-if="check.content_hash">
          <span class="text-muted-foreground">Content Hash:</span>
          <div class="font-mono text-xs mt-1 truncate">{{ check.content_hash }}</div>
        </div>
        <div v-if="check.screenshot_path">
          <span class="text-muted-foreground">Screenshot:</span>
          <div class="mt-1">
            <Button variant="outline" size="sm" @click="viewScreenshot" class="text-xs">
              <ImageIcon class="h-3 w-3 mr-1" />
              View Screenshot
            </Button>
          </div>
        </div>
      </div>

      <!-- Website Name (if showing for multiple websites) -->
      <div v-if="showWebsiteName && websiteName" class="mt-3 pt-3 border-t">
        <div class="text-sm">
          <span class="text-muted-foreground">Website:</span>
          <span class="font-medium ml-1">{{ websiteName }}</span>
        </div>
      </div>
    </CardContent>

    <!-- Actions -->
    <CardFooter v-if="showActions" class="pt-0 flex gap-2">
      <Button v-if="check.screenshot_path" variant="outline" size="sm" @click="viewScreenshot">
        <ImageIcon class="h-4 w-4 mr-1" />
        Screenshot
      </Button>
      <Button variant="outline" size="sm" @click="$emit('recheck', check.website_id)">
        <RefreshCwIcon class="h-4 w-4 mr-1" />
        Check Again
      </Button>
      <Button
        v-if="check.changes_detected"
        variant="outline"
        size="sm"
        @click="$emit('viewWebsite', check.website_id)"
      >
        <ExternalLinkIcon class="h-4 w-4 mr-1" />
        View Website
      </Button>
    </CardFooter>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { ExternalLinkIcon, ImageIcon, RefreshCwIcon } from 'lucide-vue-next'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader } from '@/components/ui/card'

import type { CheckStatus, WebsiteCheckResponse } from '@/types/website'

interface Props {
  check: WebsiteCheckResponse
  showWebsiteName?: boolean
  websiteName?: string
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showWebsiteName: false,
  showActions: true,
})

defineEmits<{
  recheck: [websiteId: string]
  viewWebsite: [websiteId: string]
  viewScreenshot: [screenshotPath: string]
}>()

const getStatusVariant = (status: CheckStatus) => {
  switch (status) {
    case 'success':
      return 'default'
    case 'changed':
      return 'destructive'
    case 'failed':
      return 'destructive'
    case 'pending':
      return 'secondary'
    default:
      return 'secondary'
  }
}

const getStatusLabel = (status: CheckStatus) => {
  switch (status) {
    case 'success':
      return 'Success'
    case 'changed':
      return 'Changed'
    case 'failed':
      return 'Failed'
    case 'pending':
      return 'Pending'
    default:
      return status
  }
}

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const viewScreenshot = () => {
  if (props.check.screenshot_path) {
    // For now, we'll emit an event. In a real app, you might open a modal
    // or navigate to a screenshot viewer
    console.log('View screenshot:', props.check.screenshot_path)
    // You could implement a screenshot viewer modal here
  }
}
</script>
