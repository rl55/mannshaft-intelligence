"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ExternalLink, CheckCircle2, AlertCircle } from "lucide-react"
import type { SystemSettings } from "./types"

interface IntegrationsSettingsProps {
  settings: SystemSettings["integrations"]
  onUpdate: (key: string, value: any) => void
}

export function IntegrationsSettings({ settings, onUpdate }: IntegrationsSettingsProps) {
  const updateSheet = (key: string, value: string) => {
    onUpdate("googleSheets", {
      ...settings.googleSheets,
      sheets: {
        ...settings.googleSheets.sheets,
        [key]: value,
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Google Sheets Integration
          {settings.googleSheets.connected ? (
            <span className="flex items-center text-sm font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
              <CheckCircle2 className="w-3 h-3 mr-1" /> Connected
            </span>
          ) : (
            <span className="flex items-center text-sm font-normal text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              <AlertCircle className="w-3 h-3 mr-1" /> Disconnected
            </span>
          )}
        </CardTitle>
        <CardDescription>Manage connections to your data sources.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-2">
          <Label>Connected Account</Label>
          <div className="flex gap-2">
            <Input value={settings.googleSheets.account} readOnly className="bg-muted" />
            <Button variant="outline" className="shrink-0 bg-transparent">
              Reconnect Google
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="sheet-revenue">Revenue Sheet ID</Label>
            <div className="flex gap-2">
              <Input
                id="sheet-revenue"
                value={settings.googleSheets.sheets.revenue}
                onChange={(e) => updateSheet("revenue", e.target.value)}
              />
              <Button variant="secondary" size="sm" className="shrink-0">
                Test Connection
              </Button>
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="sheet-product">Product Sheet ID</Label>
            <div className="flex gap-2">
              <Input
                id="sheet-product"
                value={settings.googleSheets.sheets.product}
                onChange={(e) => updateSheet("product", e.target.value)}
              />
              <Button variant="secondary" size="sm" className="shrink-0">
                Test Connection
              </Button>
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="sheet-support">Support Sheet ID</Label>
            <div className="flex gap-2">
              <Input
                id="sheet-support"
                value={settings.googleSheets.sheets.support}
                onChange={(e) => updateSheet("support", e.target.value)}
              />
              <Button variant="secondary" size="sm" className="shrink-0">
                Test Connection
              </Button>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t">
          <div className="space-y-0.5">
            <Label>Data Freshness Check</Label>
            <p className="text-sm text-muted-foreground">How often to poll sheets for updates.</p>
          </div>
          <Select
            value={settings.googleSheets.refreshInterval.toString()}
            onValueChange={(val) =>
              onUpdate("googleSheets", { ...settings.googleSheets, refreshInterval: Number.parseInt(val) })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select interval" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="15">Every 15 minutes</SelectItem>
              <SelectItem value="30">Every 30 minutes</SelectItem>
              <SelectItem value="60">Every 1 hour</SelectItem>
              <SelectItem value="360">Every 6 hours</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex justify-end">
          <Button variant="link" className="text-muted-foreground">
            <ExternalLink className="w-4 h-4 mr-2" /> View Permissions
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
