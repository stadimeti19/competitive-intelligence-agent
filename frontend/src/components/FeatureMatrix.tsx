import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, Minus, X } from "lucide-react";

interface FeatureData {
  name: string;
  features: string;
}

interface CompetitorDetail {
  name: string;
  pricing_model?: string;
  key_features?: string;
  market_position?: string;
  target_audience?: string;
  pricing_tiers?: string;
}

interface FeatureMatrixProps {
  competitors: string[];
  features: FeatureData[];
  competitorDetails?: CompetitorDetail[];
}

type FeatureStatus = "available" | "unavailable" | "unknown";

interface FeatureDefinition {
  label: string;
  terms: string[];
}

const featureDefinitions: FeatureDefinition[] = [
  { label: "AI / Machine Learning", terms: ["ai", "artificial intelligence", "machine learning", "ml", "predictive", "generative ai", "ai agents"] },
  { label: "Automation", terms: ["automation", "automated", "workflow automation", "business process automation", "automated workflows"] },
  { label: "Analytics / Reporting", terms: ["analytics", "reporting", "dashboard", "insights", "business intelligence", "performance reporting"] },
  { label: "Mobile App", terms: ["mobile app", "ios app", "android app", "mobile platform", "mobile access"] },
  { label: "Online Dashboard / Portal", terms: ["web dashboard", "online dashboard", "online portal", "client portal", "web platform", "self-service portal"] },
  { label: "API / Integrations", terms: ["api", "developer api", "integration", "integrations", "connectors", "third-party connectors", "webhooks"] },
  { label: "Security", terms: ["security", "encryption", "sso", "single sign-on", "mfa", "multi-factor authentication", "2fa", "access control"] },
  { label: "Compliance / Risk", terms: ["compliance", "risk management", "regulatory", "audit", "governance", "supervision"] },
  { label: "Admin Controls", terms: ["admin controls", "administration", "permissions", "roles", "user management", "policy management"] },
  { label: "Collaboration", terms: ["collaboration", "team collaboration", "shared workspace", "comments", "mentions"] },
  { label: "Communication / Messaging", terms: ["messaging", "chat", "team communication", "instant messaging", "video conferencing", "calling", "meetings"] },
  { label: "Document / File Sharing", terms: ["file sharing", "document sharing", "docs", "knowledge base", "content management"] },
  { label: "Task / Project Management", terms: ["task management", "project management", "kanban", "to-do", "work management", "deadline", "roadmap"] },
  { label: "Workflow Management", terms: ["workflow", "workflow management", "process management", "approval workflow", "business process"] },
  { label: "Customer Support", terms: ["customer support", "support ticket", "help desk", "live chat", "service desk", "customer service"] },
  { label: "CRM / Sales", terms: ["crm", "sales pipeline", "lead management", "sales automation", "contact management"] },
  { label: "Marketing", terms: ["marketing automation", "campaign", "email marketing", "ads", "seo", "content marketing"] },
  { label: "E-commerce", terms: ["e-commerce", "ecommerce", "online store", "checkout", "cart", "marketplace"] },
  { label: "Payments", terms: ["payment processing", "online payments", "instant payments", "settlement", "billing", "invoicing"] },
  { label: "Subscription / Billing", terms: ["subscription", "recurring billing", "billing", "pricing tiers", "usage-based pricing"] },
  { label: "Inventory / Operations", terms: ["inventory", "stock auditing", "supply chain", "operations", "asset management", "field service"] },
  { label: "HR / People", terms: ["hr", "human resources", "employee", "payroll", "recruiting", "onboarding", "workforce"] },
  { label: "Education / Learning", terms: ["education", "learning management", "lms", "courses", "training", "students"] },
  { label: "Healthcare", terms: ["healthcare", "clinical", "patient", "ehr", "emr", "medical", "care management"] },
  { label: "Developer Tools", terms: ["developer tools", "devtools", "sdk", "cli", "code", "deployment", "developer platform"] },
  { label: "Data Platform", terms: ["data platform", "data warehouse", "data lake", "etl", "data pipeline", "database"] },
  { label: "Cloud / Infrastructure", terms: ["cloud", "infrastructure", "hosting", "kubernetes", "serverless", "devops"] },
  { label: "Open Source / Self Hosted", terms: ["open-source", "open source", "self-hosted", "self hosted", "on-premise", "on premise"] },
  { label: "Enterprise Features", terms: ["enterprise", "enterprise-grade", "scalable", "governance", "sla", "dedicated support"] },
  { label: "Investment Management", terms: ["investment management", "asset management", "managed portfolio", "portfolio management"] },
  { label: "Brokerage / Trading", terms: ["brokerage", "stock trading", "trading platform", "trade stocks", "securities trading", "self-directed investing"] },
  { label: "Retirement Planning", terms: ["retirement", "401k", "401 k", "ira", "pension", "retirement account"] },
  { label: "Wealth Advisory", terms: ["wealth management", "financial advisor", "financial advisory", "advisory services", "advisor network"] },
  { label: "Mutual Funds", terms: ["mutual fund", "mutual funds", "fund family"] },
  { label: "ETFs", terms: ["etf", "exchange traded fund", "exchange-traded fund"] },
  { label: "Research & Market Data", terms: ["research", "market data", "analyst research", "investment research", "screeners"] },
  { label: "Financial Planning Tools", terms: ["financial planning", "planning tools", "goal planning", "retirement calculator", "portfolio analysis"] },
  { label: "Mobile App", terms: ["mobile app", "ios app", "android app", "mobile investing", "mobile banking"] },
  { label: "Online Dashboard / Portal", terms: ["web dashboard", "online dashboard", "online portal", "client portal", "web platform", "online account"] },
  { label: "Tax Planning", terms: ["tax planning", "tax optimization", "tax-loss harvesting", "tax loss harvesting"] },
  { label: "Cash Management", terms: ["cash management", "sweep account", "money market", "banking services"] },
  { label: "Banking", terms: ["banking", "bank account", "checking account", "savings account"] },
  { label: "Credit Cards", terms: ["credit card", "credit cards"] },
  { label: "Fraud Protection", terms: ["fraud protection", "fraud detection", "fraud monitoring", "account protection"] },
  { label: "Cryptocurrency", terms: ["cryptocurrency", "crypto", "digital assets", "bitcoin"] },
];

const genericFeatureWords = new Set([
  "features",
  "platform",
  "solution",
  "services",
  "products",
  "capabilities",
  "support",
  "including",
  "include",
  "offers",
  "provides",
  "strong",
  "broad",
  "advanced",
  "enterprise",
]);

function normalize(value: string): string {
  return value
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function includesTerm(text: string, term: string): boolean {
  return text.includes(normalize(term));
}

function hasNegativeEvidence(text: string, feature: FeatureDefinition): boolean {
  return feature.terms.some((term) => {
    const t = normalize(term);
    return (
      text.includes(`no ${t}`) ||
      text.includes(`without ${t}`) ||
      text.includes(`does not offer ${t}`) ||
      text.includes(`not offer ${t}`) ||
      text.includes(`${t} not available`) ||
      text.includes(`${t} unavailable`)
    );
  });
}

function getCompanyText(
  competitorName: string,
  features: FeatureData[],
  competitorDetails?: CompetitorDetail[],
): string {
  const featureText = features.find((f) => f.name === competitorName)?.features ?? "";
  const details = competitorDetails?.find((c) => c.name === competitorName);
  return normalize(
    [
      featureText,
      details?.key_features,
      details?.market_position,
      details?.target_audience,
      details?.pricing_model,
      details?.pricing_tiers,
    ]
      .filter(Boolean)
      .join(" "),
  );
}

function toTitleCase(value: string): string {
  return value.replace(/\b\w/g, (char) => char.toUpperCase());
}

function buildDynamicFeatureDefinitions(
  features: FeatureData[],
  competitorDetails?: CompetitorDetail[],
): FeatureDefinition[] {
  const chunks = [...features.map((f) => f.features), ...(competitorDetails ?? []).map((c) => c.key_features ?? "")]
    .join("; ")
    .split(/[.;:|()\n]+|,\s+| plus | and /i)
    .map((chunk) => normalize(chunk))
    .filter(Boolean);

  const counts = new Map<string, number>();
  chunks.forEach((chunk) => {
    const words = chunk.split(" ").filter((word) => !genericFeatureWords.has(word));
    if (words.length < 2 || words.length > 5) return;
    const phrase = words.join(" ");
    if (phrase.length < 8 || phrase.length > 60) return;
    counts.set(phrase, (counts.get(phrase) ?? 0) + 1);
  });

  const existingTerms = new Set(featureDefinitions.flatMap((feature) => feature.terms.map(normalize)));
  return [...counts.entries()]
    .filter(([phrase, count]) => count >= 2 && !existingTerms.has(phrase))
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 10)
    .map(([phrase]) => ({ label: toTitleCase(phrase), terms: [phrase] }));
}

function getFeatureStatus(
  competitorName: string,
  feature: FeatureDefinition,
  features: FeatureData[],
  competitorDetails?: CompetitorDetail[],
): FeatureStatus {
  const text = getCompanyText(competitorName, features, competitorDetails);
  if (!text || text === "n a" || text.includes("information not available")) {
    return "unknown";
  }
  if (feature.terms.some((term) => includesTerm(text, term))) {
    return "available";
  }
  if (hasNegativeEvidence(text, feature)) {
    return "unavailable";
  }
  return "unknown";
}

function getFeatureIcon(status: FeatureStatus) {
  if (status === "available") return <Check className="w-4 h-4 text-success" aria-label="Available" />;
  if (status === "unavailable") return <X className="w-4 h-4 text-destructive" aria-label="Unavailable" />;
  return <Minus className="w-4 h-4 text-muted-foreground" aria-label="Not found in sources" />;
}

export const FeatureMatrix = ({ competitors, features, competitorDetails }: FeatureMatrixProps) => {
  const allFeatureDefinitions = [
    ...featureDefinitions,
    ...buildDynamicFeatureDefinitions(features, competitorDetails),
  ];
  const visibleFeatures = allFeatureDefinitions.filter((feature) =>
    competitors.some(
      (competitor) =>
        getFeatureStatus(competitor, feature, features, competitorDetails) !== "unknown",
    ),
  );

  if (visibleFeatures.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Feature Comparison Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No source-backed feature signals were found for comparison.
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
                <TableHead className="min-w-[220px]">Feature</TableHead>
                {competitors.map((competitor) => (
                  <TableHead key={competitor} className="text-center min-w-[120px]">
                    {competitor}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleFeatures.map((feature) => (
                <TableRow key={feature.label}>
                  <TableCell className="font-medium">{feature.label}</TableCell>
                  {competitors.map((competitor) => (
                    <TableCell key={competitor} className="text-center">
                      {getFeatureIcon(
                        getFeatureStatus(competitor, feature, features, competitorDetails),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-6 mt-4 pt-4 border-t text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Check className="w-4 h-4 text-success" />
            <span>Available in source text</span>
          </div>
          <div className="flex items-center gap-2">
            <Minus className="w-4 h-4 text-muted-foreground" />
            <span>Not found in sources</span>
          </div>
          <div className="flex items-center gap-2">
            <X className="w-4 h-4 text-destructive" />
            <span>Explicitly unavailable</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
