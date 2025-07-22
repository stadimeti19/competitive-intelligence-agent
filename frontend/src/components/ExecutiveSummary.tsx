import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, AlertTriangle, Target, Lightbulb } from "lucide-react";

interface SummaryData {
  keyFindings: string[];
  opportunities: string[];
  threats: string[];
  marketPosition: string;
  recommendations: string[];
}

interface ExecutiveSummaryProps {
  data: SummaryData;
}

export const ExecutiveSummary = ({ data }: ExecutiveSummaryProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          Executive Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Target className="w-4 h-4 text-info" />
            Market Position
          </h3>
          <p className="text-muted-foreground leading-relaxed">{data.marketPosition}</p>
        </div>

        <div>
          <h3 className="font-semibold mb-3">Key Findings</h3>
          <ul className="space-y-2">
            {data.keyFindings.map((finding, index) => (
              <li key={index} className="flex items-start gap-2">
                <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                <span className="text-muted-foreground">{finding}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-success">
              <TrendingUp className="w-4 h-4" />
              Opportunities
            </h3>
            <div className="space-y-2">
              {data.opportunities.map((opportunity, index) => (
                <Badge key={index} variant="secondary" className="block w-fit">
                  {opportunity}
                </Badge>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-3 flex items-center gap-2 text-destructive">
              <AlertTriangle className="w-4 h-4" />
              Threats
            </h3>
            <div className="space-y-2">
              {data.threats.map((threat, index) => (
                <Badge key={index} variant="destructive" className="block w-fit">
                  {threat}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-warning" />
            Strategic Recommendations
          </h3>
          <div className="space-y-3">
            {data.recommendations.map((recommendation, index) => (
              <div key={index} className="bg-muted p-3 rounded-lg">
                <p className="text-sm">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};