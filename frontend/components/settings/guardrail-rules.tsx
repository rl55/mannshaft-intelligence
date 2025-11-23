"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import type { SystemSettings } from "./types"

interface GuardrailRulesProps {
  settings: SystemSettings["guardrails"]
  onUpdate: (key: string, value: any) => void
}

export function GuardrailRules({ settings, onUpdate }: GuardrailRulesProps) {
  const updateHardRule = (key: string, value: any) => {
    onUpdate("hardRules", { ...settings.hardRules, [key]: value })
  }

  const updateAdaptiveRule = (rule: string, key: string, value: any) => {
    onUpdate("adaptiveRules", {
      ...settings.adaptiveRules,
      [rule]: {
        // @ts-ignore - dynamic access
        ...settings.adaptiveRules[rule as keyof typeof settings.adaptiveRules],
        [key]: value,
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Guardrail Rules</CardTitle>
        <CardDescription>Configure safety checks and operational limits.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Hard Rules (Cannot Disable)
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>PII Detection</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically redact personally identifiable information.
                </p>
              </div>
              <Switch checked={settings.hardRules.piiDetection} disabled aria-readonly />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Cost Limit (Per Analysis)</Label>
                <p className="text-sm text-muted-foreground">Maximum allowable cost before halting execution.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">$</span>
                <Input
                  type="number"
                  className="w-20"
                  value={settings.hardRules.costLimit}
                  onChange={(e) => updateHardRule("costLimit", Number.parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>
        </div>

        <Separator />

        <div>
          <h3 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
            Adaptive Rules (Adjustable)
          </h3>
          <div className="space-y-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Low Confidence Flag</Label>
                  <p className="text-sm text-muted-foreground">
                    Flag outputs where agent confidence is below threshold.
                  </p>
                </div>
                <Switch
                  checked={settings.adaptiveRules.lowConfidence.enabled}
                  onCheckedChange={(checked) => updateAdaptiveRule("lowConfidence", "enabled", checked)}
                />
              </div>
              {settings.adaptiveRules.lowConfidence.enabled && (
                <div className="flex items-center gap-4 pl-4 border-l-2">
                  <Label className="text-xs">Threshold</Label>
                  <Input
                    type="number"
                    step="0.05"
                    max="1"
                    min="0"
                    className="w-20 h-8"
                    value={settings.adaptiveRules.lowConfidence.threshold}
                    onChange={(e) =>
                      updateAdaptiveRule("lowConfidence", "threshold", Number.parseFloat(e.target.value))
                    }
                  />
                  <Button variant="ghost" size="sm" className="h-8">
                    Adjust
                  </Button>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Data Completeness Check</Label>
                  <p className="text-sm text-muted-foreground">Ensure input data covers minimum historical range.</p>
                </div>
                <Switch
                  checked={settings.adaptiveRules.dataCompleteness.enabled}
                  onCheckedChange={(checked) => updateAdaptiveRule("dataCompleteness", "enabled", checked)}
                />
              </div>
              {settings.adaptiveRules.dataCompleteness.enabled && (
                <div className="flex items-center gap-4 pl-4 border-l-2">
                  <Label className="text-xs">Min Weeks</Label>
                  <Input
                    type="number"
                    className="w-20 h-8"
                    value={settings.adaptiveRules.dataCompleteness.minWeeks}
                    onChange={(e) =>
                      updateAdaptiveRule("dataCompleteness", "minWeeks", Number.parseInt(e.target.value))
                    }
                  />
                  <Button variant="ghost" size="sm" className="h-8">
                    Adjust
                  </Button>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Anomaly Detection</Label>
                <p className="text-sm text-muted-foreground">Scan for statistical outliers in revenue data.</p>
              </div>
              <Switch
                checked={settings.adaptiveRules.anomalyDetection.enabled}
                onCheckedChange={(checked) => updateAdaptiveRule("anomalyDetection", "enabled", checked)}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
