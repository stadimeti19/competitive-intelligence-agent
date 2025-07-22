import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Building2, Users, DollarSign, TrendingUp } from "lucide-react";

interface CompetitorCardProps {
  name: string;
  description: string;
  logo?: string;
  employees: string;
  revenue: string;
  marketShare: string;
  fundingStage: string;
}

export const CompetitorCard = ({
  name,
  description,
  logo,
  employees,
  revenue,
  marketShare,
  fundingStage
}: CompetitorCardProps) => {
  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {logo ? (
              <img src={logo} alt={`${name} logo`} className="w-12 h-12 rounded-lg object-cover" />
            ) : (
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Building2 className="w-6 h-6 text-primary" />
              </div>
            )}
            <div>
              <h3 className="font-semibold text-lg text-foreground">{name}</h3>
              <Badge variant="secondary" className="mt-1">{fundingStage}</Badge>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
        
        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-info" />
            <div>
              <p className="text-xs text-muted-foreground">Employees</p>
              <p className="text-sm font-medium">{employees}</p>
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
              <p className="text-sm font-medium">{marketShare}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};