import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PricingData {
  name: string;
  model: string;
  tiers: string;
  revenue: string;
}

interface PricingTableProps {
  pricingData: PricingData[];
}

export const PricingTable = ({ pricingData }: PricingTableProps) => {
  if (!pricingData || pricingData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pricing Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No pricing data available for analysis
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pricing Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {pricingData.map((competitor) => (
            <div key={competitor.name} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg">{competitor.name}</h3>
                <Badge variant="secondary">
                  Revenue: {competitor.revenue}
                </Badge>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-sm text-muted-foreground mb-2">Pricing Model</h4>
                  <p className="text-sm">{competitor.model}</p>
                </div>
                
                {competitor.tiers && competitor.tiers !== 'N/A' && (
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground mb-2">Pricing Tiers</h4>
                    <div className="bg-muted p-3 rounded-lg">
                      <p className="text-sm">{competitor.tiers}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};