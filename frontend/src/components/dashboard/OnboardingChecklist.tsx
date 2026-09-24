import React from 'react';
import { Link } from 'react-router-dom';
import { 
  CheckCircle2, 
  Circle, 
  ArrowRight, 
  Building2, 
  Database, 
  Sparkles, 
  FileText 
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface OnboardingChecklistProps {
  hasDataset: boolean;
}

export const OnboardingChecklist: React.FC<OnboardingChecklistProps> = ({ hasDataset }) => {
  const { currentCompany } = useAuth();

  const steps = [
    {
      id: 1,
      title: 'Configure Organization Profile',
      description: 'Define your operating industry domain, country, and primary business objective.',
      completed: !!currentCompany?.name,
      link: '/onboarding',
      buttonText: 'Update Profile',
      icon: Building2,
    },
    {
      id: 2,
      title: 'Connect Database or Upload Data',
      description: 'Connect PostgreSQL, MySQL, REST APIs, Google Sheets, or upload your first CSV/XLSX file.',
      completed: hasDataset,
      link: '/connect-data',
      buttonText: 'Connect Data Source',
      icon: Database,
    },
    {
      id: 3,
      title: 'Inspect Business Performance & P&L',
      description: 'Examine revenue trends, margin dynamics, product performance, and anomaly detection.',
      completed: hasDataset,
      link: '/overview',
      buttonText: 'View Dashboard',
      icon: Sparkles,
    },
    {
      id: 4,
      title: 'Generate Boardroom Executive Report',
      description: 'Export an evidence-based 8-page business report in PDF or editable DOCX format.',
      completed: false,
      link: '/reports',
      buttonText: 'Generate Report',
      icon: FileText,
    },
  ];

  return (
    <div className="p-6 rounded-xl bg-card border border-border shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md bg-secondary border border-border text-muted-foreground text-xs font-medium mb-2">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span>Workspace Setup Guide</span>
          </div>
          <h2 className="text-xl font-bold text-foreground tracking-tight sm:text-2xl">
            Welcome to {currentCompany?.name || 'DataScope'}
          </h2>
          <p className="text-muted-foreground text-xs sm:text-sm mt-0.5">
            Follow these essential steps to activate full decision intelligence and automated reporting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/connect-data"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold shadow-xs transition-colors"
          >
            <Database className="w-3.5 h-3.5" />
            Connect Data Source
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <div
              key={step.id}
              className={`p-4 rounded-lg border flex flex-col justify-between transition-colors ${
                step.completed
                  ? 'bg-card border-border text-foreground'
                  : 'bg-card/40 border-border/80 text-muted-foreground hover:border-border'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
                    step.completed ? 'bg-secondary text-foreground' : 'bg-muted text-muted-foreground'
                  }`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  {step.completed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                  ) : (
                    <Circle className="w-4 h-4 text-muted-foreground/60" />
                  )}
                </div>

                <h3 className="text-sm font-semibold text-foreground mb-1">{step.title}</h3>
                <p className="text-muted-foreground text-xs leading-relaxed mb-4">{step.description}</p>
              </div>

              <Link
                to={step.link}
                className={`inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  step.completed
                    ? 'bg-secondary hover:bg-secondary/80 text-secondary-foreground border border-border'
                    : 'bg-primary hover:bg-primary/90 text-primary-foreground'
                }`}
              >
                {step.buttonText} <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default OnboardingChecklist;
