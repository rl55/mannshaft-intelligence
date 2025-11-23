"use client"

import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Bell } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"

interface DashboardHeaderProps {
  title?: string
}

export function DashboardHeader({ title = "Dashboard" }: DashboardHeaderProps) {
  return (
    <header className="sticky top-0 z-10 flex h-16 items-center border-b bg-background px-6">
      <div className="flex items-center gap-4 flex-1">
        <h1 className="text-xl font-semibold">{title}</h1>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <Bell className="h-4 w-4" />
        </Button>
        <ThemeToggle />
        <Avatar className="h-8 w-8">
          <AvatarImage src="/placeholder-user.jpg" />
          <AvatarFallback>DU</AvatarFallback>
        </Avatar>
      </div>
    </header>
  )
}
