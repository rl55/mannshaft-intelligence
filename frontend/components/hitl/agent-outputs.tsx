import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import type { AgentOutput } from "./types"
import { AlertTriangle } from "lucide-react"

interface AgentOutputsProps {
  outputs: AgentOutput[]
}

export function AgentOutputs({ outputs }: AgentOutputsProps) {
  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold uppercase text-muted-foreground mb-3">Agent Outputs & Signals</h3>
      <Accordion type="single" collapsible className="w-full">
        {outputs.map((output) => (
          <AccordionItem key={output.id} value={output.id}>
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center justify-between w-full pr-4">
                <div className="flex items-center gap-2">
                  <span>{output.name}</span>
                  {output.flagged && <AlertTriangle className="h-4 w-4 text-amber-500" />}
                </div>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      output.confidence > 0.8 ? "default" : output.confidence > 0.6 ? "secondary" : "destructive"
                    }
                  >
                    {(output.confidence * 100).toFixed(0)}% Conf.
                  </Badge>
                </div>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="p-4 bg-muted/50 rounded-md space-y-3">
                {output.warnings && output.warnings.length > 0 && (
                  <div className="flex flex-col gap-1">
                    {output.warnings.map((warning, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm text-amber-600 font-medium">
                        <AlertTriangle className="h-3 w-3" />
                        {warning}
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-sm leading-relaxed">{output.content}</p>
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}
