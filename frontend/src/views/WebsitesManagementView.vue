<!-- src/views/WebsitesManagementView.vue -->
<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">Websites</h1>
        <p class="text-muted-foreground">Manage your monitored websites</p>
      </div>
      <div class="flex gap-2">
        <Button
          variant="outline"
          @click="triggerChecksForSelected"
          :disabled="selectedWebsites.length === 0 || checkLoading"
        >
          <PlayIcon class="h-4 w-4 mr-2" />
          Check Selected ({{ selectedWebsites.length }})
        </Button>
        <Button @click="showCreateDialog = true">
          <PlusIcon class="h-4 w-4 mr-2" />
          Add Website
        </Button>
      </div>
    </div>

    <!-- Filters -->
    <WebsiteFilters
      :total-results="pagination.total"
      :is-refreshing="loading"
      @refresh="refreshWebsites"
    />

    <!-- Bulk Actions -->
    <div
      v-if="selectedWebsites.length > 0"
      class="bg-blue-50 border border-blue-200 rounded-lg p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <span class="text-sm font-medium">
            {{ selectedWebsites.length }} website{{ selectedWebsites.length !== 1 ? 's' : '' }}
            selected
          </span>
          <div class="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              @click="triggerChecksForSelected"
              :disabled="checkLoading"
            >
              <PlayIcon class="h-4 w-4 mr-1" />
              Check All
            </Button>
            <Button variant="outline" size="sm" @click="toggleSelectedActive(true)">
              <CheckCircleIcon class="h-4 w-4 mr-1" />
              Activate
            </Button>
            <Button variant="outline" size="sm" @click="toggleSelectedActive(false)">
              <PauseIcon class="h-4 w-4 mr-1" />
              Deactivate
            </Button>
          </div>
        </div>
        <Button variant="ghost" size="sm" @click="selectedWebsites = []">
          <XIcon class="h-4 w-4" />
          Clear Selection
        </Button>
      </div>
    </div>

    <!-- Website List -->
    <div
      v-if="loading && (websites?.length || 0) === 0"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <div v-for="i in 6" :key="i" class="animate-pulse">
        <Card>
          <CardContent class="p-6">
            <div class="h-6 bg-gray-200 rounded mb-2"></div>
            <div class="h-4 bg-gray-200 rounded mb-4"></div>
            <div class="grid grid-cols-2 gap-4">
              <div class="h-8 bg-gray-200 rounded"></div>
              <div class="h-8 bg-gray-200 rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <div v-else-if="filteredWebsites?.length === 0" class="text-center py-12">
      <GlobeIcon class="h-16 w-16 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-xl font-semibold mb-2">
        {{ (websites?.length || 0) === 0 ? 'No websites yet' : 'No websites match your filters' }}
      </h3>
      <p class="text-muted-foreground mb-6">
        {{
          (websites?.length || 0) === 0
            ? 'Add your first website to start monitoring for changes'
            : 'Try adjusting your search or filter criteria'
        }}
      </p>
      <Button v-if="(websites?.length || 0) === 0" @click="showCreateDialog = true">
        <PlusIcon class="h-4 w-4 mr-2" />
        Add Your First Website
      </Button>
      <Button v-else variant="outline" @click="clearFilters">
        <XIcon class="h-4 w-4 mr-2" />
        Clear Filters
      </Button>
    </div>

    <div v-else class="space-y-6">
      <!-- Selection Controls -->
      <div class="flex items-center gap-4">
        <label class="flex items-center gap-2 text-sm cursor-pointer">
          <Checkbox
            :checked="isAllSelected"
            :indeterminate="isSomeSelected"
            @update:checked="toggleSelectAll"
          />
          Select All
        </label>
        <span class="text-sm text-muted-foreground">
          {{ filteredWebsites?.length || 0 }} website
          {{ (filteredWebsites?.length || 0) !== 1 ? 's' : '' }}
        </span>
      </div>

      <!-- Website Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="website in filteredWebsites || []" :key="website.id" class="relative">
          <!-- Selection Checkbox -->
          <div class="absolute top-2 left-2 z-10">
            <input
              type="checkbox"
              :checked="selectedWebsites.includes(website.id)"
              @change="toggleWebsiteSelection(website.id)"
              class="h-4 w-4 rounded border-gray-300"
            />
          </div>

          <WebsiteCard
            :website="website"
            :is-checking="checkingWebsites.includes(website.id)"
            @view="viewWebsite"
            @edit="editWebsite"
            @check="checkWebsite"
            @delete="deleteWebsite"
          />
        </div>
      </div>

      <!-- Load More -->
      <div v-if="pagination.page < pagination.totalPages" class="text-center">
        <Button variant="outline" @click="loadMoreWebsites" :disabled="loading">
          {{ loading ? 'Loading...' : 'Load More' }}
        </Button>
      </div>
    </div>

    <!-- Dialogs -->
    <WebsiteFormDialog
      v-model:open="showCreateDialog"
      :website="editingWebsite"
      @success="handleWebsiteSaved"
      @error="handleError"
    />

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:open="showDeleteDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Website</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{{ deletingWebsite?.name }}"? This action cannot be
            undone. All check history will be permanently removed.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="showDeleteDialog = false"> Cancel </Button>
          <Button variant="destructive" @click="confirmDelete" :disabled="loading">
            Delete Website
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { CheckCircleIcon, GlobeIcon, PauseIcon, PlayIcon, PlusIcon, XIcon } from 'lucide-vue-next'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'

import { useWebsiteStore } from '@/stores/website'

import { useWebsiteFilters } from '@/composables/useWebsiteFilters'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

import WebsiteCard from '@/components/website/WebsiteCard.vue'
import WebsiteFilters from '@/components/website/WebsiteFilters.vue'
import WebsiteFormDialog from '@/components/website/WebsiteFormDialog.vue'

import type { WebsiteResponse } from '@/types/website'

const router = useRouter()
const websiteStore = useWebsiteStore()
const { clearFilters } = useWebsiteFilters()

const { websites, filteredWebsites, loading, checkLoading, error, pagination } =
  storeToRefs(websiteStore)

const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingWebsite = ref<WebsiteResponse | null>(null)
const deletingWebsite = ref<WebsiteResponse | null>(null)
const selectedWebsites = ref<string[]>([])
const checkingWebsites = ref<string[]>([])

const isAllSelected = computed(
  () =>
    (filteredWebsites.value?.length || 0) > 0 &&
    selectedWebsites.value.length === (filteredWebsites.value?.length || 0),
)

const isSomeSelected = computed(
  () =>
    selectedWebsites.value.length > 0 &&
    selectedWebsites.value.length < (filteredWebsites.value?.length || 0),
)

const refreshWebsites = async () => {
  await websiteStore.fetchWebsites(1, true)
}

const loadMoreWebsites = async () => {
  await websiteStore.fetchWebsites(pagination.value.page + 1, false)
}

const viewWebsite = (website: WebsiteResponse) => {
  router.push(`/app/websites/${website.id}`)
}

const editWebsite = (website: WebsiteResponse) => {
  editingWebsite.value = website
  showCreateDialog.value = true
}

const checkWebsite = async (websiteId: string) => {
  checkingWebsites.value.push(websiteId)
  try {
    await websiteStore.triggerManualCheck([websiteId])
  } finally {
    checkingWebsites.value = checkingWebsites.value.filter((id) => id !== websiteId)
  }
}

const deleteWebsite = (websiteId: string) => {
  const website = websites.value?.find((w) => w.id === websiteId)
  if (website) {
    deletingWebsite.value = website
    showDeleteDialog.value = true
  }
}

const confirmDelete = async () => {
  if (deletingWebsite.value) {
    try {
      await websiteStore.deleteWebsite(deletingWebsite.value.id)
      showDeleteDialog.value = false
      deletingWebsite.value = null
      // Remove from selection if it was selected
      selectedWebsites.value = selectedWebsites.value.filter(
        (id) => id !== deletingWebsite.value?.id,
      )
    } catch (err) {
      console.error('Failed to delete website:', err)
    }
  }
}

const toggleWebsiteSelection = (websiteId: string) => {
  const index = selectedWebsites.value.indexOf(websiteId)
  if (index === -1) {
    selectedWebsites.value.push(websiteId)
  } else {
    selectedWebsites.value.splice(index, 1)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedWebsites.value = []
  } else {
    selectedWebsites.value = filteredWebsites.value?.map((w) => w.id) || []
  }
}

const triggerChecksForSelected = async () => {
  if (selectedWebsites.value.length === 0) return

  try {
    await websiteStore.triggerManualCheck(selectedWebsites.value)
  } catch (err) {
    console.error('Failed to trigger checks:', err)
  }
}

const toggleSelectedActive = async (active: boolean) => {
  for (const websiteId of selectedWebsites.value) {
    try {
      await websiteStore.updateWebsite(websiteId, { is_active: active })
    } catch (err) {
      console.error(`Failed to update website ${websiteId}:`, err)
    }
  }
}

const handleWebsiteSaved = () => {
  showCreateDialog.value = false
  editingWebsite.value = null
  refreshWebsites()
}

const handleError = (errorMessage: string) => {
  console.error('Website operation error:', errorMessage)
}

onMounted(async () => {
  await refreshWebsites()
})
</script>
