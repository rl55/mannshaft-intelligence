"use client"

import { LayoutDashboard, History, Shield, Users, Settings, BarChart3, Database } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar"

const menuItems = [
  {
    title: "Overview",
    items: [
      { title: "Dashboard", icon: LayoutDashboard, href: "/" },
      { title: "Sessions", icon: History, href: "/sessions" },
      { title: "HITL Queue", icon: Users, href: "/hitl" },
    ],
  },
  {
    title: "Monitoring",
    items: [
      { title: "Cache Performance", icon: Database, href: "/monitoring/cache" },
      { title: "Guardrails", icon: Shield, href: "/monitoring/guardrails" },
    ],
  },
  {
    title: "Configuration",
    items: [{ title: "Settings", icon: Settings, href: "/settings" }],
  },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-border p-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-primary" />
          <div>
            <h2 className="text-lg font-semibold">SaaS BI Agent</h2>
            <p className="text-xs text-muted-foreground">Intelligence Platform</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {menuItems.map((group) => (
          <SidebarGroup key={group.title}>
            <SidebarGroupLabel>{group.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {group.items.map((item) => {
                  const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))

                  return (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton asChild isActive={isActive}>
                        <Link href={item.href}>
                          <item.icon className="h-4 w-4" />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter className="border-t border-border p-4">
        <div className="text-xs text-muted-foreground">v1.0.0 | Powered by Gemini 2.0</div>
      </SidebarFooter>
    </Sidebar>
  )
}
