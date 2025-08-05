import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, X, Minus } from "lucide-react";

interface FeatureData {
  name: string;
  features: string;
}

interface FeatureMatrixProps {
  competitors: string[];
  features: FeatureData[];
}

export const FeatureMatrix = ({ competitors, features }: FeatureMatrixProps) => {
  // Define common features to look for
  const featureKeywords = [
    'payment processing', 'api', 'mobile app', 'web dashboard', 
    'analytics', 'fraud protection', 'multi-currency', 'instant payments',
    'recurring billing', 'subscription', 'marketplace', 'e-commerce',
    'banking', 'cryptocurrency', 'stock trading', 'peer-to-peer',
    'debit cards', 'credit cards', 'digital wallet', 'remittance',
    'compliance', 'kyc', 'aml', 'risk management', 'settlement',
    'online payments', 'point of sale', 'unified commerce', 'card issuing'
  ];
  
  const hasFeature = (competitorName: string, feature: string) => {
    const competitorData = features.find(f => f.name === competitorName);
    if (!competitorData || !competitorData.features || competitorData.features === 'N/A') {
      return false;
    }
    
    const competitorFeatures = competitorData.features.toLowerCase();
    return competitorFeatures.includes(feature.toLowerCase());
  };

  const getFeatureIcon = (value: boolean) => {
    if (value === true) return <Check className="w-4 h-4 text-success" />;
    return <X className="w-4 h-4 text-destructive" />;
  };

  if (featureKeywords.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Feature Comparison Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No feature data available for comparison
          </p>
        </CardContent>
      </Card>
    );
  }

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
              {featureKeywords.map((feature) => (
                <TableRow key={feature}>
                  <TableCell className="font-medium capitalize">{feature.replace('-', ' ')}</TableCell>
                  {competitors.map((competitor) => (
                    <TableCell key={competitor} className="text-center">
                      {getFeatureIcon(hasFeature(competitor, feature))}
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
            <span>Available</span>
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