import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PricingTier {
  competitor: string;
  tiers: {
    name: string;
    price: string;
    features: string[];
    isPopular?: boolean;
  }[];
}

interface PricingTableProps {
  pricingData: PricingTier[];
}

export const PricingTable = ({ pricingData }: PricingTableProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Pricing Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {pricingData.map((competitor) => (
            <div key={competitor.competitor} className="border rounded-lg p-4">
              <h3 className="font-semibold text-lg mb-4">{competitor.competitor}</h3>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Plan</TableHead>
                      <TableHead>Price</TableHead>
                      <TableHead>Key Features</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {competitor.tiers.map((tier, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            {tier.name}
                            {tier.isPopular && (
                              <Badge variant="default" className="text-xs">
                                Popular
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="font-semibold text-primary">
                          {tier.price}
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            {tier.features.slice(0, 3).map((feature, idx) => (
                              <div key={idx} className="text-sm text-muted-foreground">
                                • {feature}
                              </div>
                            ))}
                            {tier.features.length > 3 && (
                              <div className="text-sm text-muted-foreground">
                                +{tier.features.length - 3} more features
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};