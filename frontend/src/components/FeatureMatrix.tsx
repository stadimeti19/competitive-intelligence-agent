import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, X, Minus } from "lucide-react";

interface Feature {
  name: string;
  competitors: Record<string, boolean | "partial" | null>;
}

interface FeatureMatrixProps {
  competitors: string[];
  features: Feature[];
}

export const FeatureMatrix = ({ competitors, features }: FeatureMatrixProps) => {
  const getFeatureIcon = (value: boolean | "partial" | null) => {
    if (value === true) return <Check className="w-4 h-4 text-success" />;
    if (value === "partial") return <Minus className="w-4 h-4 text-warning" />;
    return <X className="w-4 h-4 text-destructive" />;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Feature Comparison Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[200px]">Feature</TableHead>
                {competitors.map((competitor) => (
                  <TableHead key={competitor} className="text-center min-w-[120px]">
                    {competitor}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {features.map((feature) => (
                <TableRow key={feature.name}>
                  <TableCell className="font-medium">{feature.name}</TableCell>
                  {competitors.map((competitor) => (
                    <TableCell key={competitor} className="text-center">
                      {getFeatureIcon(feature.competitors[competitor])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        
        <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-success" />
            <span>Full Support</span>
          </div>
          <div className="flex items-center gap-2">
            <Minus className="w-4 h-4 text-warning" />
            <span>Partial Support</span>
          </div>
          <div className="flex items-center gap-2">
            <X className="w-4 h-4 text-destructive" />
            <span>Not Available</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};