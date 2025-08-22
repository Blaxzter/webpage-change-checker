<script setup lang="ts">
import {
  AudioWaveform,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Command,
  Frame,
  GalleryVerticalEnd,
  Globe,
  Home,
  Map,
  Monitor,
  PieChart,
  Settings2,
  SquareTerminal,
} from 'lucide-vue-next'

import type { SidebarProps } from '@/components/ui/sidebar'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from '@/components/ui/sidebar'

import NavMain from '@/components/navigation/NavMain.vue'
import NavProjects from '@/components/navigation/NavProjects.vue'
import NavUser from '@/components/navigation/NavUser.vue'
import TeamSwitcher from '@/components/navigation/TeamSwitcher.vue'

interface AppSidebarProps extends SidebarProps {
  open?: boolean
}

const props = withDefaults(defineProps<AppSidebarProps>(), {
  collapsible: 'icon',
  open: true,
})

// This is sample data.
const data = {
  teams: [
    {
      name: 'Acme Inc',
      logo: GalleryVerticalEnd,
      plan: 'Enterprise',
    },
    {
      name: 'Acme Corp.',
      logo: AudioWaveform,
      plan: 'Startup',
    },
    {
      name: 'Evil Corp.',
      logo: Command,
      plan: 'Free',
    },
  ],
  navMain: [
    {
      title: 'Overview',
      routeName: 'home',
      icon: Home,
      items: [
        {
          title: 'Home',
          routeName: 'home',
        },
        {
          title: 'Dashboard',
          routeName: 'website-dashboard',
        },
      ],
    },
    {
      title: 'Website Monitoring',
      routeName: 'websites',
      icon: Monitor,
      isActive: true,
      items: [
        {
          title: 'Dashboard',
          routeName: 'website-dashboard',
        },
        {
          title: 'All Websites',
          routeName: 'websites',
        },
        {
          title: 'Add Website',
          routeName: 'websites',
        },
      ],
    },
    {
      title: 'Settings',
      routeName: 'settings',
      icon: Settings2,
      items: [
        {
          title: 'Profile',
          routeName: 'settings',
        },
        {
          title: 'Notifications',
          routeName: 'notification-settings',
        },
      ],
    },
    {
      title: 'Examples',
      routeName: 'examples',
      icon: Bot,
      items: [
        {
          title: 'API Example',
          routeName: 'test',
        },
        {
          title: 'Breadcrumb Examples',
          routeName: 'breadcrumb-examples',
        },
        {
          title: 'Layout Demo',
          routeName: 'layout-demo',
        },
      ],
    },
  ],
  projects: [
    {
      name: 'Design Engineering',
      url: '#',
      icon: Frame,
    },
    {
      name: 'Sales & Marketing',
      url: '#',
      icon: PieChart,
    },
    {
      name: 'Travel',
      url: '#',
      icon: Map,
    },
  ],
}
</script>

<template>
  <Sidebar v-bind="props">
    <SidebarHeader>
      <TeamSwitcher :teams="data.teams" />
    </SidebarHeader>
    <SidebarContent>
      <NavMain :items="data.navMain" :open="props.open" />
      <NavProjects :projects="data.projects" />
    </SidebarContent>
    <SidebarFooter>
      <NavUser />
    </SidebarFooter>
    <SidebarRail />
  </Sidebar>
</template>
