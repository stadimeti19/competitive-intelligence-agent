import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, BarChart3, PieChart, TrendingUp, Grid3X3 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ChartDisplayProps {
  charts: {
    revenue?: string;
    market_share?: string;
    pricing_models?: string;
    feature_matrix?: string;
  };
}

const chartConfigs = [
  {
    key: "revenue",
    title: "Revenue Comparison",
    description: "Revenue comparison across competitors",
    icon: TrendingUp,
    color: "text-blue-600"
  },
  {
    key: "market_share",
    title: "Market Share Distribution",
    description: "Market share breakdown by competitor",
    icon: PieChart,
    color: "text-green-600"
  },
  {
    key: "pricing_models",
    title: "Pricing Model Distribution",
    description: "Distribution of pricing models used",
    icon: BarChart3,
    color: "text-purple-600"
  },
  {
    key: "feature_matrix",
    title: "Feature Matrix",
    description: "Feature availability across competitors",
    icon: Grid3X3,
    color: "text-orange-600"
  }
];

export const ChartDisplay = ({ charts }: ChartDisplayProps) => {
  const [chartImages, setChartImages] = useState<Record<string, string>>({});
  const [loadingCharts, setLoadingCharts] = useState<Record<string, boolean>>({});
  const [errorCharts, setErrorCharts] = useState<Record<string, boolean>>({});
  const { toast } = useToast();
  
    const fetchChart = async (chartType: string) => {
    if (!charts[chartType as keyof typeof charts]) return;
    
    setLoadingCharts(prev => ({ ...prev, [chartType]: true }));
    setErrorCharts(prev => ({ ...prev, [chartType]: false }));
    
    try {
      const response = await fetch(`http://localhost:8000/charts/${chartType}`);
      if (!response.ok) {
        throw new Error(`Failed to load ${chartType} chart`);
      }
      
      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      setChartImages(prev => ({ ...prev, [chartType]: imageUrl }));
    } catch (error) {
      console.error(`Error loading ${chartType} chart:`, error);
      setErrorCharts(prev => ({ ...prev, [chartType]: true }));
      toast({
        title: "Chart Load Error",
        description: `Failed to load ${chartType} chart. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setLoadingCharts(prev => ({ ...prev, [chartType]: false }));
    }
  };

  useEffect(() => {
    // Fetch all available charts
    Object.keys(charts).forEach(chartType => {
      if (charts[chartType as keyof typeof charts]) {
        fetchChart(chartType);
      }
    });

    // Cleanup function to revoke object URLs
    return () => {
      Object.values(chartImages).forEach(url => {
        URL.revokeObjectURL(url);
      });
    };
  }, [charts]);

  const availableCharts = chartConfigs.filter(config => 
    charts[config.key as keyof typeof charts]
  );

  if (availableCharts.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Data Visualizations
          </h3>
          <p className="text-muted-foreground mb-6">
            No charts available. Charts will appear here after analysis.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Data Visualizations
        </h3>
        <p className="text-muted-foreground mb-6">
          Interactive charts and visualizations from your competitive analysis
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {availableCharts.map((config) => {
          const chartType = config.key;
          const isLoading = loadingCharts[chartType];
          const hasError = errorCharts[chartType];
          const imageUrl = chartImages[chartType];
          const IconComponent = config.icon;

          return (
            <Card key={chartType} className="overflow-hidden">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <IconComponent className={`w-5 h-5 ${config.color}`} />
                  {config.title}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {config.description}
                </p>
              </CardHeader>
              <CardContent>
                {isLoading && (
                  <div className="flex items-center justify-center h-64">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-6 h-6 animate-spin" />
                      <span>Loading chart...</span>
                    </div>
                  </div>
                )}

                {hasError && (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-center">
                      <p className="text-muted-foreground mb-2">
                        Failed to load chart
                      </p>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => fetchChart(chartType)}
                      >
                        Retry
                      </Button>
                    </div>
                  </div>
                )}

                {!isLoading && !hasError && imageUrl && (
                  <div className="space-y-3">
                    <img
                      src={imageUrl}
                      alt={config.title}
                      className="w-full h-auto rounded-lg border"
                      style={{ maxHeight: '400px', objectFit: 'contain' }}
                    />
                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>Generated from competitive analysis data</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const link = document.createElement('a');
                          link.href = imageUrl;
                          link.download = `${chartType}_chart.png`;
                          link.click();
                        }}
                      >
                        Download
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}; 