<!-- src/views/WebsiteDashboardView.vue -->
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">Website Monitor Dashboard</h1>
        <p class="text-muted-foreground">
          Monitor your websites for changes and get notified instantly
        </p>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" @click="refreshData" :disabled="dashboardLoading">
          <RefreshCwIcon class="h-4 w-4 mr-2" :class="{ 'animate-spin': dashboardLoading }" />
          Refresh
        </Button>
        <Button @click="showCreateDialog = true">
          <PlusIcon class="h-4 w-4 mr-2" />
          Add Website
        </Button>
      </div>
    </div>

    <!-- Dashboard Stats -->
    <DashboardStats
      :stats="stats"
      :recent-changes="recentChanges"
      :failing-websites="failingWebsites"
      :show-extended-stats="true"
    />

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card class="cursor-pointer hover:shadow-md transition-shadow" @click="triggerAllChecks">
        <CardContent class="p-4 text-center">
          <PlayIcon class="h-8 w-8 mx-auto mb-2 text-blue-600" />
          <h3 class="font-semibold">Check All Websites</h3>
          <p class="text-sm text-muted-foreground">Trigger manual checks for all active websites</p>
        </CardContent>
      </Card>

      <Card
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="$router.push('/app/websites')"
      >
        <CardContent class="p-4 text-center">
          <SettingsIcon class="h-8 w-8 mx-auto mb-2 text-green-600" />
          <h3 class="font-semibold">Manage Websites</h3>
          <p class="text-sm text-muted-foreground">Add, edit, or remove monitored websites</p>
        </CardContent>
      </Card>

      <Card
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="$router.push('/app/user-settings')"
      >
        <CardContent class="p-4 text-center">
          <BellIcon class="h-8 w-8 mx-auto mb-2 text-purple-600" />
          <h3 class="font-semibold">Notification Settings</h3>
          <p class="text-sm text-muted-foreground">Configure email and Telegram alerts</p>
        </CardContent>
      </Card>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Changes -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <AlertTriangleIcon class="h-5 w-5 text-orange-600" />
            Recent Changes
          </CardTitle>
          <CardDescription>
            Latest detected changes across your monitored websites
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="recentChanges.length === 0" class="text-center py-8">
            <CheckCircleIcon class="h-12 w-12 mx-auto text-green-600 mb-4" />
            <h3 class="text-lg font-semibold mb-2">No Recent Changes</h3>
            <p class="text-muted-foreground">All your websites are stable</p>
          </div>
          <div v-else class="space-y-4">
            <WebsiteCheckCard
              v-for="check in recentChanges.slice(0, 5)"
              :key="check.id"
              :check="check"
              :show-website-name="true"
              :show-actions="false"
            />
            <Button
              v-if="recentChanges.length > 5"
              variant="outline"
              class="w-full"
              @click="$router.push('/app/websites')"
            >
              View All Changes
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Failing Websites -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center gap-2">
            <AlertCircleIcon class="h-5 w-5 text-red-600" />
            Websites with Issues
          </CardTitle>
          <CardDescription> Websites that failed their last check </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="failingWebsites.length === 0" class="text-center py-8">
            <CheckCircleIcon class="h-12 w-12 mx-auto text-green-600 mb-4" />
            <h3 class="text-lg font-semibold mb-2">All Systems Operational</h3>
            <p class="text-muted-foreground">No websites are currently failing</p>
          </div>
          <div v-else class="space-y-4">
            <WebsiteCard
              v-for="website in failingWebsites.slice(0, 3)"
              :key="website.id"
              :website="website"
              :show-actions="false"
            />
            <Button
              v-if="failingWebsites.length > 3"
              variant="outline"
              class="w-full"
              @click="$router.push('/app/websites?status=failing')"
            >
              View All Issues
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Website Form Dialog -->
    <WebsiteFormDialog
      v-model:open="showCreateDialog"
      @success="handleWebsiteCreated"
      @error="handleError"
    />

    <!-- Error Toast -->
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
  BellIcon,
  CheckCircleIcon,
  PlayIcon,
  PlusIcon,
  RefreshCwIcon,
  SettingsIcon,
  XIcon,
} from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'

import { useWebsiteStore } from '@/stores/website'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

import DashboardStats from '@/components/website/DashboardStats.vue'
import WebsiteCard from '@/components/website/WebsiteCard.vue'
import WebsiteCheckCard from '@/components/website/WebsiteCheckCard.vue'
import WebsiteFormDialog from '@/components/website/WebsiteFormDialog.vue'

import type { WebsiteResponse } from '@/types/website'

const router = useRouter()
const websiteStore = useWebsiteStore()

const {
  dashboardData,
  dashboardLoading,
  checkLoading,
  error,
  stats,
  recentChanges,
  failingWebsites,
} = storeToRefs(websiteStore)

const showCreateDialog = ref(false)

const refreshData = async () => {
  try {
    await Promise.all([websiteStore.fetchDashboardStats(), websiteStore.fetchWebsites(1, true)])
  } catch (err) {
    console.error('Failed to refresh dashboard data:', err)
  }
}

const triggerAllChecks = async () => {
  try {
    await websiteStore.triggerManualCheck()
    // Refresh data after a short delay to see updated results
    setTimeout(refreshData, 2000)
  } catch (err) {
    console.error('Failed to trigger checks:', err)
  }
}

const handleWebsiteCreated = async (website: WebsiteResponse) => {
  // Refresh dashboard data to include the new website
  await refreshData()
}

const handleError = (errorMessage: string) => {
  console.error('Website operation error:', errorMessage)
}

const clearError = () => {
  websiteStore.clearError()
}

onMounted(async () => {
  await refreshData()
})
</script>
