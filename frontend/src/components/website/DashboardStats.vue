<!-- src/components/website/DashboardStats.vue -->
<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <!-- Total Websites -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Total Websites</p>
            <p class="text-2xl font-bold">{{ stats?.total_websites || 0 }}</p>
          </div>
          <div class="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
            <GlobeIcon class="h-6 w-6 text-blue-600" />
          </div>
        </div>
        <div v-if="stats?.active_websites !== undefined" class="mt-2">
          <p class="text-xs text-muted-foreground">
            {{ stats.active_websites }} active,
            {{ stats.total_websites - stats.active_websites }} inactive
          </p>
        </div>
      </CardContent>
    </Card>

    <!-- Total Checks -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Total Checks</p>
            <p class="text-2xl font-bold">{{ formatNumber(stats?.total_checks || 0) }}</p>
          </div>
          <div class="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
            <ActivityIcon class="h-6 w-6 text-green-600" />
          </div>
        </div>
        <div v-if="stats?.checks_last_24h !== undefined" class="mt-2">
          <p class="text-xs text-muted-foreground">{{ stats.checks_last_24h }} in last 24 hours</p>
        </div>
      </CardContent>
    </Card>

    <!-- Changes Detected -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Sites with Changes</p>
            <p class="text-2xl font-bold">{{ stats?.websites_with_changes || 0 }}</p>
          </div>
          <div class="h-12 w-12 rounded-full bg-orange-100 flex items-center justify-center">
            <AlertTriangleIcon class="h-6 w-6 text-orange-600" />
          </div>
        </div>
        <div v-if="stats?.total_websites" class="mt-2">
          <p class="text-xs text-muted-foreground">
            {{ getChangePercentage() }}% of total websites
          </p>
        </div>
      </CardContent>
    </Card>

    <!-- Average Response Time -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Avg Response Time</p>
            <p class="text-2xl font-bold">
              {{
                stats?.avg_response_time_ms ? `${Math.round(stats.avg_response_time_ms)}ms` : 'N/A'
              }}
            </p>
          </div>
          <div class="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
            <ClockIcon class="h-6 w-6 text-purple-600" />
          </div>
        </div>
        <div class="mt-2">
          <div class="flex items-center gap-1">
            <div class="h-2 w-2 rounded-full" :class="getResponseTimeColor()"></div>
            <p class="text-xs text-muted-foreground">
              {{ getResponseTimeLabel() }}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>

  <!-- Additional Stats Row -->
  <div v-if="showExtendedStats" class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
    <!-- Success Rate -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Success Rate</p>
            <p class="text-2xl font-bold">{{ getSuccessRate() }}%</p>
          </div>
          <div class="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
            <CheckCircleIcon class="h-6 w-6 text-green-600" />
          </div>
        </div>
        <div class="mt-2">
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div
              class="bg-green-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${getSuccessRate()}%` }"
            ></div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Recent Activity -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Recent Activity</p>
            <p class="text-2xl font-bold">{{ recentChanges?.length || 0 }}</p>
          </div>
          <div class="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
            <TrendingUpIcon class="h-6 w-6 text-blue-600" />
          </div>
        </div>
        <div class="mt-2">
          <p class="text-xs text-muted-foreground">Changes in last 30 days</p>
        </div>
      </CardContent>
    </Card>

    <!-- Failing Websites -->
    <Card>
      <CardContent class="p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-muted-foreground">Failing Checks</p>
            <p class="text-2xl font-bold">{{ failingWebsites?.length || 0 }}</p>
          </div>
          <div class="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircleIcon class="h-6 w-6 text-red-600" />
          </div>
        </div>
        <div class="mt-2">
          <p class="text-xs text-muted-foreground">Websites with errors</p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import {
  ActivityIcon,
  AlertCircleIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  GlobeIcon,
  TrendingUpIcon,
} from 'lucide-vue-next'

import { Card, CardContent } from '@/components/ui/card'

import type { WebsiteCheckResponse, WebsiteResponse, WebsiteStats } from '@/types/website'

interface Props {
  stats?: WebsiteStats | null
  recentChanges?: WebsiteCheckResponse[]
  failingWebsites?: WebsiteResponse[]
  showExtendedStats?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showExtendedStats: false,
})

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  } else {
    return num.toString()
  }
}

const getChangePercentage = (): number => {
  if (!props.stats?.total_websites || props.stats.total_websites === 0) {
    return 0
  }
  return Math.round((props.stats.websites_with_changes / props.stats.total_websites) * 100)
}

const getResponseTimeColor = (): string => {
  if (!props.stats?.avg_response_time_ms) return 'bg-gray-400'

  const time = props.stats.avg_response_time_ms
  if (time < 1000) return 'bg-green-500'
  if (time < 3000) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getResponseTimeLabel = (): string => {
  if (!props.stats?.avg_response_time_ms) return 'No data'

  const time = props.stats.avg_response_time_ms
  if (time < 1000) return 'Excellent'
  if (time < 3000) return 'Good'
  return 'Slow'
}

const getSuccessRate = (): number => {
  if (!props.stats?.total_checks || props.stats.total_checks === 0) {
    return 100
  }

  // Estimate success rate (in a real implementation, this would come from the backend)
  const failingCount = props.failingWebsites?.length || 0
  const totalWebsites = props.stats.total_websites || 1
  const successRate = ((totalWebsites - failingCount) / totalWebsites) * 100

  return Math.round(successRate)
}
</script>
