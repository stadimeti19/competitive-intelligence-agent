import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Radar } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

interface ScoreComponent {
  component_id: string;
  raw: number;
  normalized: number;
  weight: number;
  contribution: number;
}

interface RadarCompanyRow {
  rank: number;
  profile: {
    name: string;
    domain?: string | null;
    description?: string | null;
    industry_tags?: string[];
  };
  score_breakdown: {
    total: number;
    thesis_fit: string;
    components: ScoreComponent[];
  };
}

interface RadarResponse {
  runId: string | null;
  persisted: boolean;
  thesis: Record<string, unknown>;
  scoringConfig: Record<string, unknown>;
  labelLegend: Record<string, string>;
  companies: RadarCompanyRow[];
}

function parseKeywords(raw: string): string[] {
  return raw
    .split(/[,;\n]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export const RadarPage = () => {
  const [statement, setStatement] = useState("");
  const [mustInclude, setMustInclude] = useState("");
  const [mustExclude, setMustExclude] = useState("");
  const [maxCompanies, setMaxCompanies] = useState("12");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RadarResponse | null>(null);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statement.trim()) {
      toast({ title: "Thesis required", variant: "destructive" });
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const payload = {
        statement: statement.trim(),
        must_include_keywords: parseKeywords(mustInclude),
        must_exclude_keywords: parseKeywords(mustExclude),
        max_companies: Math.min(50, Math.max(1, parseInt(maxCompanies, 10) || 12)),
      };
      const res = await axios.post<RadarResponse>(`${API_BASE}/radar/analyze`, payload);
      setResult(res.data);
      toast({
        title: "Radar run complete",
        description: res.data.persisted
          ? "Results saved to Supabase."
          : "Results ready (configure Supabase to persist).",
      });
    } catch (err: unknown) {
      const detail = axios.isAxiosError(err)
        ? (err.response?.data as { detail?: string })?.detail || err.message
        : "Request failed";
      toast({ title: "Radar failed", description: String(detail), variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
              <Radar className="w-8 h-8" />
              Thesis radar
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              Ranked companies vs your thesis (CompanyEnrich + news signals). Scores are deterministic.
            </p>
          </div>
          <Button variant="outline" asChild>
            <Link to="/">Back to CI dashboard</Link>
          </Button>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Thesis</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="statement">Statement</Label>
                <Textarea
                  id="statement"
                  placeholder='e.g. "AI devtools for compliance teams"'
                  value={statement}
                  onChange={(e) => setStatement(e.target.value)}
                  rows={4}
                  required
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="inc">Must-include keywords (comma-separated)</Label>
                  <Input
                    id="inc"
                    value={mustInclude}
                    onChange={(e) => setMustInclude(e.target.value)}
                    placeholder="compliance, developer"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exc">Must-exclude keywords (comma-separated)</Label>
                  <Input
                    id="exc"
                    value={mustExclude}
                    onChange={(e) => setMustExclude(e.target.value)}
                    placeholder="crypto, gambling"
                  />
                </div>
              </div>
              <div className="space-y-2 max-w-xs">
                <Label htmlFor="max">Max companies</Label>
                <Input
                  id="max"
                  type="number"
                  min={1}
                  max={50}
                  value={maxCompanies}
                  onChange={(e) => setMaxCompanies(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Run radar
              </Button>
            </form>
          </CardContent>
        </Card>

        {result && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How labels work</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground space-y-1">
                {Object.entries(result.labelLegend).map(([k, v]) => (
                  <p key={k}>
                    <Badge variant="secondary" className="mr-2">
                      {k}
                    </Badge>
                    {v}
                  </p>
                ))}
              </CardContent>
            </Card>

            <h2 className="text-xl font-semibold">Ranked companies</h2>
            <Accordion type="single" collapsible className="w-full border rounded-md">
              {result.companies.map((row) => (
                <AccordionItem key={row.rank} value={`${row.rank}`}>
                  <AccordionTrigger className="px-4 hover:no-underline">
                    <div className="flex flex-wrap items-center gap-3 text-left">
                      <span className="font-mono text-muted-foreground">#{row.rank}</span>
                      <span className="font-medium">{row.profile.name}</span>
                      {row.profile.domain && (
                        <span className="text-sm text-muted-foreground">{row.profile.domain}</span>
                      )}
                      <Badge>{row.score_breakdown.thesis_fit}</Badge>
                      <span className="text-sm tabular-nums">
                        score {(row.score_breakdown.total * 100).toFixed(1)}%
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="px-4 pb-4">
                    {row.profile.description && (
                      <p className="text-sm text-muted-foreground mb-3">{row.profile.description}</p>
                    )}
                    {row.profile.industry_tags && row.profile.industry_tags.length > 0 && (
                      <p className="text-xs mb-3">
                        <span className="text-muted-foreground">Tags: </span>
                        {row.profile.industry_tags.join(", ")}
                      </p>
                    )}
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Component</TableHead>
                          <TableHead className="text-right">Weight</TableHead>
                          <TableHead className="text-right">Normalized</TableHead>
                          <TableHead className="text-right">Contribution</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {row.score_breakdown.components.map((c) => (
                          <TableRow key={c.component_id}>
                            <TableCell className="font-mono text-xs">{c.component_id}</TableCell>
                            <TableCell className="text-right tabular-nums">
                              {(c.weight * 100).toFixed(0)}%
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              {c.normalized.toFixed(3)}
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              {c.contribution.toFixed(4)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        )}
      </div>
    </div>
  );
};
