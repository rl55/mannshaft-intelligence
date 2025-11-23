"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { useToast } from "@/hooks/use-toast"
import { GeneralSettings } from "@/components/settings/general-settings"
import { AgentConfiguration } from "@/components/settings/agent-configuration"
import { GuardrailRules } from "@/components/settings/guardrail-rules"
import { IntegrationsSettings } from "@/components/settings/integrations-settings"
import { ApiConfiguration } from "@/components/settings/api-configuration"
import type { SystemSettings } from "@/components/settings/types"
import { defaultSettings } from "@/components/settings/default-settings"
import { Save, RotateCcw } from "lucide-react"

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings>(defaultSettings)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const { toast } = useToast()

  const updateGeneralSettings = (key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      general: {
        ...prev.general,
        [key]: value,
      },
    }))
    setHasUnsavedChanges(true)
  }

  const updateAgentSettings = (key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      agents: {
        ...prev.agents,
        [key]: value,
      },
    }))
    setHasUnsavedChanges(true)
  }

  const updateGuardrailSettings = (key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      guardrails: {
        ...prev.guardrails,
        [key]: value,
      },
    }))
    setHasUnsavedChanges(true)
  }

  const updateIntegrationSettings = (key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      integrations: {
        ...prev.integrations,
        [key]: value,
      },
    }))
    setHasUnsavedChanges(true)
  }

  const updateApiSettings = (key: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      api: {
        ...prev.api,
        [key]: value,
      },
    }))
    setHasUnsavedChanges(true)
  }

  const handleSave = () => {
    // In a real app, this would persist to a backend
    console.log("[v0] Saving settings:", settings)
    setHasUnsavedChanges(false)
    toast({
      title: "Settings Saved",
      description: `Configuration updated successfully at ${new Date().toLocaleTimeString()}.`,
    })
  }

  const handleReset = () => {
    setSettings(defaultSettings)
    setHasUnsavedChanges(false)
    toast({
      title: "Settings Reset",
      description: "All settings have been restored to default values.",
    })
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Configure system behavior, integrations, and security rules.</p>
        </div>
        <div className="flex items-center gap-2">
          {hasUnsavedChanges && <span className="text-sm text-amber-600 font-medium">Unsaved changes</span>}
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="mr-2 h-4 w-4" /> Reset to Defaults
          </Button>
          <Button onClick={handleSave} disabled={!hasUnsavedChanges}>
            <Save className="mr-2 h-4 w-4" /> Save Changes
          </Button>
        </div>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="guardrails">Guardrails</TabsTrigger>
          <TabsTrigger value="integrations">Integrations</TabsTrigger>
          <TabsTrigger value="api">API</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="mt-6">
          <GeneralSettings settings={settings.general} onUpdate={updateGeneralSettings} />
        </TabsContent>

        <TabsContent value="agents" className="mt-6">
          <AgentConfiguration settings={settings.agents} onUpdate={updateAgentSettings} />
        </TabsContent>

        <TabsContent value="guardrails" className="mt-6">
          <GuardrailRules settings={settings.guardrails} onUpdate={updateGuardrailSettings} />
        </TabsContent>

        <TabsContent value="integrations" className="mt-6">
          <IntegrationsSettings settings={settings.integrations} onUpdate={updateIntegrationSettings} />
        </TabsContent>

        <TabsContent value="api" className="mt-6">
          <ApiConfiguration settings={settings.api} onUpdate={updateApiSettings} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
