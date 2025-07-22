import { useState } from "react";
import { AnalysisForm, AnalysisData } from "@/components/AnalysisForm";
import { CompetitorCard } from "@/components/CompetitorCard";
import { FeatureMatrix } from "@/components/FeatureMatrix";
import { PricingTable } from "@/components/PricingTable";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Download, FileText, BarChart3 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

export const Dashboard = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [progress, setProgress] = useState(0);
  const [summary, setSummary] = useState<any>(null);
  const [competitors, setCompetitors] = useState<any[]>([]);
  const [features, setFeatures] = useState<any[]>([]);
  const [pricing, setPricing] = useState<any[]>([]);
  const { toast } = useToast();

  const handleAnalysis = async (data: AnalysisData) => {
    setIsAnalyzing(true);
    setProgress(0);
    setHasResults(false);
    try {
      // Simulate progress
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 400);
      // Call backend API
      const response = await axios.post("http://localhost:8000/analyze", data);
      setSummary(response.data.summary);
      setCompetitors(response.data.competitors);
      setFeatures(response.data.features);
      setPricing(response.data.pricing);
      setHasResults(true);
      setProgress(100);
      toast({
        title: "Analysis Complete",
        description: "Your competitive intelligence report is ready!",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to analyze. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExport = () => {
    toast({
      title: "Export Started",
      description: "Your report is being prepared for download...",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Competitive Intelligence Dashboard
          </h1>
          <p className="text-muted-foreground">
            Analyze your competition and discover market opportunities
          </p>
        </div>

        <div className="space-y-8">
          <AnalysisForm onAnalyze={handleAnalysis} isLoading={isAnalyzing} />

          {isAnalyzing && (
            <Card>
              <CardHeader>
                <CardTitle>Analysis in Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Progress value={progress} className="w-full" />
                  <p className="text-sm text-muted-foreground">
                    {progress < 30 && "Identifying competitors..."}
                    {progress >= 30 && progress < 60 && "Collecting company data..."}
                    {progress >= 60 && progress < 90 && "Analyzing features and pricing..."}
                    {progress >= 90 && "Generating insights..."}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {hasResults && summary && (
            <>
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-semibold">Analysis Results</h2>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleExport}>
                    <FileText className="w-4 h-4 mr-2" />
                    Export PDF
                  </Button>
                  <Button variant="outline" onClick={handleExport}>
                    <Download className="w-4 h-4 mr-2" />
                    Download Data
                  </Button>
                </div>
              </div>

              <ExecutiveSummary data={summary} />

              <div>
                <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Competitor Overview
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {competitors.map((competitor) => (
                    <CompetitorCard key={competitor.name} {...competitor} />
                  ))}
                </div>
              </div>

              <FeatureMatrix 
                competitors={competitors.map(c => c.name)} 
                features={features} 
              />

              <PricingTable pricingData={pricing} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};