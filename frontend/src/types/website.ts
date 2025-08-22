// src/types/website.ts
// ✅ ALWAYS import generated types - never redefine them
export type {
  WebsiteCreate,
  WebsiteUpdate,
  WebsiteResponse,
  WebsiteListResponse,
  WebsiteWithChecks,
  WebsiteCheckResponse,
  WebsiteCheckListResponse,
  NotificationSettingsCreate,
  NotificationSettingsUpdate,
  NotificationSettingsResponse,
  CheckTrigger,
  DashboardResponse,
  WebsiteStats,
  CheckStatus,
  NotificationChannel,
} from '@/client/types.gen'

// ✅ ONLY define frontend-specific types
export interface WebsiteFilters {
  search?: string
  status?: 'all' | 'active' | 'inactive'
  hasChanges?: boolean
}

export interface PaginationState {
  page: number
  perPage: number
  total: number
  totalPages: number
}

export interface CheckFilters {
  status?: CheckStatus | 'all'
  hasChanges?: boolean
  dateFrom?: string
  dateTo?: string
}

export interface NotificationTestRequest {
  channel: NotificationChannel
}

// UI-specific interfaces
export interface WebsiteCardProps {
  website: WebsiteResponse
  showActions?: boolean
}

export interface CheckCardProps {
  check: WebsiteCheckResponse
  showWebsiteName?: boolean
}

export interface MonitoringStats {
  totalWebsites: number
  activeWebsites: number
  totalChecks: number
  checksLast24h: number
  websitesWithChanges: number
  avgResponseTime?: number
  successRate: number
}

// ✅ Use auto-generated Zod schemas
export {
  zWebsiteCreate as websiteCreateSchema,
  zWebsiteUpdate as websiteUpdateSchema,
  zNotificationSettingsUpdate as notificationSettingsUpdateSchema,
  zCheckTrigger as checkTriggerSchema,
} from '@/client/zod.gen'
