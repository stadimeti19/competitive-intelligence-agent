import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Target, Users, Lightbulb } from "lucide-react";
import { useState } from "react";

interface AnalysisFormProps {
  onAnalyze: (data: AnalysisData) => void;
  isLoading?: boolean;
}

export interface AnalysisData {
  companyName: string;
  industry: string;
  targetAudience: string;
  keyFeatures: string;
  analysisType: string;
}

export const AnalysisForm = ({ onAnalyze, isLoading = false }: AnalysisFormProps) => {
  const [formData, setFormData] = useState<AnalysisData>({
    companyName: "",
    industry: "",
    targetAudience: "",
    keyFeatures: "",
    analysisType: ""
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(formData);
  };

  const updateField = (field: keyof AnalysisData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="w-5 h-5 text-primary" />
          Competitive Intelligence Analysis
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="company" className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Company Name or Business Idea *
              </Label>
              <Input
                id="company"
                placeholder="e.g., Slack, or 'team communication tool'"
                value={formData.companyName}
                onChange={(e) => updateField("companyName", e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Select value={formData.industry} onValueChange={(value) => updateField("industry", value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="saas">SaaS / Software</SelectItem>
                  <SelectItem value="ecommerce">E-commerce</SelectItem>
                  <SelectItem value="fintech">FinTech</SelectItem>
                  <SelectItem value="healthcare">Healthcare</SelectItem>
                  <SelectItem value="education">Education</SelectItem>
                  <SelectItem value="marketing">Marketing / AdTech</SelectItem>
                  <SelectItem value="productivity">Productivity Tools</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Target Audience (Optional)
            </Label>
            <Input
              id="audience"
              placeholder="e.g., Small businesses, Enterprise teams, Developers"
              value={formData.targetAudience}
              onChange={(e) => updateField("targetAudience", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="features" className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              Key Features (Optional)
            </Label>
            <Textarea
              id="features"
              placeholder="List main features or differentiators..."
              className="min-h-[80px]"
              value={formData.keyFeatures}
              onChange={(e) => updateField("keyFeatures", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="analysis-type">Analysis Type</Label>
            <Select value={formData.analysisType} onValueChange={(value) => updateField("analysisType", value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select analysis type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="full">Full CI Report</SelectItem>
                <SelectItem value="competitor">Competitor Analysis</SelectItem>
                <SelectItem value="market">Market Research</SelectItem>
                <SelectItem value="swot">SWOT Analysis</SelectItem>
                <SelectItem value="pricing">Pricing Analysis</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            disabled={!formData.companyName.trim() || isLoading}
          >
            {isLoading ? "Analyzing..." : "Start Analysis"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};