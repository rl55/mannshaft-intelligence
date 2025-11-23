"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Copy, Key, Download, Upload } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import type { SystemSettings } from "./types"

interface ApiConfigurationProps {
  settings: SystemSettings["api"]
  onUpdate: (key: string, value: any) => void
}

export function ApiConfiguration({ settings, onUpdate }: ApiConfigurationProps) {
  const { toast } = useToast()

  const handleCopyKey = () => {
    navigator.clipboard.writeText(settings.apiKey)
    toast({
      title: "API Key Copied",
      description: "The API key has been copied to your clipboard.",
    })
  }

  const handleExportConfig = () => {
    toast({
      title: "Configuration Exported",
      description: "Settings have been downloaded as JSON.",
    })
  }

  const handleImportConfig = () => {
    toast({
      title: "Configuration Imported",
      description: "Settings have been loaded successfully.",
    })
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>Manage external API access and webhooks.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-2">
            <Label htmlFor="api-key">API Key</Label>
            <div className="flex gap-2">
              <Input id="api-key" type="password" value={settings.apiKey} readOnly className="font-mono bg-muted" />
              <Button variant="outline" size="icon" onClick={handleCopyKey}>
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Key className="mr-2 h-4 w-4" /> Regenerate
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Keep this secret. Anyone with this key can access your analysis API.
            </p>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="webhook-url">Webhook URL</Label>
            <Input
              id="webhook-url"
              type="url"
              placeholder="https://api.example.com/webhooks/v1/analysis"
              value={settings.webhookUrl}
              onChange={(e) => onUpdate("webhookUrl", e.target.value)}
            />
            <p className="text-sm text-muted-foreground">POST analysis completion events to this endpoint.</p>
          </div>

          <div className="pt-4 border-t">
            <Button variant="secondary" size="sm" className="mr-2">
              Test Webhook
            </Button>
            <Button variant="link" className="text-muted-foreground">
              View API Documentation
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Configuration Management</CardTitle>
          <CardDescription>Export and import your system settings.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Export Configuration</Label>
              <p className="text-sm text-muted-foreground">Download all settings as a JSON file for backup.</p>
            </div>
            <Button variant="outline" size="sm" onClick={handleExportConfig}>
              <Download className="mr-2 h-4 w-4" /> Export JSON
            </Button>
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Import Configuration</Label>
              <p className="text-sm text-muted-foreground">Restore settings from a previously exported file.</p>
            </div>
            <Button variant="outline" size="sm" onClick={handleImportConfig}>
              <Upload className="mr-2 h-4 w-4" /> Import JSON
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
