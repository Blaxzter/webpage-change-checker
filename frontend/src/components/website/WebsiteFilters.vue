<!-- src/components/website/WebsiteFilters.vue -->
<template>
  <Card>
    <CardContent class="p-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- Search -->
        <div class="md:col-span-2">
          <Label htmlFor="search" class="sr-only">Search websites</Label>
          <div class="relative">
            <SearchIcon
              class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground"
            />
            <Input
              id="search"
              v-model="filters.search"
              placeholder="Search websites..."
              class="pl-10"
            />
          </div>
        </div>

        <!-- Status Filter -->
        <div>
          <Label htmlFor="status" class="sr-only">Filter by status</Label>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" class="w-full justify-between">
                {{ statusLabel }}
                <ChevronDownIcon class="h-4 w-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent class="w-full min-w-[200px]">
              <DropdownMenuRadioGroup v-model:value="filters.status">
                <DropdownMenuRadioItem value="all">All Websites</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="active">Active Only</DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="inactive">Inactive Only</DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <!-- Actions -->
        <div class="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="clearFilters"
            v-if="hasActiveFilters"
            class="flex-1"
          >
            <XIcon class="h-4 w-4 mr-1" />
            Clear
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="$emit('refresh')"
            :disabled="isRefreshing"
            class="flex-1"
          >
            <RefreshCwIcon class="h-4 w-4 mr-1" :class="{ 'animate-spin': isRefreshing }" />
            Refresh
          </Button>
        </div>
      </div>

      <!-- Quick Filters -->
      <div v-if="showQuickFilters" class="mt-4 pt-4 border-t">
        <div class="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            :aria-pressed="filters.hasChanges"
            role="switch"
            @click="setQuickFilter('with-changes')"
            :class="{
              'bg-orange-50 border-orange-200 text-orange-700': filters.hasChanges,
              'hover:bg-orange-50/50': !filters.hasChanges,
            }"
          >
            <AlertTriangleIcon class="h-4 w-4 mr-1" />
            With Changes
          </Button>
          <Button
            variant="outline"
            size="sm"
            :aria-pressed="filters.status === 'active'"
            role="switch"
            @click="setQuickFilter('active-only')"
            :class="{
              'bg-green-50 border-green-200 text-green-700': filters.status === 'active',
              'hover:bg-green-50/50': filters.status !== 'active',
            }"
          >
            <CheckCircleIcon class="h-4 w-4 mr-1" />
            Active Only
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="setQuickFilter('needs-attention')"
            class="hover:bg-blue-50/50"
          >
            <AlertCircleIcon class="h-4 w-4 mr-1" />
            Needs Attention
          </Button>
        </div>
      </div>

      <!-- Results Summary -->
      <div v-if="showResultsSummary && totalResults !== undefined" class="mt-4 pt-4 border-t">
        <div class="flex items-center justify-between text-sm text-muted-foreground">
          <div>
            {{ totalResults }} website{{ totalResults !== 1 ? 's' : '' }} found
            <span v-if="hasActiveFilters"> (filtered)</span>
          </div>
          <div v-if="hasActiveFilters" class="flex items-center gap-1">
            <Badge variant="secondary" class="text-xs">
              {{ activeFilterCount }} filter{{ activeFilterCount !== 1 ? 's' : '' }} active
            </Badge>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import {
  AlertCircleIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  RefreshCwIcon,
  SearchIcon,
  XIcon,
} from 'lucide-vue-next'

import { useWebsiteFilters } from '@/composables/useWebsiteFilters'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface Props {
  showQuickFilters?: boolean
  showResultsSummary?: boolean
  totalResults?: number
  isRefreshing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showQuickFilters: true,
  showResultsSummary: true,
  isRefreshing: false,
})

defineEmits<{
  refresh: []
}>()

const { filters, hasActiveFilters, clearFilters } = useWebsiteFilters()

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.search) count++
  if (filters.value.status !== 'all') count++
  if (filters.value.hasChanges) count++
  return count
})

const statusLabel = computed(() => {
  switch (filters.value.status) {
    case 'active':
      return 'Active Only'
    case 'inactive':
      return 'Inactive Only'
    default:
      return 'All Websites'
  }
})

const setQuickFilter = (type: string) => {
  switch (type) {
    case 'with-changes':
      filters.value.hasChanges = !filters.value.hasChanges
      break
    case 'active-only':
      filters.value.status = filters.value.status === 'active' ? 'all' : 'active'
      break
    case 'needs-attention':
      // Combine multiple filters for "needs attention"
      filters.value.status = 'active'
      filters.value.hasChanges = true
      break
  }
}
</script>
