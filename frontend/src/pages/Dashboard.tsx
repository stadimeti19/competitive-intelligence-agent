import { useState, useEffect } from "react";
import { AnalysisForm, AnalysisData } from "@/components/AnalysisForm";
import { CompetitorCard } from "@/components/CompetitorCard";
import { FeatureMatrix } from "@/components/FeatureMatrix";
import { PricingTable } from "@/components/PricingTable";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import { ChartDisplay } from "@/components/ChartDisplay";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Download, FileText, BarChart3, History } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

interface SummaryData {
  keyFindings: string[];
  opportunities: string[];
  threats: string[];
  marketPosition: string;
  recommendations: string[];
  charts: Record<string, string>;
}

interface CompetitorData {
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

interface FeatureData {
  name: string;
  features: string;
}

interface PricingData {
  name: string;
  model: string;
  tiers: string;
  revenue: string;
}

interface SavedRunRow {
  id: string;
  created_at: string;
  company_name: string | null;
  industry: string | null;
}

export const Dashboard = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [progress, setProgress] = useState(0);
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorData[]>([]);
  const [features, setFeatures] = useState<FeatureData[]>([]);
  const [pricing, setPricing] = useState<PricingData[]>([]);
  const [charts, setCharts] = useState<Record<string, string>>({});
  const [savedRuns, setSavedRuns] = useState<SavedRunRow[]>([]);
  const [savedRunSelection, setSavedRunSelection] = useState<string>("");
  const { toast } = useToast();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get<{ runs: SavedRunRow[] }>(`${API_BASE}/runs`);
        if (!cancelled && Array.isArray(res.data?.runs)) {
          setSavedRuns(res.data.runs);
        }
      } catch {
        /* Backend down or Supabase not configured */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshSavedRuns = async (opts?: { silent?: boolean }) => {
    try {
      const res = await axios.get<{ runs: SavedRunRow[] }>(`${API_BASE}/runs`);
      if (Array.isArray(res.data?.runs)) {
        setSavedRuns(res.data.runs);
      }
    } catch {
      if (!opts?.silent) {
        toast({
          title: "Could not load saved runs",
          description: "Is the API running and Supabase configured on the server?",
          variant: "destructive",
        });
      }
    }
  };

  const loadSavedRun = async (runId: string) => {
    if (!runId) return;
    try {
      const res = await axios.get(`${API_BASE}/runs/${runId}`);
      setSummary(res.data.summary);
      setCompetitors(res.data.competitors ?? []);
      setFeatures(res.data.features ?? []);
      setPricing(res.data.pricing ?? []);
      setCharts(res.data.summary?.charts ?? {});
      setHasResults(true);
      toast({
        title: "Loaded saved analysis",
        description: res.data.input?.companyName
          ? `${res.data.input.companyName}`
          : undefined,
      });
    } catch {
      toast({
        title: "Error",
        description: "Could not load that saved run.",
        variant: "destructive",
      });
    }
  };

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
      const response = await axios.post(`${API_BASE}/analyze`, data);
      setSummary(response.data.summary);
      setCompetitors(response.data.competitors);
      setFeatures(response.data.features);
      setPricing(response.data.pricing);
      setCharts(response.data.summary?.charts || {});
      setHasResults(true);
      setProgress(100);
      if (response.data?.persisted && response.data?.runId) {
        setSavedRunSelection(response.data.runId);
        void refreshSavedRuns({ silent: true });
      }
      toast({
        title: "Analysis Complete",
        description: response.data?.persisted
          ? "Report ready and saved to your history."
          : "Your competitive intelligence report is ready!",
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
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <History className="w-5 h-5" />
                Saved analyses
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center">
              {savedRuns.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No saved runs yet. Run an analysis to store it in Supabase (set{" "}
                  <code className="text-xs bg-muted px-1 rounded">SUPABASE_URL</code> and{" "}
                  <code className="text-xs bg-muted px-1 rounded">SUPABASE_SERVICE_ROLE_KEY</code>{" "}
                  for the API).
                </p>
              ) : (
                <Select
                  value={savedRunSelection}
                  onValueChange={(id) => {
                    setSavedRunSelection(id);
                    void loadSavedRun(id);
                  }}
                >
                  <SelectTrigger className="w-full sm:max-w-md">
                    <SelectValue placeholder="Load a previous run from Supabase…" />
                  </SelectTrigger>
                  <SelectContent>
                    {savedRuns.map((run) => (
                      <SelectItem key={run.id} value={run.id}>
                        {(run.company_name || "Untitled") +
                          " · " +
                          new Date(run.created_at).toLocaleString()}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Button type="button" variant="outline" onClick={() => void refreshSavedRuns()}>
                Refresh list
              </Button>
            </CardContent>
          </Card>

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

              <ChartDisplay charts={charts} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};