"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { AlertTriangle, Trash2, RotateCcw } from "lucide-react"
import type { SystemSettings } from "./types"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

interface GeneralSettingsProps {
  settings: SystemSettings["general"]
  onUpdate: (key: string, value: any) => void
}

export function GeneralSettings({ settings, onUpdate }: GeneralSettingsProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>General Settings</CardTitle>
          <CardDescription>Configure the default behavior for the analysis system.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-2">
            <Label htmlFor="analysis-type">Default Analysis Type</Label>
            <Select value={settings.analysisType} onValueChange={(value) => onUpdate("analysisType", value)}>
              <SelectTrigger id="analysis-type">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="comprehensive">Comprehensive (All Agents)</SelectItem>
                <SelectItem value="fast">Fast (Summary Only)</SelectItem>
                <SelectItem value="deep">Deep Dive (Metric Focused)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Cache TTL (Hours)</Label>
            <div className="grid grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="cache-prompts" className="text-xs text-muted-foreground">
                  Prompts
                </Label>
                <Input
                  id="cache-prompts"
                  type="number"
                  value={settings.cacheTtl.prompts}
                  onChange={(e) =>
                    onUpdate("cacheTtl", { ...settings.cacheTtl, prompts: Number.parseInt(e.target.value) })
                  }
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="cache-agents" className="text-xs text-muted-foreground">
                  Agents
                </Label>
                <Input
                  id="cache-agents"
                  type="number"
                  value={settings.cacheTtl.agents}
                  onChange={(e) =>
                    onUpdate("cacheTtl", { ...settings.cacheTtl, agents: Number.parseInt(e.target.value) })
                  }
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="cache-evals" className="text-xs text-muted-foreground">
                  Evaluations
                </Label>
                <Input
                  id="cache-evals"
                  type="number"
                  value={settings.cacheTtl.evaluations}
                  onChange={(e) =>
                    onUpdate("cacheTtl", { ...settings.cacheTtl, evaluations: Number.parseInt(e.target.value) })
                  }
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between space-x-2">
            <div className="space-y-0.5">
              <Label htmlFor="hitl-mode">HITL Production Mode</Label>
              <p className="text-sm text-muted-foreground">In demo mode, escalations auto-approve after 2 seconds.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                {settings.hitlMode === "production" ? "Production" : "Demo"}
              </span>
              <Switch
                id="hitl-mode"
                checked={settings.hitlMode === "production"}
                onCheckedChange={(checked) => onUpdate("hitlMode", checked ? "production" : "demo")}
              />
            </div>
          </div>

          <div className="space-y-3">
            <Label>Notifications</Label>
            <div className="space-y-2">
              <div className="flex items-center justify-between rounded-lg border p-3 shadow-sm">
                <div className="space-y-0.5">
                  <Label htmlFor="notify-email">Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">Receive emails when analysis completes.</p>
                </div>
                <Switch
                  id="notify-email"
                  checked={settings.notifications.email}
                  onCheckedChange={(checked) =>
                    onUpdate("notifications", { ...settings.notifications, email: checked })
                  }
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border p-3 shadow-sm">
                <div className="space-y-0.5">
                  <Label htmlFor="notify-slack">Slack Notifications</Label>
                  <p className="text-sm text-muted-foreground">Post to Slack on HITL escalations.</p>
                </div>
                <Switch
                  id="notify-slack"
                  checked={settings.notifications.slack}
                  onCheckedChange={(checked) =>
                    onUpdate("notifications", { ...settings.notifications, slack: checked })
                  }
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border p-3 shadow-sm">
                <div className="space-y-0.5">
                  <Label htmlFor="notify-desktop">Desktop Notifications</Label>
                  <p className="text-sm text-muted-foreground">Browser alerts for urgent issues.</p>
                </div>
                <Switch
                  id="notify-desktop"
                  checked={settings.notifications.desktop}
                  onCheckedChange={(checked) =>
                    onUpdate("notifications", { ...settings.notifications, desktop: checked })
                  }
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" /> Danger Zone
          </CardTitle>
          <CardDescription>Destructive actions that cannot be undone.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Clear System Cache</Label>
              <p className="text-sm text-muted-foreground">Removes all cached prompts and agent responses.</p>
            </div>
            <Button variant="outline" size="sm">
              <RotateCcw className="mr-2 h-4 w-4" /> Clear Cache
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-destructive">Reset System</Label>
              <p className="text-sm text-muted-foreground">Deletes all sessions and resets configuration.</p>
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <Trash2 className="mr-2 h-4 w-4" /> Reset All
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete all session data and reset your settings
                    to default.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                    Yes, Reset System
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
