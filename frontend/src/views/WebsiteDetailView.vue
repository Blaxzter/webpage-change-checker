<!-- src/views/WebsiteDetailView.vue -->
<template>
  <div v-if="currentWebsite" class="space-y-6">
    <!-- Header -->
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-2">
          <Button variant="ghost" size="sm" @click="$router.back()">
            <ArrowLeftIcon class="h-4 w-4 mr-1" />
            Back
          </Button>
        </div>
        <h1 class="text-3xl font-bold truncate">{{ currentWebsite.name }}</h1>
        <div class="flex items-center gap-4 mt-2">
          <a
            :href="currentWebsite.url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-blue-600 hover:text-blue-800 hover:underline"
          >
            {{ currentWebsite.url }}
            <ExternalLinkIcon class="h-4 w-4 inline ml-1" />
          </a>
          <Badge :variant="currentWebsite.is_active ? 'default' : 'secondary'">
            {{ currentWebsite.is_active ? 'Active' : 'Inactive' }}
          </Badge>
        </div>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" @click="triggerCheck" :disabled="checkLoading">
          <RefreshCwIcon class="h-4 w-4 mr-2" :class="{ 'animate-spin': checkLoading }" />
          Check Now
        </Button>
        <Button variant="outline" @click="editWebsite">
          <EditIcon class="h-4 w-4 mr-2" />
          Edit
        </Button>
      </div>
    </div>

    <!-- Website Overview Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent class="p-4">
          <div class="flex items-center gap-2">
            <ClockIcon class="h-5 w-5 text-blue-600" />
            <div>
              <p class="text-sm text-muted-foreground">Check Interval</p>
              <p class="font-medium">
                {{ formatInterval(currentWebsite.check_interval_minutes || 60) }}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="p-4">
          <div class="flex items-center gap-2">
            <CalendarIcon class="h-5 w-5 text-green-600" />
            <div>
              <p class="text-sm text-muted-foreground">Last Check</p>
              <p class="font-medium">
                {{
                  currentWebsite.last_check_at
                    ? formatRelativeTime(currentWebsite.last_check_at)
                    : 'Never'
                }}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="p-4">
          <div class="flex items-center gap-2">
            <AlertTriangleIcon class="h-5 w-5 text-orange-600" />
            <div>
              <p class="text-sm text-muted-foreground">Last Change</p>
              <p class="font-medium">
                {{
                  currentWebsite.last_change_at
                    ? formatRelativeTime(currentWebsite.last_change_at)
                    : 'No changes'
                }}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="p-4">
          <div class="flex items-center gap-2">
            <BellIcon class="h-5 w-5 text-purple-600" />
            <div>
              <p class="text-sm text-muted-foreground">Notifications</p>
              <div class="flex gap-1">
                <Badge v-if="currentWebsite.email_notifications" variant="outline" class="text-xs">
                  Email
                </Badge>
                <Badge
                  v-if="currentWebsite.telegram_notifications"
                  variant="outline"
                  class="text-xs"
                >
                  Telegram
                </Badge>
                <span
                  v-if="
                    !currentWebsite.email_notifications && !currentWebsite.telegram_notifications
                  "
                  class="text-xs text-muted-foreground"
                >
                  None
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Configuration Details -->
    <Card>
      <CardHeader>
        <CardTitle>Configuration</CardTitle>
        <CardDescription> Current monitoring settings for this website </CardDescription>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="font-medium mb-2">Monitoring Settings</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-muted-foreground">Status:</span>
                <span>{{ currentWebsite.is_active ? 'Active' : 'Inactive' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Check Interval:</span>
                <span>{{ formatInterval(currentWebsite.check_interval_minutes || 60) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Email Notifications:</span>
                <span>{{ currentWebsite.email_notifications ? 'Enabled' : 'Disabled' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Telegram Notifications:</span>
                <span>{{ currentWebsite.telegram_notifications ? 'Enabled' : 'Disabled' }}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 class="font-medium mb-2">Ignored Elements</h4>
            <div
              v-if="currentWebsite.ignore_selectors && currentWebsite.ignore_selectors.length > 0"
            >
              <div class="space-y-1">
                <Badge
                  v-for="selector in currentWebsite.ignore_selectors"
                  :key="selector"
                  variant="outline"
                  class="mr-1 mb-1 text-xs font-mono"
                >
                  {{ selector }}
                </Badge>
              </div>
            </div>
            <p v-else class="text-sm text-muted-foreground">No CSS selectors are being ignored</p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Check History -->
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle>Check History</CardTitle>
            <CardDescription> Recent monitoring results for this website </CardDescription>
          </div>
          <div class="flex gap-2">
            <!-- Check Filters -->
            <select v-model="checkStatusFilter" class="text-sm border rounded px-2 py-1">
              <option value="all">All Checks</option>
              <option value="success">Success Only</option>
              <option value="changed">Changes Only</option>
              <option value="failed">Failed Only</option>
            </select>
            <Button variant="outline" size="sm" @click="refreshChecks" :disabled="checkLoading">
              <RefreshCwIcon class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div v-if="checkLoading && checks.length === 0" class="space-y-4">
          <div v-for="i in 5" :key="i" class="animate-pulse">
            <div class="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>

        <div v-else-if="filteredChecks.length === 0" class="text-center py-8">
          <HistoryIcon class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">
            {{ checks.length === 0 ? 'No checks yet' : 'No checks match your filter' }}
          </h3>
          <p class="text-muted-foreground mb-4">
            {{
              checks.length === 0
                ? "This website hasn't been checked yet"
                : 'Try adjusting your filter criteria'
            }}
          </p>
          <Button v-if="checks.length === 0" @click="triggerCheck" :disabled="checkLoading">
            <PlayIcon class="h-4 w-4 mr-2" />
            Run First Check
          </Button>
        </div>

        <div v-else class="space-y-4">
          <WebsiteCheckCard
            v-for="check in filteredChecks"
            :key="check.id"
            :check="check"
            :show-website-name="false"
            @recheck="triggerCheck"
            @view-website="() => router.push(`/app/websites/${websiteId}`)"
          />

          <!-- Load More -->
          <div v-if="checkPagination.page < checkPagination.totalPages" class="text-center">
            <Button variant="outline" @click="loadMoreChecks" :disabled="checkLoading">
              {{ checkLoading ? 'Loading...' : 'Load More Checks' }}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Edit Dialog -->
    <WebsiteFormDialog
      v-model:open="showEditDialog"
      :website="currentWebsite"
      @success="handleWebsiteUpdated"
      @error="handleError"
    />
  </div>

  <div v-else-if="loading" class="space-y-6">
    <!-- Loading skeleton -->
    <div class="animate-pulse">
      <div class="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
      <div class="h-6 bg-gray-200 rounded w-1/2 mb-8"></div>
      <div class="grid grid-cols-4 gap-4 mb-8">
        <div v-for="i in 4" :key="i" class="h-20 bg-gray-200 rounded"></div>
      </div>
      <div class="h-64 bg-gray-200 rounded"></div>
    </div>
  </div>

  <div v-else class="text-center py-12">
    <AlertCircleIcon class="h-16 w-16 mx-auto text-red-500 mb-4" />
    <h2 class="text-2xl font-bold mb-2">Website Not Found</h2>
    <p class="text-muted-foreground mb-6">
      The website you're looking for doesn't exist or you don't have permission to view it.
    </p>
    <Button @click="$router.push('/app/websites')">
      <ArrowLeftIcon class="h-4 w-4 mr-2" />
      Back to Websites
    </Button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import {
  AlertCircleIcon,
  AlertTriangleIcon,
  ArrowLeftIcon,
  BellIcon,
  CalendarIcon,
  ClockIcon,
  EditIcon,
  ExternalLinkIcon,
  HistoryIcon,
  PlayIcon,
  RefreshCwIcon,
} from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'

import { useWebsiteStore } from '@/stores/website'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import WebsiteCheckCard from '@/components/website/WebsiteCheckCard.vue'
import WebsiteFormDialog from '@/components/website/WebsiteFormDialog.vue'

import type { CheckStatus } from '@/types/website'

const route = useRoute()
const router = useRouter()
const websiteStore = useWebsiteStore()

const { currentWebsite, checks, loading, checkLoading, error, checkPagination } =
  storeToRefs(websiteStore)

const websiteId = computed(() => route.params.id as string)
const showEditDialog = ref(false)
const checkStatusFilter = ref<CheckStatus | 'all'>('all')

const filteredChecks = computed(() => {
  if (checkStatusFilter.value === 'all') {
    return checks.value
  }
  return checks.value.filter((check) => check.status === checkStatusFilter.value)
})

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

const refreshChecks = async () => {
  if (websiteId.value) {
    await websiteStore.fetchWebsiteChecks(websiteId.value, 1, true)
  }
}

const loadMoreChecks = async () => {
  if (websiteId.value) {
    await websiteStore.fetchWebsiteChecks(websiteId.value, checkPagination.value.page + 1, false)
  }
}

const triggerCheck = async () => {
  if (websiteId.value) {
    await websiteStore.triggerManualCheck([websiteId.value])
    // Refresh data after a short delay
    setTimeout(() => {
      if (websiteId.value) {
        websiteStore.fetchWebsiteDetails(websiteId.value, 10)
        refreshChecks()
      }
    }, 2000)
  }
}

const editWebsite = () => {
  showEditDialog.value = true
}

const handleWebsiteUpdated = () => {
  showEditDialog.value = false
  if (websiteId.value) {
    websiteStore.fetchWebsiteDetails(websiteId.value, 10)
  }
}

const handleError = (errorMessage: string) => {
  console.error('Website operation error:', errorMessage)
}

// Watch for route changes
watch(
  websiteId,
  async (newId) => {
    if (newId) {
      await Promise.all([
        websiteStore.fetchWebsiteDetails(newId, 10),
        websiteStore.fetchWebsiteChecks(newId, 1, true),
      ])
    }
  },
  { immediate: true },
)

onMounted(async () => {
  if (websiteId.value) {
    await Promise.all([
      websiteStore.fetchWebsiteDetails(websiteId.value, 10),
      websiteStore.fetchWebsiteChecks(websiteId.value, 1, true),
    ])
  }
})
</script>
