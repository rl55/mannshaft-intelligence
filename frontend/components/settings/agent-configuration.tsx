"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import type { SystemSettings } from "./types"

interface AgentConfigurationProps {
  settings: SystemSettings["agents"]
  onUpdate: (key: string, value: any) => void
}

export function AgentConfiguration({ settings, onUpdate }: AgentConfigurationProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Configuration</CardTitle>
        <CardDescription>Manage the underlying AI models and execution behavior.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        <div className="grid gap-2">
          <Label htmlFor="gemini-model">Gemini Model</Label>
          <Select value={settings.model} onValueChange={(value) => onUpdate("model", value)}>
            <SelectTrigger id="gemini-model">
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gemini-2.0-flash-exp">gemini-2.0-flash-exp</SelectItem>
              <SelectItem value="gemini-1.5-pro">gemini-1.5-pro</SelectItem>
              <SelectItem value="gemini-1.5-flash">gemini-1.5-flash</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
            <Badge variant="secondary">{settings.confidenceThreshold.toFixed(2)}</Badge>
          </div>
          <Slider
            id="confidence-threshold"
            min={0}
            max={1}
            step={0.05}
            value={[settings.confidenceThreshold]}
            onValueChange={(vals) => onUpdate("confidenceThreshold", vals[0])}
          />
          <p className="text-sm text-muted-foreground">
            Agents will flag results for human review if their confidence score falls below this value.
          </p>
        </div>

        <div className="flex items-center justify-between space-x-2 rounded-lg border p-4">
          <div className="space-y-0.5">
            <Label htmlFor="parallel-execution">Parallel Execution</Label>
            <p className="text-sm text-muted-foreground">
              Run Revenue, Product, and Support agents concurrently to reduce total analysis time.
            </p>
          </div>
          <Switch
            id="parallel-execution"
            checked={settings.parallelExecution}
            onCheckedChange={(checked) => onUpdate("parallelExecution", checked)}
          />
        </div>
      </CardContent>
    </Card>
  )
}
