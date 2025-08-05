import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Building2, Users, DollarSign, TrendingUp, Target, Zap } from "lucide-react";

interface CompetitorCardProps {
  name: string;
  pricing_model: string;
  key_features: string;
  market_position: string;
  target_audience: string;
  revenue: string;
  market_share: string;
  pricing_tiers: string;
  data_sources: number;
}

export const CompetitorCard = ({
  name,
  pricing_model,
  key_features,
  market_position,
  target_audience,
  revenue,
  market_share,
  pricing_tiers,
  data_sources
}: CompetitorCardProps) => {
  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-foreground">{name}</h3>
              <Badge variant="secondary" className="mt-1">Data Sources: {data_sources}</Badge>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
            <Target className="w-4 h-4 text-info" />
            Market Position
          </h4>
          <p className="text-sm text-muted-foreground leading-relaxed">{market_position}</p>
        </div>
        
        <div>
          <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
            <Zap className="w-4 h-4 text-warning" />
            Key Features
          </h4>
          <p className="text-sm text-muted-foreground leading-relaxed">{key_features}</p>
        </div>
        
        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-info" />
            <div>
              <p className="text-xs text-muted-foreground">Target Audience</p>
              <p className="text-sm font-medium">{target_audience}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-success" />
            <div>
              <p className="text-xs text-muted-foreground">Revenue</p>
              <p className="text-sm font-medium">{revenue}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 col-span-2">
            <TrendingUp className="w-4 h-4 text-warning" />
            <div>
              <p className="text-xs text-muted-foreground">Market Share</p>
              <p className="text-sm font-medium">{market_share}</p>
            </div>
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-sm mb-2">Pricing Model</h4>
          <p className="text-sm text-muted-foreground">{pricing_model}</p>
          {pricing_tiers && pricing_tiers !== 'N/A' && (
            <div className="mt-2">
              <h5 className="text-xs font-medium text-muted-foreground">Pricing Tiers:</h5>
              <p className="text-xs text-muted-foreground">{pricing_tiers}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};